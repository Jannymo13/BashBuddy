import click
import questionary
from bashbuddy.cli.commands import ask, process_ask_request
from bashbuddy.cli.display import execute_command, copy_to_clipboard
from bashbuddy.utils import (
    start_daemon,
    stop_daemon,
    get_daemon_status,
    send_command,
    is_daemon_running,
    ensure_daemon_running
)


def handle_command_action(command: str, explanation: str, user_request: str = ""):
    """
    Handle user action for a command (run/copy/quit).
    This consolidates the duplicate prompt logic.
    """
    action = questionary.select(
        "What would you like to do?",
        choices=[
            "[R] Run the command",
            "[C] Copy to clipboard",
            "[Q] Cancel"
        ],
        style=questionary.Style([
            ('selected', 'fg:green bold'),
            ('pointer', 'fg:yellow bold'),
            ('question', 'fg:white bold')
        ])
    ).ask()
    
    if action == "[R] Run the command":
        click.echo()
        execute_command(command, explanation, user_request)
    elif action == "[C] Copy to clipboard":
        click.echo()
        copy_to_clipboard(command, explanation, user_request)


def interactive_mode():
    """Interactive mode - ask for input once, then process like 'ask' command."""
    # Ensure daemon is running
    if not ensure_daemon_running():
        click.echo("Error: Failed to start BashBuddy daemon.", err=True)
        click.echo("Please check that GEMINI_API_KEY is set.", err=True)
        return
    
    click.echo(click.style("What do you need help with? (Ctrl+C to exit)\n", fg="cyan", dim=True))
    try:
        # Get user input once
        question = click.prompt(click.style("❯", fg="yellow", bold=True), prompt_suffix=" ")
        
        if question.strip():
            # Process the request exactly like 'ask' command
            process_ask_request(question)
    
    except (click.Abort, KeyboardInterrupt):
        click.echo("\n")
        return


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """BashBuddy - Your intelligent terminal command assistant."""
    # If no subcommand was given, enter interactive mode
    if ctx.invoked_subcommand is None:
        interactive_mode()


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



# def status():
#     """Check the status of the BashBuddy."""
#     result = get_daemon_status()
#
#     if result["status"] == "running":
#         click.echo(f"✓ {result['message']}")
#         click.echo(f"  PID: {result.get('pid')}")
#     elif result["status"] == "stopped":
#         click.echo(f"○ {result['message']}")
#     else:
#         click.echo(f"⚠ {result['message']}", err=True)
# cli.add_command(status)

@click.command()
def reset():
    """Clear the conversation history."""
    if not ensure_daemon_running():
        click.echo("Error: Failed to start daemon", err=True)
        raise click.Abort()
        
    result = send_command("reset")
    
    if result["status"] == "ok":
        click.echo(f"✓ {result['message']}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
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
        except KeyboardInterrupt:
            click.echo("\n")
            return
            
    else:
        click.echo(f"✗ {result['message']}", err=True)
        raise click.Abort()


# Register commands
cli.add_command(start)
cli.add_command(stop)
cli.add_command(reset)
cli.add_command(history)
cli.add_command(ask)
