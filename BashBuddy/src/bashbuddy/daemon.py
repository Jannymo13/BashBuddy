"""Background daemon for persistent Gemini client and conversation history."""

import os
import json
import socket
import threading
import signal
import sys
import logging
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv
import shutil

# Set up logging
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

logger = setup_logging()

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


class BashBuddyDaemon:
    """Daemon that maintains Gemini client and conversation history."""

    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.client = None
        self.history = []
        self.running = False
        self.server_socket = None
        
        # Define tool/function declarations for Gemini using the SDK's Schema format
        # These tell Gemini what functions it can call
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
            name="get_command_manual",
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
        
        self.tool = types.Tool(function_declarations=[
            get_current_dir_decl,
            list_files_decl,
            check_command_decl,
            suggested_command_decl,
            man_command_decl
        ])

    def start(self):
        """Start the daemon server."""
        # Load .env from multiple possible locations
        # Try current directory first, then home directory
        from pathlib import Path
        
        env_locations = [
            Path.cwd() / ".env",  # Current working directory
            Path.home() / ".bashbuddy" / ".env",  # ~/.bashbuddy/.env
            Path(__file__).parent.parent.parent / ".env",  # Project root
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
        
        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("Error: GEMINI_API_KEY not found in environment")
            logger.error(f"Searched locations: {[str(p) for p in env_locations]}")
            logger.error("Please create .env file with: GEMINI_API_KEY=\"your-key-here\"")
            sys.exit(1)

        self.client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized")

        self.generation_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            system_instruction=SYSTEM_INSTRUCTION,
        )

        # Remove old socket if it exists
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        # Create Unix socket
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        self.running = True
        logger.info(f"✓ BashBuddy daemon started (socket: {self.socket_path})")
        logger.info("Press Ctrl+C to stop")

        # Accept connections
        while self.running:
            try:
                client_socket, _ = self.server_socket.accept()
                # Handle each request in a separate thread
                thread = threading.Thread(
                    target=self._handle_request, args=(client_socket,), daemon=True
                )
                thread.start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")

    def _handle_request(self, client_socket):
        """Handle a single client request."""
        try:
            # Receive data
            data = b""
            while True:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
                if b"\n\n" in data:  # End marker
                    break

            if not data:
                return

            # Parse request
            request = json.loads(data.decode("utf-8").strip())
            command = request.get("command")


            if command == "ask":
                response = self._handle_ask(request.get("message", ""))
            elif command == "reset":
                response = self._handle_reset()
            elif command == "history":
                response = self._handle_history()
            elif command == "ping":
                response = {"status": "ok", "message": "pong"}
            else:
                response = {"status": "error", "message": f"Unknown command: {command}"}

            # Send response
            response_data = json.dumps(response).encode("utf-8") + b"\n\n"
            client_socket.sendall(response_data)

        except Exception as e:
            error_response = {"status": "error", "message": str(e)}
            try:
                client_socket.sendall(
                    json.dumps(error_response).encode("utf-8") + b"\n\n"
                )
            except:
                pass
        finally:
            client_socket.close()

    def _handle_ask(self, message: str):
        """
        Process a question using the persistent Gemini client with function calling.
        
        This implements a conversation loop where:
        1. We send the user's question to Gemini
        2. Gemini can either:
           a) Return text (we're done)
           b) Request a function call (we execute it and loop again)
        3. We keep looping until Gemini returns text instead of function calls
        """
        try:
            # Add user message to our history
            self.history.append({"role": "user", "content": message})

            function_history = []
            
            # Build the conversation contents from history
            # Convert our history format to Gemini's expected format
            contents = []
            for msg in self.history:
                if msg["role"] == "user":
                    contents.append(msg["content"])
                elif msg["role"] == "assistant":
                    # For assistant messages, add as model response
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg["content"]}]
                    })
            
            logger.debug(f"Conversation history length: {len(self.history)} messages")
            logger.debug(f"Sending {len(contents)} content items to Gemini")

            # Function calling loop - allow up to 10 iterations
            # (prevents infinite loops if something goes wrong)
            max_iterations = 10
            for iteration in range(max_iterations):
                # Call Gemini with tools enabled
                # The 'tools' parameter tells Gemini what functions it can call
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",  # Changed from gemini-2.0-flash-exp for higher rate limits
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=[self.tool],  # ← Pass the Tool object
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    ),
                )

                # Extract the first part of Gemini's response
                # Response structure: candidates[0].content.parts[0]
                candidate = response.candidates[0]
                part = candidate.content.parts[0]

                # If gemini requests a function call, handle it
                if hasattr(part, 'function_call') and part.function_call:
                    # Gemini wants to call a function!
                    func_call = part.function_call
                    func_name = func_call.name
                    func_args = dict(func_call.args)  # Convert to regular dict
                    
                    # Log function call for debugging
                    logger.debug(f"[Iteration {iteration+1}] Calling: {func_name}({func_args})")
                    
                    # Store function call info in a serializable format
                    function_history.append({
                        "name": func_name,
                        "args": func_args
                    })

                    # Execute the requested function
                    result = self.execute_function(func_name, func_args)
                    logger.debug(f"[Iteration {iteration+1}] Result: {result}")

                    # Special handling for suggested_command
                    if result.get("is_final_answer"):
                        # Gemini has provided the final command - return it
                        self.history.append({
                            "role": "assistant",
                            "content": f"Command: {result['command']}\nExplanation: {result['explanation']}"
                        })
                        
                        return {
                            "status": "ok",
                            "command": result["command"],
                            "explanation": result["explanation"],
                            "history_length": len(self.history),
                            "function_calls": [f for f in function_history]
                        }

                    # Add Gemini's function call to the conversation
                    # This shows "Gemini asked to call this function"
                    contents.append({
                        "role": "model",
                        "parts": [{"function_call": func_call}]
                    })

                    # Add our function result to the conversation
                    # This shows "Here's what the function returned"
                    contents.append({
                        "role": "function",
                        "parts": [{
                            "function_response": {
                                "name": func_name,
                                "response": result
                            }
                        }]
                    })

                    # Continue the loop - Gemini will see the result and respond
                    continue

                else:
                    # Gemini returned text instead of calling suggested_command
                    # This might mean the question isn't answerable with a bash command
                    # Don't waste API calls trying to force it - just return the text
                    answer = part.text
                    
                    logger.warning(f"[Iteration {iteration+1}] Gemini returned text instead of function call: {answer[:100]}...")
                    logger.info("Accepting text response instead of forcing function call (saves API calls)")
                    
                    self.history.append({"role": "assistant", "content": answer})
                    
                    return {
                        "status": "ok",
                        "message": answer,
                        "history_length": len(self.history),
                        "function_calls": [f for f in function_history]
                    }

            # If we reach here, we hit the max iterations
            # Gemini never called suggested_command, so return the last text we got
            logger.warning(f"Hit max iterations ({max_iterations}). Function calls made: {len(function_history)}")
            
            # Try to find the last text response in the conversation
            last_text = "No response generated"
            for item in reversed(contents):
                if item.get("role") == "model":
                    parts = item.get("parts", [])
                    if parts and isinstance(parts[0], dict) and "text" in parts[0]:
                        last_text = parts[0]["text"]
                        break
            
            self.history.append({"role": "assistant", "content": last_text})
            return {
                "status": "ok",
                "message": f"[Warning: Exceeded function call limit after {len(function_history)} function calls]\n\n{last_text}",
                "history_length": len(self.history),
                "function_calls": [f for f in function_history]
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate response: {str(e)}",
            }

    def _handle_reset(self):
        """Clear conversation history."""
        self.history = []
        return {"status": "ok", "message": "Conversation history cleared"}

    def _handle_history(self):
        """Return conversation history."""
        return {"status": "ok", "history": self.history, "length": len(self.history)}

    def execute_function(self, function_name: str, arguments: dict):
        """
        Execute a function that Gemini requested.
        
        When Gemini decides it needs information, it will call one of the
        declared functions. This method routes that call to the actual Python code.
        """

        if function_name == "get_current_directory":
            # No arguments needed - just return the current directory
            return {"result": os.getcwd()}

        if function_name == "list_files":
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

        if function_name == "check_command_exists":
            # Check if a command is in the system PATH
            command = arguments.get("command")
            # shutil.which() returns path to command or None
            exists = shutil.which(command) is not None
            return {
                "exists": exists,
                "command": command
            }

        if function_name == "suggested_command":
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
        
        elif function_name == "get_man_page":
            # Get the manual page for a command
            command = arguments.get("command")
            section = arguments.get("section", "")  # Optional section number
            
            try:
                import subprocess
                
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
        
        else:
            return {"error": f"Unknown function: {function_name}"}

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info("Shutting down daemon...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        sys.exit(0)


def get_socket_path():
    """Get the path to the Unix socket."""
    runtime_dir = Path.home() / ".bashbuddy"
    runtime_dir.mkdir(exist_ok=True)
    return str(runtime_dir / "daemon.sock")


def main():
    """Entry point for daemon."""
    socket_path = get_socket_path()
    daemon = BashBuddyDaemon(socket_path)
    daemon.start()


if __name__ == "__main__":
    main()
