    # BashBuddy 🤖

Your intelligent terminal command assistant powered by Google's Gemini AI.

BashBuddy helps you find the right bash commands by understanding what you want to do in natural language. No more memorizing complex commands or searching through man pages!

## Features

✨ **Natural Language Queries** - Ask questions in plain English  
🧠 **AI-Powered** - Uses Google Gemini for intelligent command suggestions  
📝 **Command History** - Remembers your previous queries with instant cache  
🔄 **Interactive Mode** - Autocomplete from your history as you type  
⚡ **Fast & Efficient** - Daemon-based architecture for quick responses  
🎨 **Beautiful CLI** - Clean, colorful terminal interface

## Installation

### Prerequisites

- Python 3.13 or higher
- Google Gemini API key
- (Optional) Supabase account for logging

### Install from PyPI

```bash
pip install bashbuddy
```

### Install from source

```bash
git clone https://github.com/Jannymo13/bashbuddy.git
cd bashbuddy
pip install .
```

## ⚠️ Important: First-Time Setup

**After installation, you MUST configure your API key:**

```bash
# Create config directory
mkdir -p ~/.bashbuddy

# Create config file
cat > ~/.bashbuddy/.env << 'EOF'
GEMINI_API_KEY=your_actual_key_here
EOF
```

Replace `your_actual_key_here` with your real Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

📖 **See [SETUP.md](SETUP.md) for detailed setup instructions.**

## Quick Start

Once configured, start using BashBuddy:

```bash
bb ask "list all Python files"
```

## Usage

### Interactive Mode

Launch interactive mode with autocomplete from history:

```bash
bb
```

Type your question and press Tab to see suggestions from your history!

### Direct Queries

Ask a question directly:

```bash
bb ask "find large files"
bb ask "compress a directory"
bb ask "check disk usage"
```

### Command History

View your previous queries:

```bash
bb history
```

Use arrow keys to select a command, then run, copy, or quit.

### Daemon Management

```bash
bb start    # Start the daemon
bb stop     # Stop the daemon
bb reset    # Clear conversation history
```

## Examples

```bash
# Find files
bb ask "find all PDF files in current directory"
→ find . -name "*.pdf"

# System monitoring
bb ask "show disk usage"
→ df -h

# File operations
bb ask "compress folder into tar.gz"
→ tar -czf archive.tar.gz folder/

# Git commands
bb ask "undo last commit but keep changes"
→ git reset --soft HEAD~1

# Process management
bb ask "kill process on port 3000"
→ lsof -ti:3000 | xargs kill -9
```

## Features in Detail

### Smart Caching

BashBuddy remembers your queries. If you ask the same question twice, it instantly returns the cached result:

```
[CACHED] Retrieved result from history (exact match)
         Press [F] to force a fresh query
```

### Dangerous Command Warnings

BashBuddy warns you about potentially dangerous commands like `rm`, `dd`, or `sudo`:

```
⚠️  WARNING: This command could be potentially harmful!
Read the command carefully and only run if you are sure!
```

### Function Calling

BashBuddy can call helper functions to get context before suggesting commands:
- `list_files()` - Check current directory
- `check_command_exists()` - Verify command availability
- `get_man_page()` - Read command documentation

## Configuration

BashBuddy uses a daemon architecture for fast responses. The daemon:
- Auto-starts when needed
- Maintains conversation context
- Caches results for speed
- Runs in the background

Configuration files are stored in `~/.bashbuddy/`

## Development

```bash
# Clone the repo
git clone https://github.com/Jannymo13/bashbuddy.git
cd bashbuddy

# Install with poetry
poetry install

# Run in development
poetry run bb ask "your question"

# Run tests
poetry run pytest
```

## Project Structure

```
bashbuddy/
├── cli/              # CLI interface
│   ├── actions.py    # Command execution
│   ├── commands.py   # Command handlers
│   └── formatting.py # Display utilities
├── daemon/           # Background daemon
│   ├── client.py     # Socket communication
│   ├── manager.py    # Lifecycle management
│   ├── server.py     # Main daemon server
│   └── functions.py  # AI function tools
└── core/             # Core utilities
    ├── config.py     # Configuration
    └── supabase_logger.py  # Analytics
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Author

Created by [Jannymo13](https://github.com/Jannymo13)

## Acknowledgments

- Powered by [Google Gemini AI](https://deepmind.google/technologies/gemini/)
- Built with [Click](https://click.palletsprojects.com/) and [Questionary](https://github.com/tmbo/questionary)
