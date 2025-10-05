"""Display and formatting functions for CLI output."""

import click
import shutil
import subprocess
import sys
from bashbuddy.core.config import load_environment
from bashbuddy.core.supabase_logger import get_supabase_logger

# Load environment variables early
load_environment()

DANGEROUS_COMMANDS = ['rm', 'mv', 'dd', 'mkfs', 'shutdown', 'reboot', 'init', 'poweroff', 'halt', 'fdisk', 'parted', 'sudo']

def wrap_text(text, width):
    """Wrap text to fit within a given width."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word)
        if current_length + word_length + len(current_line) <= width:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = word_length
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def wrap_command(command, width):
    """
    Wrap a command intelligently, breaking at spaces or special characters.
    Continuation lines are indented.
    """
    if len(command) <= width - 2:
        return [f"  {command}"]
    
    lines = []
    current_line = "  "
    indent = "    "  # Indentation for continuation lines
    
    # Try to break at logical points: spaces, pipes, semicolons
    tokens = []
    current_token = ""
    
    for char in command:
        current_token += char
        if char in (' ', '|', ';', '&'):
            tokens.append(current_token)
            current_token = ""
    if current_token:
        tokens.append(current_token)
    
    for token in tokens:
        # Check if adding this token would exceed width
        test_line = current_line + token
        
        if len(test_line) <= width:
            current_line += token
        else:
            # Start a new line
            if current_line.strip():
                lines.append(current_line)
            current_line = indent + token.lstrip()
    
    # Add the last line
    if current_line.strip():
        lines.append(current_line)
    
    return lines if lines else [f"  {command}"]


def display_function_calls(function_calls):
    """Display function calls in a nicely formatted way."""
    if not function_calls:
        return
    
    click.echo()
    click.echo(click.style("═" * 60, fg="yellow"))
    click.echo(click.style("  Function Calls", fg="yellow", bold=True))
    click.echo(click.style("═" * 60, fg="yellow"))
    
    for i, func in enumerate(function_calls, 1):
        func_name = func["name"]
        func_args = func.get("args", {})
        
        # Format the function name
        click.echo(click.style(f"\n  {i}. ", fg="white") + click.style(f"{func_name}", fg="cyan", bold=True) + click.style("(", fg="white"))
        
        # Format arguments with nice indentation
        if func_args:
            for key, value in func_args.items():
                # Format the value nicely
                if isinstance(value, str):
                    formatted_value = click.style(f'"{value}"', fg="green")
                else:
                    formatted_value = click.style(str(value), fg="magenta")
                
                click.echo(click.style(f"       {key}", fg="white") + click.style("=", fg="white") + formatted_value)
            click.echo(click.style("     )", fg="white"))
        else:
            click.echo(click.style("     )", fg="white"))
    
    click.echo()


def display_command_and_explanation(response):
    """Display command and explanation side by side."""
    command = response.get("command", "")
    explanation = response.get("explanation", "")
    
    if not command:
        return
    
    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns
    
    # Calculate column widths (35% for command, 65% for explanation)
    min_command_width = 25
    # min_explanation_width = 35
    
    # Use stacked layout for very narrow terminals (< 70 chars)
    if terminal_width < 70:
        _display_command_stacked(response)
        _display_explanation_stacked(response)
        return
    
    command_width = max(min_command_width, int(terminal_width * 0.35))
    explanation_width = terminal_width - command_width - 5  # 5 for spacing/borders
    
    # Wrap the explanation text
    explanation_lines = wrap_text(explanation, explanation_width - 4) if explanation else []
    
    # Wrap the command intelligently
    command_lines = wrap_command(command, command_width)
    
    click.echo()
    click.echo(click.style("═" * terminal_width, fg="green"))

    # Header row
    header_left = "  Command"
    header_right = "Explanation"
    click.echo(
        click.style(header_left.ljust(command_width), fg="green", bold=True) +
        click.style(" │ ", fg="white", dim=True) +
        click.style(header_right, fg="green", bold=True)
    )
    click.echo(click.style("─" * terminal_width, fg="white", dim=True))
    
    # Pad to have same number of lines
    max_lines = max(len(command_lines), len(explanation_lines))
    command_lines += [''] * (max_lines - len(command_lines))
    explanation_lines += [''] * (max_lines - len(explanation_lines))
    
    # Display side by side
    for cmd_line, exp_line in zip(command_lines, explanation_lines):
        cmd_styled = click.style(cmd_line.ljust(command_width), fg="cyan", bold=True)
        separator = click.style(" │ ", fg="white", dim=True)
        exp_styled = f"  {exp_line}"
        
        click.echo(cmd_styled + separator + exp_styled)
    
    click.echo(click.style("═" * terminal_width, fg="green"))
    click.echo()


def _display_command_stacked(response):
    """Fallback: Display command in stacked layout."""
    command = response.get("command", "")
    if not command:
        return
    
    terminal_width = shutil.get_terminal_size().columns
    terminal_width = min(terminal_width, 80)  # Cap at 80
    
    click.echo()
    click.echo(click.style("═" * terminal_width, fg="green"))
    click.echo(click.style("  Command", fg="green", bold=True))
    click.echo(click.style("═" * terminal_width, fg="green"))
    click.echo()
    click.echo(click.style(f"  {command}", fg="cyan", bold=True))
    click.echo()


def _display_explanation_stacked(response):
    """Fallback: Display explanation in stacked layout."""
    explanation = response.get("explanation", "")
    if not explanation:
        return
    
    terminal_width = shutil.get_terminal_size().columns
    terminal_width = min(terminal_width, 80)  # Cap at 80
    
    click.echo(click.style("─" * terminal_width, fg="white", dim=True))
    click.echo(click.style("  Explanation", fg="white", bold=True))
    click.echo(click.style("─" * terminal_width, fg="white", dim=True))
    click.echo()
    
    # Wrap explanation text for narrow terminals
    wrapped_lines = wrap_text(explanation, terminal_width - 4)
    for line in wrapped_lines:
        click.echo(f"  {line}")
    
    click.echo()
    click.echo(click.style("═" * terminal_width, fg="green"))
    click.echo()


def display_text_response(message_text):
    """Display a text response (warning, error, or info)."""
    # Determine the color based on message content
    is_warning = "Warning" in message_text or "warning" in message_text
    is_error = "Error" in message_text or "error" in message_text
    
    if is_error:
        color = "red"
        title = "Error"
    elif is_warning:
        color = "yellow"
        title = "Warning"
    else:
        color = "blue"
        title = "Response"
    
    # Get terminal width for proper formatting
    terminal_width = shutil.get_terminal_size().columns
    terminal_width = min(terminal_width, 100)  # Cap at 100 for readability
    
    # Show the message with nice formatting
    click.echo()
    click.echo(click.style("═" * terminal_width, fg=color))
    click.echo(click.style(f"  {title}", fg=color, bold=True))
    click.echo(click.style("═" * terminal_width, fg=color))
    click.echo()
    
    # Wrap the message text to fit terminal width
    wrapped_lines = wrap_text(message_text, terminal_width - 4)
    for line in wrapped_lines:
        click.echo(f"  {line}")
    
    click.echo()
    click.echo(click.style("─" * terminal_width, fg="white", dim=True))
    click.echo()

def prompt_user_action(command: str) -> tuple[str, str | None]:
    """Prompt user for action and return their choice."""
    click.echo()
    click.echo(click.style("What would you like to do with this command?", fg="yellow", bold=True))

    if any(command.strip().startswith(dc) for dc in DANGEROUS_COMMANDS):
        click.echo(click.style("  [R]un the command. WARNING: This command could be potentially harmful!", fg="red", bold=True))
        click.echo(click.style("  Read the command carefully and only run if you are sure!", fg="red"))
    else:
        click.echo(click.style("  [R]un the command", fg="white"))

    click.echo(click.style("  [C]opy to clipboard", fg="white"))
    click.echo(click.style("  [Q]uit", fg="white"))
    click.echo(click.style("  Or type a follow-up question", fg="cyan", dim=True))
    click.echo()
    
    choice = click.prompt(
        click.style("Your choice", fg="yellow"),
        default='q',
        show_default=False
    ).strip().lower()
    
    # Return the choice (single letter or full text for follow-up)
    if choice in ['r', 'run']:
        return ('run', None)
    elif choice in ['c', 'copy']:
        return ('copy', None)
    elif choice in ['q', 'quit', '']:
        return ('quit', None)
    else:
        # It's a follow-up question
        return ('followup', choice)


def execute_command(command: str, explanation: str = "", user_request: str = ""):
    """Execute a bash command in a subshell and show output in real-time."""
    try:
        # Log to Supabase before execution
        if explanation:
            logger = get_supabase_logger()
            result = logger.log_command(command, explanation, user_request)
            
        
        # Use subprocess with shell=True to run the command
        # This runs in a subshell, so it won't affect the current environment
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            # Don't capture output - let it print directly to terminal
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


def copy_to_clipboard(command: str, explanation: str = "", user_request: str = ""):
    """Copy command to clipboard using available clipboard tools."""
    # Log to Supabase when copying
    if explanation:
        logger = get_supabase_logger()
        logger.log_command(command, explanation, user_request)
    
    # Try different clipboard tools in order of preference
    clipboard_commands = [
        ['wl-copy'],           # Wayland
        ['xclip', '-selection', 'clipboard'],  # X11
        ['xsel', '--clipboard', '--input'],    # X11 alternative
        ['pbcopy'],            # macOS
    ]
    
    for clipboard_cmd in clipboard_commands:
        try:
            # Check if the clipboard tool exists
            if subprocess.run(['which', clipboard_cmd[0]], 
                            capture_output=True, 
                            text=True).returncode == 0:
                # Copy to clipboard
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
    
    # If no clipboard tool worked, show a fallback message
    click.echo(click.style("[ERROR] No clipboard tool found!", fg="red", bold=True))
    click.echo(click.style("  Install one of: wl-copy, xclip, xsel", fg="yellow"))
    click.echo()
    click.echo(click.style("  Here's the command to copy manually:", fg="white", bold=True))
    click.echo(click.style(f"  {command}", fg="cyan", bold=True))
    return False
