"""
Test suite for shell operations

Run: python tests/test_shell.py
"""

import sys
from pathlib import Path
import tempfile
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.shell import *


def test_execute_command():
    """Test basic command execution"""
    print("Testing execute_command...")

    # Simple command
    result = execute_command("echo 'Hello World'")
    assert result.success, "Command should succeed"
    assert "Hello World" in result.stdout, "Should capture stdout"
    assert result.returncode == 0, "Return code should be 0"

    # Command with exit code
    result = execute_command("exit 42")
    assert not result.success, "Command should fail"
    assert result.returncode == 42, "Return code should be 42"

    print("  ✓ Execute command working")


def test_working_directory():
    """Test working directory"""
    print("Testing working directory...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file in tmpdir
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Run command in tmpdir
        result = execute_command("ls test.txt", cwd=tmpdir)
        assert result.success, "Should find file in working directory"
        assert "test.txt" in result.stdout, "Should list test file"

    print("  ✓ Working directory working")


def test_environment_variables():
    """Test environment variable passing"""
    print("Testing environment variables...")

    # Pass custom environment variable
    result = execute_command(
        "echo $TEST_VAR",
        env={"TEST_VAR": "custom_value"}
    )
    assert result.success, "Command should succeed"
    assert "custom_value" in result.stdout, "Should use custom env var"

    print("  ✓ Environment variables working")


def test_timeout():
    """Test command timeout"""
    print("Testing timeout...")

    # Command that sleeps longer than timeout
    try:
        result = execute_command("sleep 10", timeout=1)
        assert False, "Should raise CommandTimeoutError"
    except CommandTimeoutError:
        pass

    print("  ✓ Timeout working")


def test_run_command():
    """Test run_command with check"""
    print("Testing run_command...")

    # Successful command
    result = run_command("echo 'test'", check=True)
    assert result.success, "Should succeed"

    # Failed command with check
    try:
        result = run_command("exit 1", check=True)
        assert False, "Should raise CommandExecutionError"
    except CommandExecutionError:
        pass

    print("  ✓ Run command working")


def test_run_commands():
    """Test running multiple commands"""
    print("Testing run_commands...")

    commands = [
        "echo 'first'",
        "echo 'second'",
        "echo 'third'"
    ]

    results = run_commands(commands)
    assert len(results) == 3, "Should execute all commands"
    assert all(r.success for r in results), "All should succeed"

    # Test stop on error
    commands_with_error = [
        "echo 'first'",
        "exit 1",
        "echo 'third'"
    ]

    results = run_commands(commands_with_error, stop_on_error=True)
    assert len(results) == 2, "Should stop on error"
    assert results[0].success, "First should succeed"
    assert not results[1].success, "Second should fail"

    print("  ✓ Run commands working")


def test_background_process():
    """Test background process management"""
    print("Testing background process...")

    # Start background process
    process = BackgroundProcess("sleep 2")
    assert process.start(), "Should start successfully"
    assert process.is_running(), "Should be running"

    # Check status
    status = process.get_status()
    assert status["running"], "Status should show running"
    assert status["pid"] is not None, "Should have PID"

    # Kill process
    assert process.kill(), "Should kill successfully"
    assert not process.is_running(), "Should not be running"

    print("  ✓ Background process working")


def test_background_process_output():
    """Test background process output capture"""
    print("Testing background process output...")

    # Start process that produces output
    process = BackgroundProcess("echo 'background output'")
    process.start()

    # Wait for completion and get output
    result = process.get_output(timeout=5)
    assert result.success, "Should complete successfully"
    assert "background output" in result.stdout, "Should capture output"

    print("  ✓ Background process output working")


def test_background_process_terminate():
    """Test graceful termination"""
    print("Testing background process termination...")

    process = BackgroundProcess("sleep 10")
    process.start()

    assert process.is_running(), "Should be running"
    assert process.terminate(), "Should terminate successfully"
    assert not process.is_running(), "Should not be running"

    print("  ✓ Background process termination working")


def test_stdout_stderr_separation():
    """Test stdout and stderr separation"""
    print("Testing stdout/stderr separation...")

    # Command with both stdout and stderr
    result = execute_command("echo 'output' && echo 'error' >&2")
    assert result.success, "Should succeed"
    assert "output" in result.stdout, "Should capture stdout"
    assert "error" in result.stderr, "Should capture stderr"

    print("  ✓ Stdout/stderr separation working")


def test_error_handling():
    """Test error cases"""
    print("Testing error handling...")

    # Non-existent working directory
    try:
        execute_command("echo 'test'", cwd="/nonexistent/path")
        assert False, "Should raise ShellError"
    except ShellError:
        pass

    # Invalid command (shell executes and returns non-zero exit code)
    result = execute_command("nonexistent_command_xyz123")
    assert not result.success, "Should fail with non-zero exit code"
    assert result.returncode != 0, "Should have non-zero return code"

    print("  ✓ Error handling working")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing Shell Operations")
    print("=" * 60)

    test_execute_command()
    test_working_directory()
    test_environment_variables()
    test_timeout()
    test_run_command()
    test_run_commands()
    test_background_process()
    test_background_process_output()
    test_background_process_terminate()
    test_stdout_stderr_separation()
    test_error_handling()

    print("=" * 60)
    print("All shell operation tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
