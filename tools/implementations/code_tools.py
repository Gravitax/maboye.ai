"""
Code quality tools

Provides tools for static code analysis and verification.
"""

from tools.tool_base import Tool, ToolMetadata, ToolParameter
from tools import code_ops

class CheckSyntaxTool(Tool):
    """Tool for static code analysis"""
    
    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="check_syntax",
            description="Check Python file syntax without execution",
            parameters=[
                ToolParameter(name="file_path", type=str, description="Path to python file", required=True)
            ],
            category="code_quality"
        )

    def execute(self, file_path: str) -> str:
        return code_ops.check_syntax(file_path)
