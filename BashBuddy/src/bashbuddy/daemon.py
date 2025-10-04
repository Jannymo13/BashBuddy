"""Background daemon for persistent Gemini client and conversation history."""

import os
import json
import socket
import threading
import signal
import sys
from pathlib import Path
from google import genai
from google.genai import types
from dotenv import load_dotenv

SYSTEM_INSTRUCTION = (
    "You are BashBuddy, a helpful bash command assistant, You are designed to help answer "
    "questions about terminal commands. You will provide short concise accurate answers to the user's "
    "questions. You will not provide any additional commentary. At the end of your response, you will "
    "provide the command that the user must run surrounded by four `."
)


class BashBuddyDaemon:
    """Daemon that maintains Gemini client and conversation history."""

    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.client = None
        self.history = []
        self.running = False
        self.server_socket = None

    def start(self):
        """Start the daemon server."""
        load_dotenv()

        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY not found in environment")
            sys.exit(1)

        self.client = genai.Client(api_key=api_key)
        print(f"Gemini client initialized")

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
        print(f"✓ BashBuddy daemon started (socket: {self.socket_path})")
        print("Press Ctrl+C to stop")

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
                    print(f"Error accepting connection: {e}")

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
        """Process a question using the persistent Gemini client."""
        try:
            # Add to history
            self.history.append({"role": "user", "content": message})

            # Generate response using persistent client
            # Note: For now sending just the message. Full conversation history
            # support can be added later by building a proper contents array
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=message,
                config=self.generation_config,
            )

            answer = response.text

            # Add to history
            self.history.append({"role": "assistant", "content": answer})

            return {
                "status": "ok",
                "message": answer,
                "history_length": len(self.history),
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

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown."""
        print("\nShutting down daemon...")
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
