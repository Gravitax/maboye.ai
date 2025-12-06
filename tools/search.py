"""
Search operations for agent system

Provides file search (glob) and content search (grep) capabilities.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
import glob as glob_module

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.logger import logger


class SearchError(Exception):
    """Base exception for search errors"""
    pass


def glob_files(
    pattern: str,
    path: str = ".",
    recursive: bool = True
) -> List[str]:
    """
    Find files matching pattern

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.js")
        path: Directory to search in
        recursive: Enable recursive search

    Returns:
        List of matching file paths
    """
    base_path = Path(path).resolve()

    if not base_path.exists():
        logger.error("SEARCH", "Path not found", {"path": str(base_path)})
        raise SearchError(f"Path not found: {path}")

    try:
        # Build full pattern
        if recursive and '**' not in pattern:
            full_pattern = str(base_path / '**' / pattern)
        else:
            full_pattern = str(base_path / pattern)

        # Search for files
        matches = glob_module.glob(full_pattern, recursive=recursive)

        # Filter to files only (not directories)
        files = [f for f in matches if Path(f).is_file()]

        # Sort by modification time (most recent first)
        files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)

        logger.info("SEARCH", "Glob search completed", {
            "pattern": pattern,
            "path": str(base_path),
            "matches": len(files)
        })

        return files

    except Exception as e:
        logger.error("SEARCH", "Glob search failed", {
            "pattern": pattern,
            "path": str(base_path),
            "error": str(e)
        })
        raise SearchError(f"Glob search failed: {e}")


def grep_content(
    pattern: str,
    path: str = ".",
    file_pattern: Optional[str] = None,
    case_sensitive: bool = True,
    output_mode: str = "files_with_matches",
    context_lines: int = 0,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    Search file contents for pattern

    Args:
        pattern: Regex pattern to search for
        path: Directory to search in
        file_pattern: Glob pattern for files to search (e.g., "*.py")
        case_sensitive: Case-sensitive search
        output_mode: "files_with_matches", "content", or "count"
        context_lines: Lines of context around matches
        max_results: Maximum number of results

    Returns:
        Dictionary with search results
    """
    base_path = Path(path).resolve()

    if not base_path.exists():
        logger.error("SEARCH", "Path not found", {"path": str(base_path)})
        raise SearchError(f"Path not found: {path}")

    try:
        # Compile regex
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)

        # Get files to search
        if file_pattern:
            files = glob_files(file_pattern, str(base_path))
        else:
            files = glob_files("*", str(base_path))

        results = {
            "pattern": pattern,
            "files_searched": 0,
            "matches_found": 0,
            "files_with_matches": [],
            "content_matches": [],
            "match_counts": {}
        }

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                results["files_searched"] += 1
                file_matches = []
                match_count = 0

                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        match_count += 1
                        results["matches_found"] += 1

                        if output_mode == "content":
                            # Include context lines
                            start = max(0, line_num - context_lines - 1)
                            end = min(len(lines), line_num + context_lines)
                            context = lines[start:end]

                            file_matches.append({
                                "line_number": line_num,
                                "line": line.rstrip(),
                                "context": [l.rstrip() for l in context]
                            })

                if match_count > 0:
                    results["files_with_matches"].append(file_path)
                    results["match_counts"][file_path] = match_count

                    if output_mode == "content":
                        results["content_matches"].append({
                            "file": file_path,
                            "matches": file_matches
                        })

                # Stop if max results reached
                if max_results and len(results["files_with_matches"]) >= max_results:
                    break

            except UnicodeDecodeError:
                # Skip binary files
                continue
            except Exception as e:
                logger.warning("SEARCH", "Failed to search file", {
                    "file": file_path,
                    "error": str(e)
                })
                continue

        logger.info("SEARCH", "Grep search completed", {
            "pattern": pattern,
            "files_searched": results["files_searched"],
            "matches_found": results["matches_found"]
        })

        return results

    except Exception as e:
        logger.error("SEARCH", "Grep search failed", {
            "pattern": pattern,
            "path": str(base_path),
            "error": str(e)
        })
        raise SearchError(f"Grep search failed: {e}")


def list_directory(
    path: str = ".",
    include_hidden: bool = False,
    files_only: bool = False,
    dirs_only: bool = False
) -> List[Dict[str, Any]]:
    """
    List directory contents

    Args:
        path: Directory path
        include_hidden: Include hidden files (starting with .)
        files_only: List only files
        dirs_only: List only directories

    Returns:
        List of dictionaries with file/directory information
    """
    dir_path = Path(path).resolve()

    if not dir_path.exists():
        logger.error("SEARCH", "Directory not found", {"path": str(dir_path)})
        raise SearchError(f"Directory not found: {path}")

    if not dir_path.is_dir():
        logger.error("SEARCH", "Not a directory", {"path": str(dir_path)})
        raise SearchError(f"Not a directory: {path}")

    try:
        items = []

        for item in dir_path.iterdir():
            # Skip hidden files if requested
            if not include_hidden and item.name.startswith('.'):
                continue

            # Apply filters
            if files_only and not item.is_file():
                continue
            if dirs_only and not item.is_dir():
                continue

            stat = item.stat()

            items.append({
                "name": item.name,
                "path": str(item),
                "is_file": item.is_file(),
                "is_dir": item.is_dir(),
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime
            })

        # Sort: directories first, then by name
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        logger.debug("SEARCH", "Directory listed", {
            "path": str(dir_path),
            "items": len(items)
        })

        return items

    except Exception as e:
        logger.error("SEARCH", "List directory failed", {
            "path": str(dir_path),
            "error": str(e)
        })
        raise SearchError(f"Failed to list directory: {e}")


def find_files_by_content(
    search_text: str,
    path: str = ".",
    file_extension: Optional[str] = None,
    case_sensitive: bool = False
) -> List[str]:
    """
    Find files containing specific text

    Args:
        search_text: Text to search for
        path: Directory to search in
        file_extension: Filter by extension (e.g., ".py")
        case_sensitive: Case-sensitive search

    Returns:
        List of file paths containing the text
    """
    pattern = re.escape(search_text)
    file_pattern = f"*{file_extension}" if file_extension else "*"

    results = grep_content(
        pattern=pattern,
        path=path,
        file_pattern=file_pattern,
        case_sensitive=case_sensitive,
        output_mode="files_with_matches"
    )

    return results["files_with_matches"]
