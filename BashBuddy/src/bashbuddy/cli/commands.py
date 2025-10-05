"""CLI command handlers."""

import click
from bashbuddy.utils import send_command, ensure_daemon_running
from bashbuddy.cli.display import (
    display_function_calls,
    display_command_and_explanation,
    display_text_response,
    prompt_user_action,
    execute_command,
    copy_to_clipboard
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

            # Prompt user for next action
            action, followup = prompt_user_action(response["command"])

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
