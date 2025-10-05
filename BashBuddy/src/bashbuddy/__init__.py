import click
from bashbuddy.cli.commands import ask
from bashbuddy.utils import (
    start_daemon,
    stop_daemon,
    get_daemon_status,
    send_command,
    is_daemon_running,
    ensure_daemon_running
)


@click.group()
def cli():
    """BashBuddy - Your intelligent bash command assistant."""
    pass


@click.command()
def start():
    """Start the BashBuddy daemon."""
    click.echo("Starting BashBuddy daemon...")
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
    """Stop the BashBuddy daemon."""
    click.echo("Stopping BashBuddy daemon...")
    result = stop_daemon()
    
    if result["status"] == "ok":
        click.echo(f"  {result['message']}")
    else:
        click.echo(f"  {result['message']}", err=True)
        raise click.Abort()


@click.command()
def status():
    """Check the status of the BashBuddy daemon."""
    result = get_daemon_status()
    
    if result["status"] == "running":
        click.echo(f"✓ {result['message']}")
        click.echo(f"  PID: {result.get('pid')}")
    elif result["status"] == "stopped":
        click.echo(f"○ {result['message']}")
    else:
        click.echo(f"⚠ {result['message']}", err=True)


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
    """Show the conversation history."""
    if not ensure_daemon_running():
        click.echo("Error: Failed to start daemon", err=True)
        raise click.Abort()
        
    result = send_command("history")
    
    if result["status"] == "ok":
        history_items = result.get("history", [])
        
        if not history_items:
            click.echo("No conversation history yet.")
            return
            
        click.echo(f"Conversation history ({result['length']} messages):\n")
        
        for i, item in enumerate(history_items, 1):
            role = item["role"].capitalize()
            content = item["content"]
            
            # Truncate long messages
            if len(content) > 100:
                content = content[:97] + "..."
                
            click.echo(f"{i}. {role}: {content}")
    else:
        click.echo(f"✗ {result['message']}", err=True)
        raise click.Abort()


# Register commands
cli.add_command(start)
cli.add_command(stop)
cli.add_command(status)
cli.add_command(reset)
cli.add_command(history)
cli.add_command(ask)
