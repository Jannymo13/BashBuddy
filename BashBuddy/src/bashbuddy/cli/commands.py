"""CLI command handlers."""

import click
from bashbuddy.utils import send_command, ensure_daemon_running
from bashbuddy.cli.display import (
    display_function_calls,
    display_command_and_explanation,
    display_text_response,
    prompt_user_action
)


@click.command()
@click.argument("request")
@click.option("--cmd", "-c", help="Command to get help for", required=False)
def ask(request: str, cmd: str | None):
    """Ask BashBuddy a question about bash commands."""
    
    # Automatically ensure daemon is running (starts it if needed)
    if not ensure_daemon_running():
        click.echo("Error: Failed to start BashBuddy daemon.", err=True)
        raise click.Abort()
    
    # Prepare the message
    if cmd:
        message = f"Help for command '{cmd}': {request}"
    else:
        message = request
    
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
                click.echo(click.style("\nRunning command...\n", fg="green", bold=True))
                # TODO: Implement execute_command(response["command"])
                click.echo(click.style("Command execution not yet implemented!", fg="yellow"))
            elif action == 'copy':
                click.echo(click.style("\nCopying to clipboard...\n", fg="green", bold=True))
                # TODO: Implement copy_to_clipboard(response["command"])
                click.echo(click.style("Clipboard support not yet implemented!", fg="yellow"))
            elif action == 'followup':
                click.echo(click.style(f"\nFollow-up question: {followup}\n", fg="cyan"))
                # TODO: handle follow-up question
                click.echo(click.style("Follow-up questions not yet implemented!", fg="yellow"))
        else:
            # Regular text response - still show function calls if any
            display_function_calls(response.get("function_calls"))
            
            # Display the text response
            display_text_response(response["message"])
    else:
        click.echo(f"Error: {response.get('message', 'Unknown error')}", err=True)
        raise click.Abort()
