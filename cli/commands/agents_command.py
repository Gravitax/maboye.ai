"""
Agents Command

Manage and inspect agents (list, info).
"""

from typing import List
from .base_command import BaseCommand
from cli.cli_utils import Color, _print_formatted_message


class AgentsCommand(BaseCommand):
    """
    Command to manage agents.

    Subcommands:
    - /agents              : List all agents with stats
    - /agents <name>       : Show detailed info for specific agent
    """

    @property
    def description(self) -> str:
        """Command description."""
        return "Manage agents. Usage: /agents [name]"

    def execute(self, args: List[str]) -> bool:
        """
        Execute agents command.

        Args:
            args: Command arguments

        Returns:
            True if command executed successfully
        """
        if not args:
            # Default: list all agents
            self._list_agents()
        elif args[0] == "list":
            self._list_agents()
        elif args[0] == "info":
            if len(args) < 2:
                _print_formatted_message("\nError: /agents info requires agent name", color=Color.RED)
                _print_formatted_message("Usage: /agents <name>\n")
                return False
            self._show_agent_info(args[1])
        else:
            # Assume arg is agent name
            self._show_agent_info(args[0])

        return True

    def _list_agents(self):
        """List all registered agents with stats"""
        agent_repository = self._orchestrator.get_agent_repository()
        all_agents = agent_repository.find_all()
        
        separator = "-" * 70

        _print_formatted_message("\n" + separator, color=Color.BRIGHT_BLACK)
        _print_formatted_message("REGISTERED AGENTS", style=Color.BOLD, color=Color.BLUE)
        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
        _print_formatted_message(f"Total: {len(all_agents)}\n")

        if not all_agents:
            _print_formatted_message("No agents registered.", color=Color.YELLOW)
            _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
            _print_formatted_message("")
            return

        for idx, agent in enumerate(all_agents, 1):
            name = f"{Color.GREEN}{agent.get_agent_name()}{Color.RESET}"
            description = agent.get_description()
            tools_count = len(agent.agent_capabilities.authorized_tools)

            _print_formatted_message(f"[{idx}] {name}")
            _print_formatted_message(f"    Description: {description}")
            _print_formatted_message(f"    Tools: {tools_count}")
            _print_formatted_message("")

        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)

    def _show_agent_info(self, agent_name: str):
        """
        Show detailed information for a specific agent.

        Args:
            agent_name: Name of the agent to inspect
        """
        agent_repository = self._orchestrator.get_agent_repository()
        agent = agent_repository.find_by_name(agent_name)

        if not agent:
            _print_formatted_message(f"\nError: Agent '{agent_name}' not found.", color=Color.RED)
            return

        caps = agent.agent_capabilities
        identity = agent.agent_identity
        separator = "-" * 70
        
        _print_formatted_message("\n" + separator, color=Color.BRIGHT_BLACK)
        _print_formatted_message(f"AGENT DETAILS: {Color.GREEN}{agent.get_agent_name()}", style=Color.BOLD)
        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
        
        # Identity & Basic Info
        status_color = Color.GREEN if agent.is_active else Color.RED
        status = f"{status_color}{'Active' if agent.is_active else 'Inactive'}{Color.RESET}"
        
        _print_formatted_message(f"ID:          {identity.agent_id}")
        _print_formatted_message(f"Status:      {status}")
        _print_formatted_message(f"Description: {caps.description}")
        _print_formatted_message(f"Created:     {agent.created_at}")
        _print_formatted_message(f"Updated:     {agent.updated_at}")
        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
        
        # Capabilities
        _print_formatted_message("CAPABILITIES:", style=Color.BOLD, color=Color.CYAN)
        _print_formatted_message(f"  Max Reasoning Turns: {caps.max_reasoning_turns}")
        _print_formatted_message(f"  Max Memory Turns:    {caps.max_memory_turns}")
        tags = f"{Color.MAGENTA}{', '.join(caps.specialization_tags)}{Color.RESET}" if caps.specialization_tags else "None"
        _print_formatted_message(f"  Specialization Tags: {tags}")
        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
        
        # LLM Configuration
        _print_formatted_message("LLM CONFIGURATION:", style=Color.BOLD, color=Color.CYAN)
        _print_formatted_message(f"  Temperature:     {caps.llm_temperature}")
        _print_formatted_message(f"  Max Tokens:      {caps.llm_max_tokens}")
        _print_formatted_message(f"  Timeout:         {caps.llm_timeout}s")
        _print_formatted_message(f"  Response Format: {caps.llm_response_format}")
        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
        
        # Tools
        tools = caps.authorized_tools
        _print_formatted_message(f"AUTHORIZED TOOLS ({len(tools)}):", style=Color.BOLD, color=Color.CYAN)
        if not tools:
            _print_formatted_message("  (No tools authorized - Unrestricted access implied if empty list)", color=Color.YELLOW)
        else:
            # Group tools for better readability if list is long
            sorted_tools = sorted(tools)
            for i in range(0, len(sorted_tools), 3):
                chunk = sorted_tools[i:i+3]
                _print_formatted_message("  " + " | ".join(f"{Color.YELLOW}{t:<20}{Color.RESET}" for t in chunk))
        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
        
        # System Prompt
        _print_formatted_message("SYSTEM PROMPT:", style=Color.BOLD, color=Color.CYAN)
        _print_formatted_message(agent.system_prompt)
        _print_formatted_message(separator, color=Color.BRIGHT_BLACK)
        _print_formatted_message("")