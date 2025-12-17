"""
Agents Command

Manage and inspect agents (list, info).
"""

from typing import List
from .base_command import BaseCommand


class AgentsCommand(BaseCommand):
    """
    Command to manage agents.

    Subcommands:
    - /agents              : List all agents with stats
    """

    @property
    def description(self) -> str:
        """Command description."""
        return "Manage agents. Usage: /agents [list <name>|info <name>]"

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
                print("\nError: /agents info requires agent name")
                print("Usage: /agents info <name>\n")
                return False
            self._show_agent_info(args[1])
        else:
            print(f"\nError: Unknown subcommand '{args[0]}'")
            print("Available: list, info\n")
            return False

        return True

    def _list_agents(self):
        """List all registered agents with stats"""
        agent_repository = self._orchestrator.get_agent_repository()
        all_agents = agent_repository.find_all()

        print("\n" + "="*70)
        print("REGISTERED AGENTS")
        print("="*70)
        print(f"Total: {len(all_agents)}")
        print()

        if not all_agents:
            print("No agents registered.")
            print("="*70)
            print()
            return

        for idx, agent in enumerate(all_agents, 1):
            name = agent.get_agent_name()
            description = agent.get_description()
            tools_count = len(agent.agent_capabilities.authorized_tools)

            print(f"[{idx}] {name}")
            print(f"    Description: {description}")
            print(f"    Tools: {tools_count}")
            print()

        print("="*70)
