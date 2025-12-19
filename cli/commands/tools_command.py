"""
Tools Command

List available tools and their parameters.
"""

from typing import List
from .base_command import BaseCommand
from cli.cli_utils import Color, _print_formatted_message


class ToolsCommand(BaseCommand):
    """Command to list available tools."""

    @property
    def description(self) -> str:
        """Command description."""
        return "Tool information and exploration. Usage: /tools [option]"

    def execute(self, args: List[str]) -> bool:
        """
        Execute tools command.
        
        Args:
            args: Command arguments.
        """
        tools_info = self._orchestrator.get_tool_info()
        separator = "-" * 60
        
        if not args:
            # Menu mode
            _print_formatted_message("\nTool Command Options:", style=Color.BOLD)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            _print_formatted_message("1. List all tools (/tools 1)", color=Color.CYAN)
            _print_formatted_message("2. List tool categories (/tools 2)", color=Color.CYAN)
            _print_formatted_message("3. List safe tools (/tools safe)", color=Color.GREEN)
            _print_formatted_message("4. List dangerous tools (/tools dangerous)", color=Color.RED)
            _print_formatted_message("\nUsage:", style=Color.BOLD)
            _print_formatted_message("  /tools <category_name> : List tools in a specific category")
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            _print_formatted_message("")
            return True

        # Determine specific mode based on args
        mode = None
        target_category = None
        
        if args[0] == "1":
            mode = "all"
        elif args[0] == "2":
            mode = "categories"
        elif args[0] == "safe":
            mode = "safe_tools"
        elif args[0] == "dangerous":
            mode = "dangerous_tools"
        else:
            mode = "category_filter"
            target_category = args[0]

        if mode == "all":
            _print_formatted_message("\nAvailable Tools:", style=Color.BOLD)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            if not tools_info:
                _print_formatted_message("No tools registered.", color=Color.YELLOW)
            else:
                for tool in tools_info:
                    # Tool Header
                    name = f"{Color.GREEN}{tool['name']}{Color.RESET}"
                    desc = f"{Color.WHITE}{tool['description']}{Color.RESET}"
                    cat = f"{Color.CYAN}(Category: {tool['category']}){Color.RESET}"
                    _print_formatted_message(f"- {name}: {desc} {cat}")
                    
                    if tool['parameters']:
                        _print_formatted_message("  Parameters:", color=Color.BRIGHT_BLACK)
                        for param in tool['parameters']:
                            req = f"{Color.RED}(required){Color.RESET}" if param['required'] else ""
                            default = f"{Color.BRIGHT_BLACK}(default: {param['default']}){Color.RESET}" if param['default'] is not None else ""
                            p_name = f"{Color.YELLOW}{param['name']}{Color.RESET}"
                            p_type = f"{Color.MAGENTA}({param['type']}){Color.RESET}"
                            p_desc = param['description']
                            
                            _print_formatted_message(f"    - {p_name} {p_type} {req} {default}: {p_desc}")
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)

        elif mode == "categories":
            _print_formatted_message("\nTool Categories:", style=Color.BOLD)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            if not tools_info:
                _print_formatted_message("No tools registered.", color=Color.YELLOW)
            else:
                categories = sorted(list(set(tool['category'] for tool in tools_info)))
                for cat in categories:
                    _print_formatted_message(f"- {cat}", color=Color.CYAN)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)

        elif mode == "safe_tools":
            _print_formatted_message("\nSafe Tools (Read-only / Non-destructive):", style=Color.BOLD, color=Color.GREEN)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            safe_tools = [t for t in tools_info if not t.get('dangerous', False)]
            if not safe_tools:
                _print_formatted_message("No safe tools found.", color=Color.YELLOW)
            else:
                for tool in safe_tools:
                    name = f"{Color.GREEN}{tool['name']}{Color.RESET}"
                    desc = tool['description']
                    _print_formatted_message(f"- {name}: {desc}")
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)

        elif mode == "dangerous_tools":
            _print_formatted_message("\nDangerous Tools (Write / Execute / State-changing):", style=Color.BOLD, color=Color.RED)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            dangerous_tools = [t for t in tools_info if t.get('dangerous', False)]
            if not dangerous_tools:
                _print_formatted_message("No dangerous tools found.", color=Color.YELLOW)
            else:
                for tool in dangerous_tools:
                    name = f"{Color.RED}{tool['name']}{Color.RESET}"
                    desc = tool['description']
                    _print_formatted_message(f"- {name}: {desc}")
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)

        elif mode == "category_filter":
            _print_formatted_message(f"\nTools in category '{target_category}':", style=Color.BOLD)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            
            filtered_tools = [
                t for t in tools_info 
                if t['category'].lower() == target_category.lower()
            ]
            
            if not filtered_tools:
                _print_formatted_message(f"No tools found in category '{target_category}'.", color=Color.YELLOW)
            else:
                for tool in filtered_tools:
                    name = f"{Color.GREEN}{tool['name']}{Color.RESET}"
                    desc = tool['description']
                    _print_formatted_message(f"- {name}: {desc}")
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)

        _print_formatted_message("")
        return True