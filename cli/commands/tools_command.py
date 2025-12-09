"""
Tools Command

List available tools and their parameters.
"""

from typing import List
from .base_command import BaseCommand


class ToolsCommand(BaseCommand):
    """Command to list available tools."""

    @property
    def description(self) -> str:
        """Command description."""
        return "List available tools."

    def execute(self, args: List[str]) -> bool:
        """Execute tools command."""
        tools_info = self._orchestrator.get_tool_info()
        print("\nAvailable Tools:")
        print("-" * 60)

        if not tools_info:
            print("No tools registered.")
        else:
            for tool in tools_info:
                print(f"- {tool['name']}: {tool['description']} (Category: {tool['category']})")
                if tool['parameters']:
                    print("  Parameters:")
                    for param in tool['parameters']:
                        req = " (required)" if param['required'] else ""
                        default = f" (default: {param['default']})" if param['default'] is not None else ""
                        print(f"    - {param['name']} ({param['type']}){req}{default}: {param['description']}")

        print("-" * 60)
        print()
        return True
