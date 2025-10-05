import click
import shutil
from bashbuddy.utils import send_command, ensure_daemon_running


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
    
    is_first_line = True
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
            is_first_line = False
    
    # Add the last line
    if current_line.strip():
        lines.append(current_line)
    
    return lines if lines else [f"  {command}"]


def display_command_and_explanation(response):
    """Display command and explanation side by side."""
    command = response.get("command", "")
    explanation = response.get("explanation", "")
    
    if not command:
        return
    
    # Get terminal width
    terminal_width = shutil.get_terminal_size().columns
    
    # Calculate column widths (40% for command, 60% for explanation)
    # But ensure minimum widths
    min_command_width = 30
    min_explanation_width = 40
    
    if terminal_width < 80:
        # Terminal too narrow, fall back to stacked layout
        display_command_stacked(response)
        display_explanation_stacked(response)
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


def display_command_stacked(response):
    """Fallback: Display command in stacked layout."""
    command = response.get("command", "")
    if not command:
        return
    
    click.echo()
    click.echo(click.style("═" * 60, fg="green"))
    click.echo(click.style("  Suggested Command", fg="green", bold=True))
    click.echo(click.style("═" * 60, fg="green"))
    click.echo()
    click.echo(click.style(f"  {command}", fg="white", bold=True))


def display_explanation_stacked(response):
    """Fallback: Display explanation in stacked layout."""
    explanation = response.get("explanation", "")
    if not explanation:
        return
    
    click.echo()
    click.echo(click.style("─" * 60, fg="white", dim=True))
    click.echo(click.style("  Explanation", fg="white", bold=True))
    click.echo(click.style("─" * 60, fg="white", dim=True))
    click.echo()
    click.echo(f"  {explanation}")
    click.echo()

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
    if cmd: message = f"Help for command '{cmd}': {request}"
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

        else:
            # Regular text response - still show function calls if any
            display_function_calls(response.get("function_calls"))
            
            # Determine the color based on message content
            message_text = response["message"]
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
    else:
        click.echo(f"Error: {response.get('message', 'Unknown error')}", err=True)
        raise click.Abort()
