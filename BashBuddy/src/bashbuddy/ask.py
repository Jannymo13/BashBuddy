import click
from bashbuddy.utils import send_command, ensure_daemon_running


@click.command()
@click.argument("request")
@click.option("--cmd", "-c", help="Command to get help for", required=False)
def ask(request: str, cmd: str | None):
    """Ask BashBuddy a question about bash commands."""
    
    # Automatically ensure daemon is running (starts it if needed)
    if not ensure_daemon_running():
        click.echo("Error: Failed to start BashBuddy daemon.", err=True)
        click.echo("Please check that GEMINI_API_KEY is set.", err=True)
        raise click.Abort()
    
    # Prepare the message
    if cmd:
        message = f"Help for command '{cmd}': {request}"
    else:
        message = request
    
    # Send request to daemon
    response = send_command("ask", message=message)
    
    if response.get("status") == "ok":
        click.echo(response["message"])
    else:
        click.echo(f"Error: {response.get('message', 'Unknown error')}", err=True)
        raise click.Abort()
