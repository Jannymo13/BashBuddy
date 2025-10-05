import click
from bashbuddy.cli.commands import ask, process_ask_request, start, stop, reset, history
from bashbuddy.daemon.manager import (
    start_daemon,
    stop_daemon,
    get_daemon_status,
    ensure_daemon_running
)
from bashbuddy.daemon.client import (
    send_command,
    is_daemon_running
)


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


# Register commands
cli.add_command(start)
cli.add_command(stop)
cli.add_command(reset)
cli.add_command(history)
cli.add_command(ask)

