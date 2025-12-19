"""
File manipulation tools

Provides tools for reading, writing, editing, and listing files.
Each tool wraps the corresponding file operation with proper validation
and error handling.
"""

from typing import List, Dict, Any

from tools.tool_base import Tool, ToolMetadata, ToolParameter
from tools import file_ops


class ReadFileTool(Tool):
    """
    Read file contents with line numbers

    Reads a file and returns its contents with optional line range.
    Useful for viewing source code or configuration files.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="read_file",
            description="Read file contents with optional line range",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to the file to read",
                    required=True
                ),
                ToolParameter(
                    name="start_line",
                    type=int,
                    description="Line number to start reading from (0-indexed)",
                    required=False,
                    default=0
                ),
                ToolParameter(
                    name="num_lines",
                    type=int,
                    description="Maximum number of lines to read (None for all)",
                    required=False,
                    default=None
                )
            ],
            category="file_operations"
        )

    def execute(
        self,
        file_path: str,
        start_line: int = 0,
        num_lines: int = None
    ) -> str:
        """
        Execute file read operation

        Args:
            file_path: Path to file
            start_line: Starting line (0-indexed)
            num_lines: Number of lines to read

        Returns:
            File contents as string
        """
        return file_ops.read_file(file_path, start_line, num_lines)


class WriteFileTool(Tool):
    """
    Write or create new file

    Creates a new file or overwrites an existing file with the given content.
    Can optionally create parent directories if they don't exist.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="write_file",
            description="Write content to file (creates or overwrites)",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to the file to write",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type=str,
                    description="Content to write to the file",
                    required=True
                ),
                ToolParameter(
                    name="create_dirs",
                    type=bool,
                    description="Create parent directories if they don't exist",
                    required=False,
                    default=True
                )
            ],
            category="file_operations",
            dangerous=True
        )

    def execute(
        self,
        file_path: str,
        content: str,
        create_dirs: bool = True
    ) -> str:
        """
        Execute file write operation

        Args:
            file_path: Path to file
            content: Content to write
            create_dirs: Whether to create parent directories

        Returns:
            A string indicating successful write operation.
        """
        file_ops.write_file(file_path, content, create_dirs)
        return f"Successfully wrote to {file_path}"


class EditFileTool(Tool):
    """
    Edit file with find and replace

    Finds exact text match in a file and replaces it with new text.
    Can replace first occurrence or all occurrences.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="edit_file",
            description="Edit file by finding and replacing exact text match",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to the file to edit",
                    required=True
                ),
                ToolParameter(
                    name="old_text",
                    type=str,
                    description="Exact text to find (must match exactly)",
                    required=True
                ),
                ToolParameter(
                    name="new_text",
                    type=str,
                    description="Text to replace with",
                    required=True
                ),
                ToolParameter(
                    name="replace_all",
                    type=bool,
                    description="Replace all occurrences (default: first only)",
                    required=False,
                    default=False
                )
            ],
            category="file_operations",
            dangerous=True
        )

    def execute(
        self,
        file_path: str,
        old_text: str,
        new_text: str,
        replace_all: bool = False
    ) -> bool:
        """
        Execute file edit operation

        Args:
            file_path: Path to file
            old_text: Text to find
            new_text: Text to replace with
            replace_all: Whether to replace all occurrences

        Returns:
            True if replacement was made
        """
        return file_ops.edit_file(file_path, old_text, new_text, replace_all)


class ListFilesTool(Tool):
    """
    List files in directory

    Lists all files and directories in the specified path with optional
    filtering for files-only or directories-only.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="list_files",
            description="List files and directories with optional filtering",
            parameters=[
                ToolParameter(
                    name="directory",
                    type=str,
                    description="Directory path to list (default: current directory)",
                    required=False,
                    default="."
                ),
                ToolParameter(
                    name="include_hidden",
                    type=bool,
                    description="Include hidden files (starting with .)",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="files_only",
                    type=bool,
                    description="Show only files (exclude directories)",
                    required=False,
                    default=False
                ),
                ToolParameter(
                    name="dirs_only",
                    type=bool,
                    description="Show only directories (exclude files)",
                    required=False,
                    default=False
                )
            ],
            category="file_operations"
        )

    def execute(
        self,
        directory: str = ".",
        include_hidden: bool = False,
        files_only: bool = False,
        dirs_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute directory listing

        Args:
            directory: Path to directory
            include_hidden: Include hidden files
            files_only: Only list files
            dirs_only: Only list directories

        Returns:
            List of entries with metadata
        """
        from .. import search
        return search.list_directory(directory, include_hidden, files_only, dirs_only)


class FileInfoTool(Tool):
    """
    Get file metadata

    Retrieves detailed information about a file including size,
    permissions, and timestamps.
    """

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="file_info",
            description="Get detailed file metadata (size, permissions, timestamps)",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=str,
                    description="Path to the file",
                    required=True
                )
            ],
            category="file_operations"
        )

    def execute(self, file_path: str) -> Dict[str, Any]:
        """
        Execute file info retrieval

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        return file_ops.get_file_info(file_path)


class MoveFileTool(Tool):
    """Tool for moving or renaming files/directories"""
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="move_path",
            description="Move or rename a file or directory",
            parameters=[
                ToolParameter(name="src", type=str, description="Source path", required=True),
                ToolParameter(name="dst", type=str, description="Destination path", required=True)
            ],
            category="file_operations",
            dangerous=True
        )

    def execute(self, src: str, dst: str) -> str:
        return file_ops.move_path(src, dst)


class DeleteFileTool(Tool):
    """Tool for deleting files/directories"""
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="delete_path",
            description="Delete a file or directory",
            parameters=[
                ToolParameter(name="path", type=str, description="Path to delete", required=True),
                ToolParameter(name="force", type=bool, description="Force delete (required for directories)", default=False)
            ],
            category="file_operations",
            dangerous=True
        )

    def execute(self, path: str, force: bool = False) -> str:
        return file_ops.delete_path(path, force)
