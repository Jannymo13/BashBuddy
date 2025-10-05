"""Entry point for running the daemon."""

import sys
from pathlib import Path

# Add parent directory to path if needed
parent_dir = Path(__file__).parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from bashbuddy.daemon.server import BashBuddyDaemon
from bashbuddy.daemon.client import get_socket_path


def main():
    """Start the daemon."""
    socket_path = get_socket_path()
    daemon = BashBuddyDaemon(socket_path)
    daemon.start()


if __name__ == "__main__":
    main()
