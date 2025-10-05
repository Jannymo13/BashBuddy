"""User interaction and command execution functions."""

import click
import questionary
import subprocess
from typing import Optional
from bashbuddy.core.config import load_environment
from bashbuddy.core.supabase_logger import get_supabase_logger

load_environment()

DANGEROUS_COMMANDS = ['rm', 'mv', 'dd', 'mkfs', 'shutdown', 'reboot', 'init', 'poweroff', 'halt', 'fdisk', 'parted', 'sudo']


def handle_command_action(command: str, explanation: str, user_request: str = "") -> None:
    """Handle user selection for command action (run/copy/quit)."""
    action = questionary.select(
        "What would you like to do?",
        choices=[
            "Run the command",
            "Copy to clipboard",
            "Cancel"
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


def prompt_user_action(command: str, is_cached: bool = False) -> tuple[str, Optional[str]]:
    """
    Prompt user for what to do with the command.
    Returns tuple of (action, followup_text).
    """
    click.echo()
    click.echo(click.style("What would you like to do with this command?", fg="yellow", bold=True))

    if any(command.strip().startswith(dc) for dc in DANGEROUS_COMMANDS):
        click.echo(click.style("  [R]un the command. WARNING: This command could be potentially harmful!", fg="red", bold=True))
        click.echo(click.style("  Read the command carefully and only run if you are sure!", fg="red"))
    else:
        click.echo(click.style("  [R]un the command", fg="white"))

    click.echo(click.style("  [C]opy to clipboard", fg="white"))
    
    if is_cached:
        click.echo(click.style("  [F]orce fresh query", fg="yellow"))
    
    click.echo(click.style("  [Q]uit", fg="white"))
    click.echo(click.style("  Or type a follow-up question", fg="cyan", dim=True))
    click.echo()
    
    choice = click.prompt(
        click.style("Your choice", fg="yellow"),
        default='q',
        show_default=False
    ).strip().lower()
    
    if choice in ['r', 'run']:
        return ('run', None)
    elif choice in ['c', 'copy']:
        return ('copy', None)
    elif choice in ['f', 'force', 'fresh']:
        return ('refresh', None)
    elif choice in ['q', 'quit', '']:
        return ('quit', None)
    else:
        return ('followup', choice)


def execute_command(command: str, explanation: str = "", user_request: str = "") -> bool:
    """Execute bash command in subprocess and display output."""
    try:
        if explanation:
            logger = get_supabase_logger()
            logger.log_command(command, explanation, user_request)
        
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            stdout=None,
            stderr=None
        )
        
        click.echo()
        if result.returncode == 0:
            click.echo(click.style("\n[OK] Command completed successfully", fg="green", bold=True))
        else:
            click.echo(click.style(f"[ERROR] Command exited with code {result.returncode}", fg="red", bold=True))
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        click.echo()
        click.echo(click.style("\n[!] Command interrupted by user", fg="yellow"))
        return False
    except Exception as e:
        click.echo()
        click.echo(click.style(f"[ERROR] Error running command: {str(e)}", fg="red", bold=True))
        return False


def copy_to_clipboard(command: str, explanation: str = "", user_request: str = "") -> bool:
    """Copy command to clipboard using available tools (wl-copy, xclip, xsel, pbcopy)."""
    if explanation:
        logger = get_supabase_logger()
        logger.log_command(command, explanation, user_request)
    
    clipboard_commands = [
        ['wl-copy'],
        ['xclip', '-selection', 'clipboard'],
        ['xsel', '--clipboard', '--input'],
        ['pbcopy'],
    ]
    
    for clipboard_cmd in clipboard_commands:
        try:
            if subprocess.run(['which', clipboard_cmd[0]], 
                            capture_output=True, 
                            text=True).returncode == 0:
                subprocess.run(
                    clipboard_cmd,
                    input=command,
                    text=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                click.echo(click.style(f"Command copied to clipboard!", fg="green", bold=True))
                click.echo(click.style(f"  {command}", fg="cyan"))
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    click.echo(click.style("[ERROR] No clipboard tool found!", fg="red", bold=True))
    click.echo(click.style("  Install one of: wl-copy, xclip, xsel", fg="yellow"))
    click.echo()
    click.echo(click.style("  Here's the command to copy manually:", fg="white", bold=True))
    click.echo(click.style(f"  {command}", fg="cyan", bold=True))
    return False
