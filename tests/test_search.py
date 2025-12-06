"""
Test suite for search operations

Run: python tests/test_search.py
"""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.file_ops import write_file
from tools.search import *


def setup_test_files(tmpdir):
    """Create test file structure"""
    # Python files
    write_file(str(Path(tmpdir) / "file1.py"), "def hello():\n    print('hello')\n")
    write_file(str(Path(tmpdir) / "file2.py"), "class MyClass:\n    pass\n")

    # JavaScript files
    write_file(str(Path(tmpdir) / "script.js"), "function test() {\n    return true;\n}\n")

    # Text files
    write_file(str(Path(tmpdir) / "readme.txt"), "This is a README file\n")
    write_file(str(Path(tmpdir) / "data.txt"), "Some data here\n")

    # Subdirectory
    subdir = Path(tmpdir) / "subdir"
    write_file(str(subdir / "nested.py"), "def nested():\n    pass\n", create_dirs=True)


def test_glob_files():
    """Test glob file search"""
    print("Testing glob_files...")

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_test_files(tmpdir)

        # Find all Python files
        py_files = glob_files("*.py", tmpdir)
        assert len(py_files) >= 2, "Should find Python files"

        # Find all JavaScript files
        js_files = glob_files("*.js", tmpdir)
        assert len(js_files) == 1, "Should find one JS file"

        # Find all files
        all_files = glob_files("*", tmpdir)
        assert len(all_files) >= 5, "Should find all files"

        print("  ✓ Glob files working")


def test_grep_content():
    """Test content search"""
    print("Testing grep_content...")

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_test_files(tmpdir)

        # Search for "def"
        results = grep_content("def", tmpdir, "*.py", output_mode="files_with_matches")
        assert len(results["files_with_matches"]) >= 1, "Should find files with 'def'"
        assert results["matches_found"] > 0, "Should have matches"

        # Search for "class"
        results = grep_content("class", tmpdir, "*.py")
        assert len(results["files_with_matches"]) >= 1, "Should find files with 'class'"

        # Case insensitive search
        results = grep_content("HELLO", tmpdir, "*.py", case_sensitive=False)
        assert len(results["files_with_matches"]) >= 1, "Should find case-insensitive match"

        # Content mode with context
        results = grep_content("def", tmpdir, "*.py", output_mode="content", context_lines=1)
        assert len(results["content_matches"]) > 0, "Should have content matches"

        print("  ✓ Grep content working")


def test_list_directory():
    """Test directory listing"""
    print("Testing list_directory...")

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_test_files(tmpdir)

        # List all items
        items = list_directory(tmpdir)
        assert len(items) > 0, "Should list items"

        # List only files
        files = list_directory(tmpdir, files_only=True)
        assert all(item["is_file"] for item in files), "Should only list files"

        # List only directories
        dirs = list_directory(tmpdir, dirs_only=True)
        assert all(item["is_dir"] for item in dirs), "Should only list directories"

        # Check item structure
        if items:
            item = items[0]
            assert "name" in item, "Should have name"
            assert "path" in item, "Should have path"
            assert "is_file" in item, "Should have is_file"
            assert "is_dir" in item, "Should have is_dir"
            assert "size" in item, "Should have size"
            assert "modified" in item, "Should have modified"

        print("  ✓ List directory working")


def test_find_files_by_content():
    """Test finding files by content"""
    print("Testing find_files_by_content...")

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_test_files(tmpdir)

        # Find files containing "def"
        files = find_files_by_content("def", tmpdir, ".py")
        assert len(files) >= 1, "Should find files with 'def'"

        # Find files containing "class"
        files = find_files_by_content("class", tmpdir, ".py")
        assert len(files) >= 1, "Should find files with 'class'"

        # Case insensitive
        files = find_files_by_content("HELLO", tmpdir, ".py", case_sensitive=False)
        assert len(files) >= 1, "Should find case-insensitive match"

        print("  ✓ Find files by content working")


def test_error_handling():
    """Test error cases"""
    print("Testing error handling...")

    # Non-existent path
    try:
        glob_files("*.py", "/nonexistent/path")
        assert False, "Should raise SearchError"
    except SearchError:
        pass

    # Non-existent path for grep
    try:
        grep_content("test", "/nonexistent/path")
        assert False, "Should raise SearchError"
    except SearchError:
        pass

    # Non-existent directory for list
    try:
        list_directory("/nonexistent/path")
        assert False, "Should raise SearchError"
    except SearchError:
        pass

    print("  ✓ Error handling working")


def test_max_results():
    """Test max results limit"""
    print("Testing max results...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple files with matches
        for i in range(10):
            write_file(str(Path(tmpdir) / f"file{i}.txt"), f"test content {i}\n")

        # Limit results
        results = grep_content("test", tmpdir, "*.txt", max_results=3)
        assert len(results["files_with_matches"]) == 3, "Should respect max_results"

        print("  ✓ Max results working")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing Search Operations")
    print("=" * 60)

    test_glob_files()
    test_grep_content()
    test_list_directory()
    test_find_files_by_content()
    test_error_handling()
    test_max_results()

    print("=" * 60)
    print("All search operation tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
