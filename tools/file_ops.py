"""
File operations for agent system

Provides basic file operations: read, write, edit, and metadata.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import os

from core.logger import logger


class FileOperationError(Exception):
    """Base exception for file operation errors"""
    pass


class FileNotFoundError(FileOperationError):
    """File not found error"""
    pass


class FilePermissionError(FileOperationError):
    """Permission denied error"""
    pass


def read_file(
    file_path: str,
    offset: int = 0,
    limit: Optional[int] = None
) -> str:
    """
    Read file contents with optional line range

    Args:
        file_path: Path to file
        offset: Line number to start from (0-indexed)
        limit: Maximum number of lines to read

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: File does not exist
        FilePermissionError: No read permission
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise FileOperationError(f"Not a file: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Apply offset and limit
        if offset > 0:
            lines = lines[offset:]

        if limit is not None and limit > 0:
            lines = lines[:limit]

        content = ''.join(lines)
        return content

    except PermissionError:
        raise FilePermissionError(f"Permission denied: {file_path}")

    except UnicodeDecodeError as e:
        raise FileOperationError(f"Cannot decode file: {file_path}")


def write_file(
    file_path: str,
    content: str,
    create_dirs: bool = True
) -> bool:
    """
    Write content to file (creates or overwrites)

    Args:
        file_path: Path to file
        content: Content to write
        create_dirs: Create parent directories if needed

    Returns:
        True if successful

    Raises:
        FilePermissionError: No write permission
        FileOperationError: Write failed
    """
    path = Path(file_path)

    try:
        # Create parent directories if needed
        if create_dirs and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        # Write file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    except PermissionError:
        raise FilePermissionError(f"Permission denied: {file_path}")

    except Exception as e:
        raise FileOperationError(f"Failed to write file: {e}")


def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False
) -> bool:
    """
    Edit file by replacing text

    Args:
        file_path: Path to file
        old_string: Text to find
        new_string: Text to replace with
        replace_all: Replace all occurrences (default: first only)

    Returns:
        True if replacement made

    Raises:
        FileNotFoundError: File does not exist
        FileOperationError: String not found or edit failed
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # Read current content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if old_string exists
        if old_string not in content:
            raise FileOperationError(f"String not found in file: {file_path}")

        # Replace
        if replace_all:
            new_content = content.replace(old_string, new_string)
            count = content.count(old_string)
        else:
            new_content = content.replace(old_string, new_string, 1)
            count = 1

        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True

    except FileOperationError:
        raise

    except Exception as e:
        raise FileOperationError(f"Failed to edit file: {e}")


def file_exists(file_path: str) -> bool:
    """
    Check if file exists

    Args:
        file_path: Path to check

    Returns:
        True if file exists and is a file
    """
    path = Path(file_path)
    exists = path.exists() and path.is_file()
    return exists


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get file metadata

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information

    Raises:
        FileNotFoundError: File does not exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        stat = path.stat()

        info = {
            "path": str(path.absolute()),
            "name": path.name,
            "size": stat.st_size,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
            "executable": os.access(path, os.X_OK)
        }
        return info

    except Exception as e:
        raise FileOperationError(f"Failed to get file info: {e}")


def delete_file(file_path: str) -> bool:
    """
    Delete file

    Args:
        file_path: Path to file

    Returns:
        True if deleted

    Raises:
        FileNotFoundError: File does not exist
        FilePermissionError: No delete permission
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        path.unlink()
        return True

    except PermissionError:
        raise FilePermissionError(f"Permission denied: {file_path}")

    except Exception as e:
        raise FileOperationError(f"Failed to delete file: {e}")


def copy_file(source: str, destination: str) -> bool:
    """
    Copy file

    Args:
        source: Source file path
        destination: Destination file path

    Returns:
        True if copied

    Raises:
        FileNotFoundError: Source does not exist
        FileOperationError: Copy failed
    """
    import shutil

    src_path = Path(source)
    dst_path = Path(destination)

    if not src_path.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    try:
        shutil.copy2(src_path, dst_path)
        return True

    except Exception as e:
        raise FileOperationError(f"Failed to copy file: {e}")
