"""Main daemon server - refactored version."""

import os
import json
import socket
import threading
import signal
import sys
from google import genai
from google.genai import types

from bashbuddy.core.config import setup_logging, load_api_key, SYSTEM_INSTRUCTION
from bashbuddy.daemon.functions import create_function_declarations, execute_function


logger = setup_logging()


class BashBuddyDaemon:
    """Daemon that maintains Gemini client and conversation history."""

    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.client = None
        self.history = []
        self.running = False
        self.server_socket = None
        
        # Create function declarations
        self.tool = create_function_declarations()

    def start(self):
        """Start the daemon server."""
        # Load API key
        api_key = load_api_key(logger)

        # Initialize Gemini client
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
                message = request.get("message")
                force_fresh = request.get("force_fresh", False)
                response = self._handle_ask(message, force_fresh=force_fresh)
            elif command == "ping":
                response = {"status": "ok", "message": "pong"}
            elif command == "reset":
                response = self._handle_reset()
            elif command == "history":
                response = self._handle_history()
            elif command == "status":
                response = {"status": "ok", "message": "Daemon is running"}
            else:
                response = {"status": "error", "message": f"Unknown command: {command}"}

            # Send response
            response_data = json.dumps(response).encode("utf-8") + b"\n\n"
            client_socket.sendall(response_data)

        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            error_response = {"status": "error", "message": f"Failed to generate response: {str(e)}"}
            try:
                client_socket.sendall(json.dumps(error_response).encode("utf-8") + b"\n\n")
            except:
                pass
        finally:
            client_socket.close()

    def _handle_ask(self, message: str, force_fresh: bool = False):
        """Process a question using Gemini with function calling."""
        try:
            # Check if we have an exact match in history (unless force_fresh)
            if not force_fresh:
                cached_result = self._check_history_cache(message)
                if cached_result:
                    logger.info(f"Cache hit for query: {message[:50]}...")
                    return cached_result
            
            # Add user message to history
            self.history.append({"role": "user", "content": message})

            function_history = []
            
            # Build conversation contents from history
            contents = []
            for msg in self.history:
                if msg["role"] == "user":
                    contents.append(msg["content"])
                elif msg["role"] == "assistant":
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg["content"]}]
                    })
            
            logger.debug(f"Conversation history length: {len(self.history)} messages")
            logger.debug(f"Sending {len(contents)} content items to Gemini")

            # Function calling loop
            max_iterations = 10
            retry_count = 0  # Track if we've retried for text response
            for iteration in range(max_iterations):
                # Call Gemini with tools enabled
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=[self.tool],
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    ),
                )

                # Extract response
                candidate = response.candidates[0]
                part = candidate.content.parts[0]

                # Check if Gemini called a function
                if hasattr(part, 'function_call') and part.function_call:
                    func_call = part.function_call
                    func_name = func_call.name
                    func_args = dict(func_call.args)
                    
                    logger.debug(f"[Iteration {iteration+1}] Calling: {func_name}({func_args})")
                    
                    # Store function call
                    function_history.append({
                        "name": func_name,
                        "args": func_args
                    })

                    # Execute the function
                    result = execute_function(func_name, func_args)
                    logger.debug(f"[Iteration {iteration+1}] Result: {result}")

                    # Check if this is the final answer
                    if result.get("is_final_answer"):
                        self.history.append({
                            "role": "assistant",
                            "content": f"Command: {result['command']}\nExplanation: {result['explanation']}"
                        })
                        
                        return {
                            "status": "ok",
                            "command": result["command"],
                            "explanation": result["explanation"],
                            "history_length": len(self.history),
                            "function_calls": function_history
                        }

                    # Add function call and response to conversation
                    contents.append({
                        "role": "model",
                        "parts": [{"function_call": func_call}]
                    })

                    contents.append({
                        "role": "function",
                        "parts": [{
                            "function_response": {
                                "name": func_name,
                                "response": result
                            }
                        }]
                    })

                    continue

                else:
                    # Gemini returned text instead of function call
                    answer = part.text
                    
                    logger.warning(f"[Iteration {iteration+1}] Gemini returned text instead of function call: {answer[:100]}...")
                    
                    # Retry once with a strong reminder to use suggested_command
                    if retry_count == 0:
                        retry_count += 1
                        logger.info("Retrying with stronger instruction to use suggested_command")
                        
                        # Add the text response to conversation
                        contents.append({
                            "role": "model",
                            "parts": [{"text": answer}]
                        })
                        
                        # Add a VERY strong reminder
                        contents.append({
                            "role": "user",
                            "parts": [{"text": (
                                "CRITICAL: You MUST call the suggested_command() function now. "
                                "Do NOT respond with text. Your response above should be converted "
                                "to a suggested_command(command, explanation) function call. "
                                "Extract the command and explanation from your text and call the function."
                            )}]
                        })
                        
                        continue  # Try again
                    
                    # Already retried once, accept the text response
                    logger.info("Already retried once, accepting text response")
                    
                    self.history.append({"role": "assistant", "content": answer})
                    
                    return {
                        "status": "ok",
                        "message": answer,
                        "history_length": len(self.history),
                        "function_calls": function_history
                    }

            # Hit max iterations
            logger.warning(f"Hit max iterations ({max_iterations}). Function calls made: {len(function_history)}")
            
            # Find last text response
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
                "function_calls": function_history
            }

        except Exception as e:
            logger.error(f"Error in _handle_ask: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate response: {str(e)}"
            }

    def _check_history_cache(self, query: str):
        """
        Check if we have an exact match for this query in history.
        Returns the cached response if found, None otherwise.
        """
        # Look for matching user query in history
        for i in range(len(self.history) - 1):
            if self.history[i]["role"] == "user" and self.history[i]["content"].strip().lower() == query.strip().lower():
                # Found a match! Get the next assistant response
                if i + 1 < len(self.history) and self.history[i + 1]["role"] == "assistant":
                    cached_response = self.history[i + 1]["content"]
                    
                    # Parse the cached response to extract command and explanation
                    if "Command:" in cached_response and "Explanation:" in cached_response:
                        lines = cached_response.split("\n")
                        command = ""
                        explanation = ""
                        
                        for line in lines:
                            if line.startswith("Command:"):
                                command = line.replace("Command:", "").strip()
                            elif line.startswith("Explanation:"):
                                explanation = line.replace("Explanation:", "").strip()
                        
                        if command:
                            return {
                                "status": "ok",
                                "type": "command",
                                "command": command,
                                "explanation": explanation,
                                "cached": True,
                                "history_length": len(self.history)
                            }
        
        return None

    def _handle_reset(self):
        """Reset conversation history."""
        self.history = []
        return {"status": "ok", "message": "✓ Conversation history cleared"}

    def _handle_history(self):
        """Return conversation history."""
        return {
            "status": "ok",
            "history": self.history,
            "count": len(self.history)
        }

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        logger.info("Shutting down daemon...")
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        sys.exit(0)
