"""
Control and System Tools

Tools for controlling agent flow and signaling task completion.
"""

from typing import Dict, Any
from tools.tool_base import Tool, ToolMetadata, ToolParameter
from tools.tool_ids import ToolId

class TaskSuccessTool(Tool):
    """Tool explicitly used to signal task success"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=ToolId.TASK_SUCCESS.value,
            description="Call this when the objective is achieved.",
            parameters=[
                ToolParameter(
                    name="message",
                    type=str,
                    description="Final summary of what was achieved",
                    required=False,
                    default="Task completed successfully."
                )
            ],
            category="system"
        )

    def execute(self, message: str = "Task completed successfully.") -> Dict[str, Any]:
        """
        Signals task success.

        Args:
            message: Final summary of the task.

        Returns:
            Dictionary indicating success and status.
        """
        return {
            "success": True,
            "status": "success",
            "message": message
        }


class TaskErrorTool(Tool):
    """Tool explicitly used to signal task failure"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=ToolId.TASK_ERROR.value,
            description="Call this when the objective cannot be achieved due to an error.",
            parameters=[
                ToolParameter(
                    name="error_message",
                    type=str,
                    description="Detailed description of the error",
                    required=True
                )
            ],
            category="system"
        )

    def execute(self, error_message: str) -> Dict[str, Any]:
        """
        Signals task failure.

        Args:
            error_message: Error description.

        Returns:
            Dictionary indicating failure and status.
        """
        return {
            "success": False,
            "status": "error",
            "error_message": error_message
        }
