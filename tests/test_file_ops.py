"""
Test suite for file operations

Run: python tests/test_file_ops.py
"""

import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.file_ops import *


def test_write_and_read():
    """Test writing and reading files"""
    print("Testing write_file and read_file...")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"

        # Write file
        write_file(str(file_path), content)
        assert file_path.exists(), "File should exist after write"

        # Read full file
        read_content = read_file(str(file_path))
        assert read_content == content, "Content should match"

        # Read with offset
        offset_content = read_file(str(file_path), offset=2)
        assert offset_content.startswith("Line 3"), "Offset should work"

        # Read with limit
        limit_content = read_file(str(file_path), limit=2)
        assert limit_content.count('\n') == 2, "Limit should work"
        assert limit_content == "Line 1\nLine 2\n", "Should read exactly 2 lines"

        print("  ✓ Write and read working")


def test_edit_file():
    """Test file editing"""
    print("Testing edit_file...")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "Hello World\nHello Python\nHello World"

        write_file(str(file_path), content)

        # Replace first occurrence
        edit_file(str(file_path), "World", "Universe")
        edited = read_file(str(file_path))
        assert "Universe" in edited, "Edit should replace text"
        assert edited.count("World") == 1, "Should replace only first occurrence"

        # Replace all occurrences
        edit_file(str(file_path), "World", "Galaxy", replace_all=True)
        edited = read_file(str(file_path))
        assert "World" not in edited, "All occurrences should be replaced"
        assert edited.count("Galaxy") == 1, "All should be replaced"

        print("  ✓ Edit working")


def test_file_exists():
    """Test file existence check"""
    print("Testing file_exists...")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        # Non-existent file
        assert not file_exists(str(file_path)), "Should return False for non-existent"

        # Create file
        write_file(str(file_path), "content")
        assert file_exists(str(file_path)), "Should return True for existing file"

        print("  ✓ File exists check working")


def test_get_file_info():
    """Test file metadata"""
    print("Testing get_file_info...")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "Test content"

        write_file(str(file_path), content)
        info = get_file_info(str(file_path))

        assert info["name"] == "test.txt", "Name should match"
        assert info["size"] == len(content), "Size should match"
        assert info["is_file"], "Should be a file"
        assert not info["is_dir"], "Should not be a directory"
        assert info["readable"], "Should be readable"
        assert info["writable"], "Should be writable"

        print("  ✓ File info working")


def test_delete_file():
    """Test file deletion"""
    print("Testing delete_file...")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        write_file(str(file_path), "content")
        assert file_path.exists(), "File should exist"

        delete_file(str(file_path))
        assert not file_path.exists(), "File should be deleted"

        print("  ✓ Delete working")


def test_copy_file():
    """Test file copying"""
    print("Testing copy_file...")

    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source.txt"
        dst = Path(tmpdir) / "destination.txt"
        content = "Test content"

        write_file(str(src), content)
        copy_file(str(src), str(dst))

        assert dst.exists(), "Destination should exist"
        assert read_file(str(dst)) == content, "Content should match"

        print("  ✓ Copy working")


def test_create_directories():
    """Test automatic directory creation"""
    print("Testing automatic directory creation...")

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "subdir1" / "subdir2" / "test.txt"

        write_file(str(file_path), "content", create_dirs=True)
        assert file_path.exists(), "File should be created with directories"
        assert file_path.parent.parent.name == "subdir1", "Nested dirs should exist"

        print("  ✓ Directory creation working")


def test_error_handling():
    """Test error cases"""
    print("Testing error handling...")

    # Read non-existent file
    try:
        read_file("/nonexistent/file.txt")
        assert False, "Should raise FileNotFoundError"
    except FileNotFoundError:
        pass

    # Edit non-existent file
    try:
        edit_file("/nonexistent/file.txt", "old", "new")
        assert False, "Should raise FileNotFoundError"
    except FileNotFoundError:
        pass

    # Edit with non-matching string
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        write_file(str(file_path), "content")

        try:
            edit_file(str(file_path), "notfound", "new")
            assert False, "Should raise FileOperationError"
        except FileOperationError:
            pass

    print("  ✓ Error handling working")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing File Operations")
    print("=" * 60)

    test_write_and_read()
    test_edit_file()
    test_file_exists()
    test_get_file_info()
    test_delete_file()
    test_copy_file()
    test_create_directories()
    test_error_handling()

    print("=" * 60)
    print("All file operation tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
