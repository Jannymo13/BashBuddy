"""Text formatting and display utilities for CLI output."""

import click
import shutil


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
            current_line = indent + token
    
    # Add final line
    if current_line.strip():
        lines.append(current_line)
    
    return lines


def display_function_calls(function_calls):
    """Display function calls in a formatted box."""
    if not function_calls:
        return
    
    terminal_width = shutil.get_terminal_size().columns
    box_width = min(60, terminal_width - 4)
    
    # Header
    click.echo()
    click.echo("═" * box_width)
    click.echo(click.style("  Function Calls", fg="yellow", bold=True))
    click.echo("═" * box_width)
    click.echo()
    
    # Display each function call
    for i, call in enumerate(function_calls, 1):
        func_name = call['name']
        args = call.get('arguments', {})
        
        # Format function signature
        click.echo(click.style(f"  {i}. {func_name}(", fg="cyan"))
        
        # Format arguments
        for key, value in args.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 60:
                value_str = value_str[:57] + "..."
            
            # Handle multiline values
            if '\n' in value_str:
                lines = value_str.split('\n')
                click.echo(f"       {key}=\"{lines[0]}\"")
                for line in lines[1:]:
                    click.echo(f"       {line}")
            else:
                click.echo(f"       {key}=\"{value_str}\"")
        
        click.echo("     )")
        click.echo()


def display_command_and_explanation(response):
    """Display command and explanation side by side in a formatted table."""
    terminal_width = shutil.get_terminal_size().columns
    
    # Use full terminal width, minus some padding
    table_width = min(terminal_width - 4, 100)
    command_width = int(table_width * 0.3)  # 30% for command
    explanation_width = table_width - command_width - 3  # Rest for explanation (minus separators)
    
    command = response['command']
    explanation = response['explanation']
    
    # Wrap text
    command_lines = wrap_command(command, command_width)
    explanation_lines = wrap_text(explanation, explanation_width)
    
    # Make lists same length
    max_lines = max(len(command_lines), len(explanation_lines))
    while len(command_lines) < max_lines:
        command_lines.append("")
    while len(explanation_lines) < max_lines:
        explanation_lines.append("")
    
    # Print table
    click.echo()
    click.echo("═" * table_width)
    click.echo(
        click.style(f"  {'Command':<{command_width}}", fg="green", bold=True) +
        "│ " +
        click.style(f"{'Explanation'}", fg="green", bold=True)
    )
    click.echo("─" * table_width)
    
    for cmd_line, exp_line in zip(command_lines, explanation_lines):
        # Pad command line
        cmd_display = cmd_line.ljust(command_width)
        exp_display = f"  {exp_line}"
        
        click.echo(
            click.style(cmd_display, fg="cyan", bold=True) +
            "│" +
            exp_display
        )
    
    click.echo("═" * table_width)


def display_text_response(message_text):
    """Display a text response in a formatted box."""
    terminal_width = shutil.get_terminal_size().columns
    box_width = min(terminal_width - 4, 100)
    
    click.echo()
    click.echo("═" * box_width)
    click.echo(click.style("  Response", fg="green", bold=True))
    click.echo("═" * box_width)
    click.echo()
    
    # Wrap text to fit
    content_width = box_width - 4
    lines = wrap_text(message_text, content_width)
    
    for line in lines:
        click.echo(f"  {line}")
    
    click.echo()
    click.echo("─" * box_width)
