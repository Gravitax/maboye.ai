"""
Tool Implementations

Provides all tool implementations organized by category:
- File operations: Read, write, edit, list files
- Code search: Grep, find files, explore directory structure
- Bash execution: Safe shell command execution
- Git operations: Status, diff, log, add, commit

All tools are registered via register_all_tools() function.
"""

from tools.implementations.file_tools import (
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListFilesTool,
    FileInfoTool
)

from tools.implementations.search_tools import (
    GrepTool,
    FindFileTool,
    GetFileStructureTool,
    CodeSearchTool
)

from tools.implementations.bash_tools import (
    BashTool,
    GitStatusTool,
    GitDiffTool,
    GitLogTool,
    GitAddTool,
    GitCommitTool
)


def register_all_tools():
    """
    Register all tool implementations in global registry

    Registers tools from all categories:
    - 5 file operation tools
    - 4 search tools
    - 6 bash and git tools

    Total: 15 tools
    """
    from tools.tool_base import register_tool
    from core.logger import logger

    # File operations (5 tools)
    file_tools = [
        ReadFileTool(),
        WriteFileTool(),
        EditFileTool(),
        ListFilesTool(),
        FileInfoTool()
    ]

    # Search tools (4 tools)
    search_tools = [
        GrepTool(),
        FindFileTool(),
        GetFileStructureTool(),
        CodeSearchTool()
    ]

    # Bash and Git tools (6 tools)
    bash_tools = [
        BashTool(),
        GitStatusTool(),
        GitDiffTool(),
        GitLogTool(),
        GitAddTool(),
        GitCommitTool()
    ]

    # Register all tools
    all_tools = file_tools + search_tools + bash_tools

    for tool in all_tools:
        register_tool(tool)


__all__ = [
    # File tools
    'ReadFileTool',
    'WriteFileTool',
    'EditFileTool',
    'ListFilesTool',
    'FileInfoTool',
    # Search tools
    'GrepTool',
    'FindFileTool',
    'GetFileStructureTool',
    'CodeSearchTool',
    # Bash/Git tools
    'BashTool',
    'GitStatusTool',
    'GitDiffTool',
    'GitLogTool',
    'GitAddTool',
    'GitCommitTool',
    # Registration function
    'register_all_tools'
]
