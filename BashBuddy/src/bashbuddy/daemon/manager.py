"""Daemon lifecycle management functions."""

import os
import subprocess
import signal
import time
import sys
from bashbuddy.daemon.client import get_pid_file, is_daemon_running, send_command, get_socket_path


def start_daemon():
    """Start the daemon process."""
    if is_daemon_running():
        return {"status": "error", "message": "Daemon is already running"}
        
    # Start daemon as background process
    try:
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
