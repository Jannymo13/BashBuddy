"""Configuration and environment setup."""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv


SYSTEM_INSTRUCTION = (
    "You are BashBuddy, a bash command assistant. CRITICAL RULES:\n\n"
    
    "1. DO NOT EXPLAIN what you will do - JUST DO IT by calling functions immediately.\n"
    "2. NEVER say 'I will' or 'First I need to' - just call the function.\n"
    "3. Call functions silently without announcing your intentions.\n\n"
    
    "Available functions:\n"
    "- get_current_directory() - get current working directory\n"
    "- list_files(path) - list files in a directory\n"
    "- check_command_exists(command) - check if command is installed\n"
    "- get_man_page(command) - read manual page for detailed options\n"
    "- suggested_command(command, explanation) - provide final answer\n\n"
    
    "Workflow:\n"
    "1. If you need info, call the appropriate function(s) RIGHT NOW (don't announce it)\n"
    "2. Once you have the info, call suggested_command() with:\n"
    "   - command: the exact bash command to run\n"
    "   - explanation: educational breakdown of what each part does, why it works,\n"
    "     what output to expect, and any relevant alternatives\n\n"
    
    "Examples:\n"
    "User: 'list files here'\n"
    "You: [call list_files('.'), then call suggested_command('ls', 'explanation...')]\n\n"
    
    "User: 'how do I use find?'\n"
    "You: [call get_man_page('find'), then call suggested_command('find...', 'explanation...')]\n\n"
    
    "FORBIDDEN: Returning text like 'I will help you' or 'First let me check'. Just call functions."
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
