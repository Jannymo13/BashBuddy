"""Supabase logging for command history."""

import os
import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseLogger:
    """Log commands to Supabase database."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Supabase client if credentials are available."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            logger.info("Supabase not configured - command logging disabled (optional feature)")
            return
        
        try:
            self.client = create_client(url, key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def determine_category(self, command: str) -> str:
        """
        Determine command category based on the first word.
        
        Groups common commands into categories, otherwise uses first word.
        """
        if not command or not command.strip():
            return "unknown"
        
        # Get first word (command name)
        first_word = command.strip().split()[0]
        
        # Define category mappings for common commands
        categories = {
            # File operations
            "ls": "file_operations",
            "cd": "file_operations",
            "pwd": "file_operations",
            "mkdir": "file_operations",
            "rmdir": "file_operations",
            "rm": "file_operations",
            "cp": "file_operations",
            "mv": "file_operations",
            "touch": "file_operations",
            "cat": "file_operations",
            "less": "file_operations",
            "more": "file_operations",
            "head": "file_operations",
            "tail": "file_operations",
            
            # Search and filter
            "find": "search",
            "grep": "search",
            "locate": "search",
            "which": "search",
            "whereis": "search",
            
            # Text processing
            "sed": "text_processing",
            "awk": "text_processing",
            "cut": "text_processing",
            "sort": "text_processing",
            "uniq": "text_processing",
            "wc": "text_processing",
            "tr": "text_processing",
            
            # System info
            "ps": "system_info",
            "top": "system_info",
            "htop": "system_info",
            "df": "system_info",
            "du": "system_info",
            "free": "system_info",
            "uname": "system_info",
            "uptime": "system_info",
            
            # Network
            "ping": "network",
            "curl": "network",
            "wget": "network",
            "ssh": "network",
            "scp": "network",
            "netstat": "network",
            "ifconfig": "network",
            "ip": "network",
            
            # Permissions
            "chmod": "permissions",
            "chown": "permissions",
            "chgrp": "permissions",
            
            # Archives
            "tar": "archives",
            "zip": "archives",
            "unzip": "archives",
            "gzip": "archives",
            "gunzip": "archives",
            
            # Package management
            "apt": "package_management",
            "apt-get": "package_management",
            "dnf": "package_management",
            "yum": "package_management",
            "pacman": "package_management",
            "brew": "package_management",
            
            # Version control
            "git": "git",
            "svn": "version_control",
            
            # Docker
            "docker": "docker",
            "docker-compose": "docker",
            
            # Other
            "sudo": "privileges",
            "su": "privileges",
        }
        
        # Return mapped category or use first word
        return categories.get(first_word, first_word)
    
    def log_command(self, command: str, explanation: str, user_request: str) -> bool:
        """
        Log a command to Supabase.
        
        Paramaters:
            command: The bash command
            explanation: Gemini's explanation
            user_request: The user's original question/request
        
        Returns True if successful, False otherwise.
        """
        if not self.client:
            logger.debug("Supabase not configured - skipping command log")
            return False
        
        try:
            category = self.determine_category(command)
            
            # Build data with only non-empty fields - don't include user
            data = {
                "user": "a25c7126-1d92-4902-a217-2a32cc807550",
                "query": user_request,
                "suggested_command": command,
                "cmd": category,
                "response": explanation
            }
            
            logger.info(f"Attempting to insert into requests table: {data}")
            
            # Insert into the requests table
            response = self.client.table("requests").insert(data).execute()
            
            logger.info(f"Supabase insert response: {response}")
            logger.info(f"✓ Logged command to Supabase: {command[:50]}... (category: {category})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log command to Supabase: {e}")
            return False


# Global instance
_supabase_logger: Optional[SupabaseLogger] = None


def get_supabase_logger() -> SupabaseLogger:
    """Get or create the global Supabase logger instance."""
    global _supabase_logger
    if _supabase_logger is None:
        _supabase_logger = SupabaseLogger()
    return _supabase_logger
