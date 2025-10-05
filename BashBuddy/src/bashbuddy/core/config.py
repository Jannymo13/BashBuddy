"""Configuration and environment setup."""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv


def load_environment():
    """Load environment variables from .env file."""
    env_locations = [
        Path.cwd() / ".env",  # Current working directory
        Path.home() / ".bashbuddy" / ".env",  # ~/.bashbuddy/.env
        Path(__file__).parent.parent.parent.parent / ".env",  # Project root
    ]
    
    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path)
            return True
    
    return False


SYSTEM_INSTRUCTION = (
    "You are BashBuddy, a bash command assistant. YOUR ONLY JOB is to provide bash commands.\n\n"
    
    "CRITICAL RULES - FOLLOW THESE EXACTLY:\n"
    "1. ALWAYS end with suggested_command() - NEVER return plain text\n"
    "2. EVERY response must provide an executable bash command\n"
    "3. Even for follow-up questions, you MUST call suggested_command()\n"
    "4. DO NOT explain what you will do - just call functions silently\n"
    "5. NEVER say 'I will' or 'First I need to' - just execute\n"
    "6. Commands MUST be syntactically correct and actually work in bash\n"
    "7. Test your commands mentally before suggesting them\n\n"
    
    "IMPORTANT BASH RULES:\n"
    "- `ls` takes directories as arguments, NOT patterns. Use `find` for pattern matching.\n"
    "- To find files by pattern: use `find . -name \"pattern\"`\n"
    "- To list specific files: let the shell expand globs, or use `find`\n"
    "- Always provide working, tested command patterns\n\n"
    
    "Available functions:\n"
    "- get_current_directory() - get current working directory\n"
    "- list_files(path) - list files in a directory\n"
    "- check_command_exists(command) - check if command is installed\n"
    "- get_man_page(command) - read manual page for detailed options\n"
    "- suggested_command(command, explanation) - REQUIRED for every response\n\n"
    
    "Workflow (MANDATORY):\n"
    "1. If you need info → call function(s) silently\n"
    "2. ALWAYS finish by calling suggested_command() with:\n"
    "   - command: exact bash command to run (MUST be syntactically correct)\n"
    "   - explanation: educational breakdown (what it does, why, output, alternatives)\n\n"
    
    "For follow-up questions:\n"
    "- Modify the previous command based on the follow-up\n"
    "- Still call suggested_command() with the new command\n"
    "- Reference conversation context naturally in explanation\n\n"
    
    "Examples:\n"
    "User: 'list files here'\n"
    "→ [call list_files('.'), call suggested_command('ls', 'explanation')]\n\n"
    
    "User: 'list Python files'\n"
    "→ [call suggested_command('find . -name \"*.py\"', 'explanation')] NOT 'ls *.py'\n\n"
    
    "User: 'only python files'\n"
    "→ [call suggested_command('find . -name \"*.py\"', 'explanation with context')]\n\n"
    
    "FORBIDDEN behaviors:\n"
    "❌ Returning plain text without suggested_command()\n"
    "❌ Saying 'I will help' or any conversational response\n"
    "❌ Explaining your process - just do it\n"
    "❌ Suggesting commands that don't actually work (like 'ls *.py')\n"
    "✅ ALWAYS call suggested_command() - no exceptions!\n"
    "✅ ALWAYS provide syntactically correct, working commands!"
)


def setup_logging():
    """Configure logging to file."""
    log_dir = Path.home() / ".bashbuddy"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "daemon.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to stdout when run manually
        ]
    )
    return logging.getLogger(__name__)


def load_api_key(logger):
    """Load API key from environment."""
    # Load .env from multiple possible locations
    # Try current directory first, then home directory
    env_locations = [
        Path.cwd() / ".env",  # Current working directory
        Path.home() / ".bashbuddy" / ".env",  # ~/.bashbuddy/.env
        Path(__file__).parent.parent.parent.parent / ".env",  # Project root
    ]
    
    env_loaded = False
    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded .env from: {env_path}")
            env_loaded = True
            break
    
    if not env_loaded:
        logger.warning("No .env file found in standard locations")
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("Error: GEMINI_API_KEY not found in environment")
        logger.error(f"Searched locations: {[str(p) for p in env_locations]}")
        logger.error("Please create .env file with: GEMINI_API_KEY=\"your-key-here\"")
        sys.exit(1)
    
    return api_key
