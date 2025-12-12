"""
Code search and navigation tools

Provides tools for searching code, finding files, and exploring codebase structure.
Uses efficient search methods including glob patterns and regex.
"""

from typing import List, Dict, Any
from pathlib import Path

from tools.tool_base import Tool, ToolMetadata, ToolParameter
from tools import search


class GrepTool(Tool):
    """
    Search for text pattern in files

    Searches file contents using regex patterns. Supports case-sensitive
    and case-insensitive searches with file pattern filtering.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="grep",
            description="Search file contents for text pattern (regex supported)",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type=str,
                    description="Regex pattern to search for",
                    required=True
                ),
                ToolParameter(
                    name="directory",
                    type=str,
                    description="Directory to search in (default: current directory)",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="file_pattern",
                    type=str,
                    description="File pattern filter (e.g., '*.py' for Python files)",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="case_sensitive",
                    type=bool,
                    description="Whether search should be case-sensitive",
                    required=False,
                    default=True
                )
            ],
            category="search"
        )

    def execute(
        self,
        pattern: str,
        directory: str = ".",
        file_pattern: str = None,
        case_sensitive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute grep search

        Args:
            pattern: Regex pattern to search
            directory: Directory to search in
            file_pattern: File filter pattern
            case_sensitive: Whether search is case-sensitive

        Returns:
            List of matches with file, line number, and content
        """
        return search.grep_content(pattern, directory, file_pattern, case_sensitive)


class FindFileTool(Tool):
    """
    Find files by name pattern

    Searches for files matching a glob pattern (e.g., '*.py', 'test_*.js').
    Supports recursive directory traversal.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="find_file",
            description="Find files by name pattern (glob patterns supported)",
            parameters=[
                ToolParameter(
                    name="name_pattern",
                    type=str,
                    description="Name pattern to match (e.g., '*.py', 'config.*')",
                    required=True
                ),
                ToolParameter(
                    name="directory",
                    type=str,
                    description="Directory to search in (default: current directory)",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="recursive",
                    type=bool,
                    description="Search in subdirectories recursively",
                    required=False,
                    default=True
                )
            ],
            category="search"
        )

    def execute(
        self,
        name_pattern: str,
        directory: str = ".",
        recursive: bool = True
    ) -> List[str]:
        """
        Execute file find operation

        Args:
            name_pattern: Glob pattern to match
            directory: Directory to search in
            recursive: Whether to search recursively

        Returns:
            List of matching file paths
        """
        return search.glob_files(name_pattern, directory, recursive)


class GetFileStructureTool(Tool):
    """
    Get directory tree structure

    Returns a tree-like visualization of the directory structure.
    Useful for understanding project layout and organization.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="get_file_structure",
            description="Get directory tree structure (tree-like visualization)",
            parameters=[
                ToolParameter(
                    name="directory",
                    type=str,
                    description="Directory to analyze (default: current directory)",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="max_depth",
                    type=int,
                    description="Maximum depth to traverse (0 for unlimited)",
                    required=False,
                    default=3
                ),
                ToolParameter(
                    name="include_hidden",
                    type=bool,
                    description="Include hidden files and directories",
                    required=False,
                    default=False
                )
            ],
            category="search"
        )

    def execute(
        self,
        directory: str = ".",
        max_depth: int = 3,
        include_hidden: bool = False
    ) -> str:
        """
        Execute directory tree generation

        Args:
            directory: Root directory
            max_depth: Maximum depth to traverse
            include_hidden: Include hidden entries

        Returns:
            Tree structure as formatted string
        """
        return self._build_tree_structure(directory, max_depth, include_hidden)

    def _build_tree_structure(
        self,
        directory: str,
        max_depth: int,
        include_hidden: bool
    ) -> str:
        """
        Build tree structure recursively

        Args:
            directory: Directory path
            max_depth: Maximum depth
            include_hidden: Include hidden files

        Returns:
            Formatted tree string
        """
        path = Path(directory)
        if not path.exists():
            return f"Directory not found: {directory}"

        lines = [str(path.absolute())]
        self._add_tree_entries(path, lines, "", max_depth, 0, include_hidden)
        return "\n".join(lines)

    def _add_tree_entries(
        self,
        path: Path,
        lines: List[str],
        prefix: str,
        max_depth: int,
        current_depth: int,
        include_hidden: bool
    ):
        """
        Recursively add tree entries

        Args:
            path: Current path
            lines: Output lines list
            prefix: Current prefix for tree drawing
            max_depth: Maximum depth
            current_depth: Current depth
            include_hidden: Include hidden entries
        """
        if max_depth > 0 and current_depth >= max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))

            if not include_hidden:
                entries = [e for e in entries if not e.name.startswith('.')]

            for index, entry in enumerate(entries):
                is_last = index == len(entries) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{entry.name}")

                if entry.is_dir():
                    extension = "    " if is_last else "│   "
                    self._add_tree_entries(
                        entry,
                        lines,
                        prefix + extension,
                        max_depth,
                        current_depth + 1,
                        include_hidden
                    )
        except PermissionError:
            pass


class CodeSearchTool(Tool):
    """
    High-performance code search

    Uses ripgrep for fast code search with context lines.
    Optimized for large codebases.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="code_search",
            description="Fast code search with ripgrep (optimized for large codebases)",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type=str,
                    description="Regex pattern to search for",
                    required=True
                ),
                ToolParameter(
                    name="directory",
                    type=str,
                    description="Directory to search in",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="file_pattern",
                    type=str,
                    description="File pattern filter",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="case_sensitive",
                    type=bool,
                    description="Case-sensitive search",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="max_results",
                    type=int,
                    description="Maximum number of results",
                    required=False,
                    default=None
                ),
                ToolParameter(
                    name="context_lines",
                    type=int,
                    description="Lines of context around matches",
                    required=False,
                    default=2
                )
            ],
            category="search"
        )

    def execute(
        self,
        pattern: str,
        directory: str = ".",
        file_pattern: str = None,
        case_sensitive: bool = True,
        max_results: int = None,
        context_lines: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Execute code search

        Args:
            pattern: Pattern to search
            directory: Search directory
            file_pattern: File filter
            case_sensitive: Case sensitivity
            max_results: Maximum results
            context_lines: Context lines

        Returns:
            List of search results with context
        """
        return search.code_search(
            pattern,
            directory,
            file_pattern,
            case_sensitive,
            max_results,
            context_lines
        )
