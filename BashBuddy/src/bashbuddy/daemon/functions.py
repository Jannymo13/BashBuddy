"""Function declarations and execution for Gemini function calling."""

import os
import shutil
import subprocess
from google.genai import types


def create_function_declarations():
    """Create all function declarations for Gemini."""
    
    get_current_dir_decl = types.FunctionDeclaration(
        name="get_current_directory",
        description="Get the user's current working directory path"
    )
    
    list_files_decl = types.FunctionDeclaration(
        name="list_files",
        description="List files and directories in a given path",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "path": types.Schema(
                    type=types.Type.STRING,
                    description="The directory path to list (use '.' for current)"
                )
            },
            required=["path"]
        )
    )
    
    check_command_decl = types.FunctionDeclaration(
        name="check_command_exists",
        description="Check if a bash command or program is installed on the system",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "command": types.Schema(
                    type=types.Type.STRING,
                    description="The command name to check (e.g., 'git', 'docker')"
                )
            },
            required=["command"]
        )
    )

    man_command_decl = types.FunctionDeclaration(
        name="get_man_page",
        description="Retrieve the manual page for a given bash command",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "command": types.Schema(
                    type=types.Type.STRING,
                    description="The command name to get the manual for (e.g., 'ls', 'grep')"
                ),
                "section": types.Schema(
                    type=types.Type.STRING,
                    description="Optional: Manual section number (1-8). Most commands are in section 1. Leave empty for default."
                )
            },
            required=["command"]
        )
    )
    
    suggested_command_decl = types.FunctionDeclaration(
        name="suggested_command",
        description="Provide the bash command that answers the user's question. Call this with the final command after explaining it.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "command": types.Schema(
                    type=types.Type.STRING,
                    description="The bash command to run"
                ),
                "explanation": types.Schema(
                    type=types.Type.STRING,
                    description="Brief explanation of what the command does"
                )
            },
            required=["command", "explanation"]
        )
    )
    
    return types.Tool(function_declarations=[
        get_current_dir_decl,
        list_files_decl,
        check_command_decl,
        suggested_command_decl,
        man_command_decl
    ])


def execute_function(function_name: str, arguments: dict):
    """
    Execute a function that Gemini requested.
    
    When Gemini decides it needs information, it will call one of the
    declared functions. This method routes that call to the actual Python code.
    """
    
    if function_name == "get_current_directory":
        # No arguments needed - just return the current directory
        return {"result": os.getcwd()}
    
    elif function_name == "list_files":
        # Get the path argument (defaults to current directory)
        path = arguments.get("path", ".")
        try:
            # List files and return first 20 (to avoid huge responses)
            files = os.listdir(path)
            return {
                "result": files[:20],  # Limit to 20 files
                "count": len(files),   # Total count
                "truncated": len(files) > 20  # Was it truncated?
            }
        except Exception as e:
            # If path doesn't exist or permission denied
            return {"error": str(e)}
    
    elif function_name == "check_command_exists":
        # Check if a command is in the system PATH
        command = arguments.get("command")
        # shutil.which() returns path to command or None
        exists = shutil.which(command) is not None
        return {
            "exists": exists,
            "command": command
        }
    
    elif function_name == "get_man_page":
        # Get the manual page for a command
        command = arguments.get("command")
        section = arguments.get("section", "")  # Optional section number
        
        try:
            # Build the man command
            if section:
                man_cmd = ["man", section, command]
            else:
                man_cmd = ["man", command]
            
            # Run man command and capture output
            result = subprocess.run(
                man_cmd,
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            if result.returncode == 0:
                # Man page found - truncate to reasonable size (first 100 lines)
                lines = result.stdout.split('\n')
                truncated = '\n'.join(lines[:100])
                
                return {
                    "found": True,
                    "command": command,
                    "content": truncated,
                    "truncated": len(lines) > 100,
                    "total_lines": len(lines)
                }
            else:
                # Man page not found
                return {
                    "found": False,
                    "command": command,
                    "error": result.stderr.strip() or f"No manual entry for {command}"
                }
        
        except subprocess.TimeoutExpired:
            return {
                "found": False,
                "command": command,
                "error": "Command timed out"
            }
        except Exception as e:
            return {
                "found": False,
                "command": command,
                "error": str(e)
            }
    
    elif function_name == "suggested_command":
        # Gemini is providing the final command suggestion
        # Store it so we can return it to the user
        command = arguments.get("command")
        explanation = arguments.get("explanation")
        
        # Store these for use in the response
        # We'll mark this specially so _handle_ask knows to return it
        return {
            "command": command,
            "explanation": explanation,
            "is_final_answer": True  # Signal that this is the answer
        }
    
    else:
        return {"error": f"Unknown function: {function_name}"}
