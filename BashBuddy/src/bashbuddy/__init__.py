import click
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
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
    
    # Get history to use for autocomplete
    history_response = send_command("history")
    suggestions = []
    
    if history_response.get("status") == "ok":
        history_items = history_response.get("history", [])
        # Extract unique user queries from history
        seen = set()
        for item in history_items:
            if item["role"] == "user":
                query = item["content"].strip()
                if query and query.lower() not in seen:
                    suggestions.append(query)
                    seen.add(query.lower())
    
    # Create completer with history suggestions
    completer = WordCompleter(suggestions, ignore_case=True, match_middle=True)
    
    # Custom style with better colors
    style = Style.from_dict({
        'completion-menu.completion': 'bg:#008888 #ffffff',  # Cyan background, white text
        'completion-menu.completion.current': 'bg:#00aaaa #000000',  # Lighter cyan for selected, black text
        'scrollbar.background': 'bg:#88aaaa',
        'scrollbar.button': 'bg:#222222',
    })
    
    click.echo(click.style("What do you need help with? (Tab for suggestions, Ctrl+C to exit)\n", fg="cyan", dim=True))
    try:
        # Get user input with autocomplete
        question = prompt(
            "❯ ",
            completer=completer,
            complete_while_typing=True,
            style=style
        )
        
        if question.strip():
            # Process the request exactly like 'ask' command
            process_ask_request(question)
    
    except (KeyboardInterrupt, EOFError):
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

