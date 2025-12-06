"""
Test suite for Git operations

Run: python tests/test_git_ops.py
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.git_ops import *
from tools.file_ops import write_file


def test_is_git_repository():
    """Test Git repository detection"""
    print("Testing is_git_repository...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Not a repository
        assert not is_git_repository(tmpdir), "Should not be a repository"

        # Initialize repository
        git_init(tmpdir)
        assert is_git_repository(tmpdir), "Should be a repository"

    print("  ✓ Repository detection working")


def test_git_init():
    """Test repository initialization"""
    print("Testing git_init...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)

        # Check .git directory exists
        git_dir = Path(tmpdir) / ".git"
        assert git_dir.exists(), "Should create .git directory"
        assert is_git_repository(tmpdir), "Should be a valid repository"

    print("  ✓ Repository initialization working")


def test_git_status():
    """Test status check"""
    print("Testing git_status...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)

        # Empty repository
        status = git_status(tmpdir)
        assert status, "Should return status"

        # Add file
        test_file = Path(tmpdir) / "test.txt"
        write_file(str(test_file), "content")

        status = git_status(tmpdir, porcelain=True)
        assert "test.txt" in status, "Should show untracked file"

    print("  ✓ Status working")


def test_git_add_and_commit():
    """Test staging and commit"""
    print("Testing git_add and git_commit...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)

        # Configure user for commits
        run_command('git config user.email "test@example.com"', cwd=tmpdir)
        run_command('git config user.name "Test User"', cwd=tmpdir)

        # Create and add file
        test_file = Path(tmpdir) / "test.txt"
        write_file(str(test_file), "content")

        git_add(["test.txt"], path=tmpdir)

        # Check staged
        status = git_status(tmpdir, porcelain=True)
        assert "test.txt" in status, "Should show staged file"

        # Commit
        commit_hash = git_commit("Initial commit", path=tmpdir)
        assert commit_hash, "Should return commit hash"
        assert len(commit_hash) == 40, "Should be full SHA hash"

    print("  ✓ Add and commit working")


def test_git_diff():
    """Test diff viewing"""
    print("Testing git_diff...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)
        run_command('git config user.email "test@example.com"', cwd=tmpdir)
        run_command('git config user.name "Test User"', cwd=tmpdir)

        # Create initial commit
        test_file = Path(tmpdir) / "test.txt"
        write_file(str(test_file), "initial content")
        git_add(["test.txt"], path=tmpdir)
        git_commit("Initial commit", path=tmpdir)

        # Modify file
        write_file(str(test_file), "modified content")

        # Check diff
        diff = git_diff(tmpdir)
        assert "modified content" in diff or "initial content" in diff, "Should show changes"

    print("  ✓ Diff working")


def test_git_log():
    """Test log viewing"""
    print("Testing git_log...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)
        run_command('git config user.email "test@example.com"', cwd=tmpdir)
        run_command('git config user.name "Test User"', cwd=tmpdir)

        # Create commits
        for i in range(3):
            test_file = Path(tmpdir) / f"file{i}.txt"
            write_file(str(test_file), f"content {i}")
            git_add([f"file{i}.txt"], path=tmpdir)
            git_commit(f"Commit {i}", path=tmpdir)

        # Get log
        log = git_log(tmpdir, max_count=5)
        assert "Commit 0" in log, "Should show first commit"
        assert "Commit 2" in log, "Should show last commit"

        # Oneline format
        log_oneline = git_log(tmpdir, max_count=5, oneline=True)
        assert len(log_oneline.split("\n")) >= 3, "Should have at least 3 lines"

    print("  ✓ Log working")


def test_git_branch():
    """Test branch operations"""
    print("Testing git_branch...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)
        run_command('git config user.email "test@example.com"', cwd=tmpdir)
        run_command('git config user.name "Test User"', cwd=tmpdir)

        # Create initial commit (required for branches)
        test_file = Path(tmpdir) / "test.txt"
        write_file(str(test_file), "content")
        git_add(["test.txt"], path=tmpdir)
        git_commit("Initial commit", path=tmpdir)

        # List branches
        branches = git_branch(tmpdir)
        assert len(branches) >= 1, "Should have at least one branch"

        # Create new branch
        git_checkout("feature", tmpdir, create=True)
        branches = git_branch(tmpdir)
        assert "feature" in branches, "Should have new branch"

    print("  ✓ Branch operations working")


def test_git_current_branch():
    """Test current branch retrieval"""
    print("Testing git_current_branch...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)
        run_command('git config user.email "test@example.com"', cwd=tmpdir)
        run_command('git config user.name "Test User"', cwd=tmpdir)

        # Create initial commit
        test_file = Path(tmpdir) / "test.txt"
        write_file(str(test_file), "content")
        git_add(["test.txt"], path=tmpdir)
        git_commit("Initial commit", path=tmpdir)

        # Get current branch (usually "main" or "master")
        current = git_current_branch(tmpdir)
        assert current, "Should have current branch"

        # Create and switch to new branch
        git_checkout("test-branch", tmpdir, create=True)
        current = git_current_branch(tmpdir)
        assert current == "test-branch", "Should be on new branch"

    print("  ✓ Current branch working")


def test_git_add_all():
    """Test adding all files"""
    print("Testing git_add with all_files...")

    with tempfile.TemporaryDirectory() as tmpdir:
        git_init(tmpdir)

        # Create multiple files
        for i in range(3):
            write_file(str(Path(tmpdir) / f"file{i}.txt"), f"content {i}")

        # Add all
        git_add([], path=tmpdir, all_files=True)

        # Check status
        status = git_status(tmpdir, porcelain=True)
        assert "file0.txt" in status, "Should stage first file"
        assert "file2.txt" in status, "Should stage last file"

    print("  ✓ Add all files working")


def test_error_handling():
    """Test error cases"""
    print("Testing error handling...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Operations on non-repository
        try:
            git_status(tmpdir)
            assert False, "Should raise GitNotRepositoryError"
        except GitNotRepositoryError:
            pass

        try:
            git_add(["test.txt"], path=tmpdir)
            assert False, "Should raise GitNotRepositoryError"
        except GitNotRepositoryError:
            pass

        try:
            git_commit("message", path=tmpdir)
            assert False, "Should raise GitNotRepositoryError"
        except GitNotRepositoryError:
            pass

    print("  ✓ Error handling working")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing Git Operations")
    print("=" * 60)

    test_is_git_repository()
    test_git_init()
    test_git_status()
    test_git_add_and_commit()
    test_git_diff()
    test_git_log()
    test_git_branch()
    test_git_current_branch()
    test_git_add_all()
    test_error_handling()

    print("=" * 60)
    print("All Git operation tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
