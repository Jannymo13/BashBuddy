#!/usr/bin/env python3
"""
Simple test script to verify BashBuddy setup without calling Gemini API.
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bashbuddy.utils import get_socket_path, get_pid_file


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        import bashbuddy
        import bashbuddy.ask
        import bashbuddy.daemon
        import bashbuddy.utils
        print("✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_dependencies():
    """Test that required dependencies are available."""
    print("\nTesting dependencies...")
    all_ok = True
    
    # Test click
    try:
        import click
        print(f"✓ click is installed")
    except ImportError:
        print(f"✗ click is NOT installed")
        all_ok = False
    
    # Test google.genai (needs special import handling)
    try:
        from google import genai
        print(f"✓ google.genai is installed")
    except ImportError:
        print(f"✗ google.genai is NOT installed")
        all_ok = False
    
    # Test python-dotenv
    try:
        import dotenv
        print(f"✓ python-dotenv is installed")
    except ImportError:
        print(f"✗ python-dotenv is NOT installed")
        all_ok = False
    
    return all_ok


def test_env_setup():
    """Test environment configuration."""
    print("\nTesting environment setup...")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"✓ GEMINI_API_KEY is set (length: {len(api_key)})")
    else:
        # Check for .env file
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            print("○ GEMINI_API_KEY not in environment, but .env file exists")
        else:
            print("⚠ GEMINI_API_KEY not set and no .env file found")
            print("  The daemon will fail to start without an API key")
    
    return True


def test_filesystem():
    """Test filesystem paths."""
    print("\nTesting filesystem setup...")
    
    socket_path = get_socket_path()
    pid_file = get_pid_file()
    
    socket_dir = Path(socket_path).parent
    
    print(f"Socket path: {socket_path}")
    print(f"PID file: {pid_file}")
    
    if not socket_dir.exists():
        print(f"Creating directory: {socket_dir}")
        socket_dir.mkdir(parents=True, exist_ok=True)
    
    if socket_dir.exists():
        print(f"✓ Runtime directory exists: {socket_dir}")
        
        # Test write permissions
        test_file = socket_dir / ".test"
        try:
            test_file.touch()
            test_file.unlink()
            print("✓ Directory is writable")
        except Exception as e:
            print(f"✗ Directory not writable: {e}")
            return False
    else:
        print(f"✗ Could not create directory: {socket_dir}")
        return False
    
    return True


def test_cli_entry_point():
    """Test that CLI entry point is configured."""
    print("\nTesting CLI entry point...")
    
    from bashbuddy import cli
    
    if cli:
        print("✓ CLI entry point is configured")
        
        # List commands
        commands = list(cli.commands.keys())
        print(f"  Available commands: {', '.join(commands)}")
        
        expected_commands = ['start', 'stop', 'status', 'reset', 'history', 'ask']
        missing = set(expected_commands) - set(commands)
        
        if missing:
            print(f"⚠ Missing commands: {', '.join(missing)}")
        else:
            print("✓ All expected commands are registered")
        
        return True
    else:
        print("✗ CLI entry point not found")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("BashBuddy Setup Verification")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_dependencies,
        test_env_setup,
        test_filesystem,
        test_cli_entry_point,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! BashBuddy is ready to use.")
        print("\nNext steps:")
        print("1. Make sure GEMINI_API_KEY is set")
        print("2. Just run: bb ask 'your question'")
        print("   (daemon will start automatically!)")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
