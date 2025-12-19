"""
Control and System Tools

Tools for controlling agent flow and signaling task completion.
"""

from typing import Dict, Any
from tools.tool_base import Tool, ToolMetadata, ToolParameter

class TaskCompletedTool(Tool):
    """Tool explicitly used to signal task completion"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="task_completed",
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
        Signals task completion.

        Args:
            message: Final summary of the task.

        Returns:
            Dictionary indicating success and status.
        """
        # Returns a special dict that TaskExecution can detect
        return {
            "success": True,
            "status": "completed",
            "message": message
        }
