"""CLI command handlers."""

import click
import questionary
from bashbuddy.daemon.client import send_command
from bashbuddy.daemon.manager import ensure_daemon_running, start_daemon, stop_daemon
from bashbuddy.cli.formatting import (
    display_function_calls,
    display_command_and_explanation,
    display_text_response
)
from bashbuddy.cli.actions import (
    prompt_user_action,
    execute_command,
    copy_to_clipboard,
    handle_command_action
)


def process_ask_request(message: str):
    """Process an ask request and handle user interactions."""
    # Automatically ensure daemon is running (starts it if needed)
    if not ensure_daemon_running():
        click.echo("Error: Failed to start BashBuddy daemon.", err=True)
        raise click.Abort()
    
    # Send request to daemon
    response = send_command("ask", message=message)
    
    if response.get("status") == "ok":
        # Check if we got a structured command response
        if "command" in response and "explanation" in response:
            # Show function calls if any were made
            display_function_calls(response.get("function_calls"))
            
            # Display command and explanation side by side
            display_command_and_explanation(response)
            
            # Show if this is a cached result (AFTER displaying command)
            if response.get("cached"):
                click.echo()
                click.echo(click.style("Retrieved result from history (exact match)", fg="cyan", dim=True))
                click.echo(click.style("  Press [F] to force a fresh query", fg="cyan", dim=True))

            # Prompt user for next action
            action, followup = prompt_user_action(response["command"], is_cached=response.get("cached", False))

            # Handle force refresh
            if action == 'refresh':
                click.echo(click.style("\nFetching fresh result...\n", fg="yellow"))
                # Send request with force flag to bypass cache
                response = send_command("ask", message=message, force_fresh=True)
                if response.get("status") == "ok" and "command" in response:
                    display_function_calls(response.get("function_calls"))
                    display_command_and_explanation(response)
                    action, followup = prompt_user_action(response["command"], is_cached=False)
                else:
                    click.echo("Error getting fresh result", err=True)
                    return

            if action == 'run':
                click.echo(click.style("\nRunning command...", fg="green", bold=True))
                click.echo(click.style("Command Output:", fg="white", bold=True))
                execute_command(
                    response["command"], 
                    response.get("explanation", ""),
                    message  # Pass the user's original request
                )
            elif action == 'copy':
                click.echo()
                copy_to_clipboard(
                    response["command"], 
                    response.get("explanation", ""),
                    message  # Pass the user's original request
                )
            elif action == 'followup':
                process_ask_request(followup)
            # elif action == 'quit': just exit naturally

        else:
            # Regular text response - still show function calls if any
            display_function_calls(response.get("function_calls"))
            
            # Display the text response
            display_text_response(response["message"])
    else:
        click.echo(f"Error: {response.get('message', 'Unknown error')}", err=True)
        raise click.Abort()


@click.command()
@click.argument("request")
@click.option("--cmd", "-c", help="Command to get help for", required=False)
def ask(request: str, cmd: str | None):
    """Ask BashBuddy a question about bash commands."""
    
    # Prepare the message
    if cmd:
        message = f"Help for command '{cmd}': {request}"
    else:
        message = request
    
    # Process the request
    process_ask_request(message)


@click.command()
def start():
    """Manually start a connection to BashBuddy servers."""
    click.echo("Starting BashBuddy connection...")
    result = start_daemon()
    
    if result["status"] == "ok":
        click.echo(f"  {result['message']}")
        click.echo(f"  PID: {result.get('pid')}")
        click.echo("\nYou can now use: bashbuddy ask \"your question\"")
    else:
        click.echo(f"  {result['message']}", err=True)
        raise click.Abort()


@click.command()
def stop():
    """Stop the connection to BashBuddy servers."""
    click.echo("Stopping BashBuddy daemon...")
    result = stop_daemon()
    
    if result["status"] == "ok":
        click.echo(f"  {result['message']}")
    else:
        click.echo(f"  {result['message']}", err=True)
        raise click.Abort()


@click.command()
def reset():
    """Clear the conversation history."""
    if not ensure_daemon_running():
        click.echo("Error: Failed to start daemon", err=True)
        raise click.Abort()
        
    result = send_command("reset")
    
    if result["status"] == "ok":
        click.echo(f"[OK] {result['message']}")
    else:
        click.echo(f"[ERROR] {result['message']}", err=True)
        raise click.Abort()


@click.command()
def history():
    """Show the conversation history and select commands to run/copy."""
    if not ensure_daemon_running():
        click.echo("Error: Failed to start daemon", err=True)
        raise click.Abort()
        
    result = send_command("history")
    
    if result["status"] == "ok":
        history_items = result.get("history", [])
        
        if not history_items:
            click.echo("No conversation history yet.")
            return
        
        # Extract only assistant responses that contain commands
        commands = []
        for item in history_items:
            if item["role"] == "assistant":
                content = item["content"]
                # Check if it's a command response (contains "Command:")
                if "Command:" in content:
                    # Extract command from "Command: <cmd>\nExplanation: <exp>"
                    lines = content.split("\n")
                    if lines:
                        cmd_line = lines[0].replace("Command:", "").strip()
                        explanation = ""
                        if len(lines) > 1:
                            explanation = lines[1].replace("Explanation:", "").strip()
                        commands.append({"command": cmd_line, "explanation": explanation})
        
        if not commands:
            click.echo("No commands in history yet.")
            return
        
        # Create choices for questionary with command and description
        choices = []
        for cmd_data in commands:
            cmd = cmd_data["command"]
            exp = cmd_data["explanation"]
            # Truncate explanation if too long
            if len(exp) > 60:
                exp = exp[:57] + "..."
            # Format: command on first line, explanation indented below
            choice = f"{cmd}\n      {exp}"
            choices.append(choice)
        
        # Use questionary to select with arrow keys
        try:
            click.echo(click.style("\nCommand History\n", fg="cyan", bold=True))
            
            selected = questionary.select(
                "Select a command:",
                choices=choices,
                style=questionary.Style([
                    ('selected', 'fg:cyan bold'),
                    ('pointer', 'fg:yellow bold'),
                    ('highlighted', 'fg:cyan'),
                    ('question', 'fg:white bold')
                ])
            ).ask()
            
            if not selected:
                return
            
            # Find the selected command data
            selected_index = choices.index(selected)
            cmd_data = commands[selected_index]
            
            # Show selected command details
            click.echo()
            click.echo(click.style("═" * 80, fg="green"))
            click.echo(click.style(f"  Command", fg="green", bold=True))
            click.echo(click.style("─" * 80, fg="white", dim=True))
            click.echo(click.style(f"  {cmd_data['command']}", fg="cyan", bold=True))
            click.echo()
            click.echo(click.style(f"  Explanation", fg="green", bold=True))
            click.echo(click.style("─" * 80, fg="white", dim=True))
            click.echo(f"  {cmd_data['explanation']}")
            click.echo(click.style("═" * 80, fg="green"))
            click.echo()
            
            # Use shared function to handle action
            handle_command_action(cmd_data['command'], cmd_data['explanation'], "")
            
        except (KeyboardInterrupt, EOFError):
            click.echo("\n")
            return
            
    else:
        click.echo(f"[ERROR] {result['message']}", err=True)
        raise click.Abort()

