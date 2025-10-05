"""Client functions for communicating with the BashBuddy daemon."""

import os
import json
import socket
from pathlib import Path


def get_socket_path():
    """Get the path to the Unix socket."""
    runtime_dir = Path.home() / ".bashbuddy"
    runtime_dir.mkdir(exist_ok=True)
    return str(runtime_dir / "daemon.sock")


def get_pid_file():
    """Get the path to the PID file."""
    runtime_dir = Path.home() / ".bashbuddy"
    runtime_dir.mkdir(exist_ok=True)
    return str(runtime_dir / "daemon.pid")


def is_daemon_running():
    """Check if the daemon is running."""
    pid_file = get_pid_file()
    
    if not os.path.exists(pid_file):
        return False
        
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
            
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (OSError, ValueError, ProcessLookupError):
        # Clean up stale PID file
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return False


def send_command(command: str, **kwargs):
    """Send a command to the daemon and return the response."""
    socket_path = get_socket_path()
    
    if not os.path.exists(socket_path):
        return {"status": "error", "message": "Daemon not running. Start it with: bashbuddy start"}
        
    try:
        # Create socket and connect
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.settimeout(60)  # 60 second timeout (increased for API rate limits)
        client_socket.connect(socket_path)
        
        # Prepare request
        request = {"command": command, **kwargs}
        request_data = json.dumps(request).encode('utf-8') + b"\n\n"
        
        # Send request
        client_socket.sendall(request_data)
        
        # Receive response
        data = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n\n" in data:
                break
                
        client_socket.close()
        
        # Parse response
        if not data:
            return {"status": "error", "message": "Daemon closed connection (possibly crashed). Try: bb stop && bb start"}
        
        response = json.loads(data.decode('utf-8').strip())
        return response
        
    except socket.timeout:
        return {"status": "error", "message": "Request timed out (API may be slow or rate limited)"}
    except ConnectionRefusedError:
        return {"status": "error", "message": "Could not connect to daemon"}
    except BrokenPipeError:
        return {"status": "error", "message": "Connection broken (daemon may have crashed). Try restarting: bb stop && bb start"}
    except Exception as e:
        return {"status": "error", "message": f"Communication error: {str(e)}"}
