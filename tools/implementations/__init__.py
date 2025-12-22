"""
Tool Implementations

Provides all tool implementations organized by category:
- Control/System tools: Signal task completion
- File operations: Read, write, edit, list files, move, delete
- Web operations: Fetch URL content
- Code quality: Syntax check
- Code search: Grep, find files, explore directory structure
- Bash execution: Safe shell command execution
- Git operations: Status, diff, log, add, commit, checkout

All tools are registered via register_all_tools() function.
"""

from tools.implementations.control_tools import (
    TaskSuccessTool,
    TaskErrorTool,
    TasksCompletedTool
)

from tools.implementations.file_tools import (
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListFilesTool,
    FileInfoTool,
    MoveFileTool,
    DeleteFileTool
)

from tools.implementations.web_tools import (
    FetchUrlTool
)

from tools.implementations.code_tools import (
    CheckSyntaxTool
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
    GitCommitTool,
    GitCheckoutTool
)


def register_all_tools():
    """
    Register all tool implementations in global registry

    Registers tools from all categories:
    - 2 system/control tool
    - 7 file operation tools
    - 1 web tool
    - 1 code tool
    - 4 search tools
    - 7 bash and git tools

    Total: 22 tools
    """
    from tools.tool_base import register_tool
    from core.logger import logger

    # System / Control tools (2 tools)
    control_tools = [
        TaskSuccessTool(),
        TaskErrorTool(),
        TasksCompletedTool()
    ]

    # File operations (7 tools)
    file_tools = [
        ReadFileTool(),
        WriteFileTool(),
        EditFileTool(),
        ListFilesTool(),
        FileInfoTool(),
        MoveFileTool(),
        DeleteFileTool()
    ]

    # Web tools (1 tool)
    web_tools = [
        FetchUrlTool()
    ]

    # Code tools (1 tool)
    code_tools = [
        CheckSyntaxTool()
    ]

    # Search tools (4 tools)
    search_tools = [
        GrepTool(),
        FindFileTool(),
        GetFileStructureTool(),
        CodeSearchTool()
    ]

    # Bash and Git tools (7 tools)
    bash_tools = [
        BashTool(),
        GitStatusTool(),
        GitDiffTool(),
        GitLogTool(),
        GitAddTool(),
        GitCommitTool(),
        GitCheckoutTool()
    ]

    # Register all tools
    all_tools = (
        control_tools +
        file_tools +
        web_tools +
        code_tools +
        search_tools +
        bash_tools
    )

    for tool in all_tools:
        register_tool(tool)


__all__ = [
    # Control tools
    'TaskSuccessTool',
    'TaskErrorTool',
    'TasksCompletedTool',
    # File tools
    'ReadFileTool',
    'WriteFileTool',
    'EditFileTool',
    'ListFilesTool',
    'FileInfoTool',
    'MoveFileTool',
    'DeleteFileTool',
    # Web tools
    'FetchUrlTool',
    # Code tools
    'CheckSyntaxTool',
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
    'GitCheckoutTool',
    # Registration function
    'register_all_tools'
]
