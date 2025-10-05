"""Utility functions for daemon communication and management."""
import os
import json
import socket
import subprocess
import signal
import time
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


def start_daemon():
    """Start the daemon process."""
    if is_daemon_running():
        return {"status": "error", "message": "Daemon is already running"}
        
    # Start daemon as background process
    try:
        import sys
        python_exe = sys.executable
        
        # Get the daemon module path (use __main__.py)
        daemon_module = "bashbuddy.daemon"
        
        # Start daemon in background
        process = subprocess.Popen(
            [python_exe, "-m", daemon_module],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Save PID
        pid_file = get_pid_file()
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))
            
        # Wait for daemon to initialize and become responsive
        # The daemon needs time to: load env, create socket, init Gemini client
        max_retries = 10
        retry_delay = 0.3
        
        for attempt in range(max_retries):
            time.sleep(retry_delay)
            
            # Check if process is still running
            if not is_daemon_running():
                break
            
            # Try to connect
            response = send_command("ping")
            if response.get("status") == "ok":
                return {"status": "ok", "message": "Daemon started successfully", "pid": process.pid}
        
        # If we got here, daemon didn't become responsive in time
        if is_daemon_running():
            return {"status": "error", "message": "Daemon started but not responding (timeout)"}
        else:
            # Get error output
            try:
                _, stderr = process.communicate(timeout=1)
                error_msg = stderr.decode('utf-8')
            except:
                error_msg = "Unknown error"
            return {"status": "error", "message": f"Failed to start daemon: {error_msg}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Failed to start daemon: {str(e)}"}


def stop_daemon():
    """Stop the daemon process."""
    if not is_daemon_running():
        return {"status": "error", "message": "Daemon is not running"}
        
    pid_file = get_pid_file()
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
            
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)
        
        # Wait for shutdown
        for _ in range(10):
            time.sleep(0.2)
            if not is_daemon_running():
                break
                
        # Force kill if still running
        if is_daemon_running():
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.5)
            
        # Clean up
        if os.path.exists(pid_file):
            os.remove(pid_file)
            
        socket_path = get_socket_path()
        if os.path.exists(socket_path):
            os.remove(socket_path)
            
        return {"status": "ok", "message": "Daemon stopped"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to stop daemon: {str(e)}"}


def get_daemon_status():
    """Get the status of the daemon."""
    if not is_daemon_running():
        return {
            "status": "stopped",
            "message": "Daemon is not running"
        }
        
    # Try to ping the daemon
    response = send_command("ping")
    
    if response.get("status") == "ok":
        pid_file = get_pid_file()
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
            
        return {
            "status": "running",
            "message": "Daemon is running",
            "pid": pid
        }
    else:
        return {
            "status": "error",
            "message": "Daemon process exists but not responding"
        }


def ensure_daemon_running():
    """
    Ensure the daemon is running, starting it automatically if needed.
    Returns True if daemon is running (or was successfully started), False otherwise.
    """
    # Check if already running
    if is_daemon_running():
        # Verify it's responsive
        response = send_command("ping")
        if response.get("status") == "ok":
            return True
        else:
            # Daemon exists but not responding, restart it
            stop_daemon()
            time.sleep(0.5)
    
    # Start the daemon
    result = start_daemon()
    
    # Check result - both "ok" and "already running" are fine
    if result.get("status") == "ok":
        return True
    
    # If it says already running, verify it's actually working
    if "already running" in result.get("message", "").lower():
        if is_daemon_running():
            response = send_command("ping")
            return response.get("status") == "ok"
    
    return False
