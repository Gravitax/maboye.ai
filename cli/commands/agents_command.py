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
    - /agents info <name>  : Show detailed info about agent
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
        active_agents = agent_repository.find_active()

        print("\n" + "="*70)
        print("REGISTERED AGENTS")
        print("="*70)
        print(f"Total: {len(all_agents)} | Active: {len(active_agents)}")
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
            is_active = agent.is_active

            status = "ACTIVE" if is_active else "inactive"
            status_marker = "●" if is_active else "○"

            print(f"{status_marker} [{idx}] {name}")
            print(f"    Description: {description}")
            print(f"    Tools: {tools_count}")
            print(f"    Status: {status}")
            print()

        print("="*70)
        print("Usage:")
        print("  /agents info <name>    - Show detailed agent information")
        print()

    def _show_agent_info(self, agent_name: str):
        """
        Show detailed information about an agent.

        Args:
            agent_name: Name of agent
        """
        agent_repository = self._orchestrator.get_agent_repository()

        # Find agent by name
        agent = agent_repository.find_by_name(agent_name)

        if not agent:
            print(f"\nError: Agent '{agent_name}' not found.")
            print("Use /agents to see available agents.\n")
            return

        # Display detailed info
        print("\n" + "="*70)
        print(f"AGENT: {agent.get_agent_name()}")
        print("="*70)
        print()

        print(f"Agent ID: {agent.get_agent_id()}")
        print(f"Description: {agent.get_description()}")
        print(f"Status: {'ACTIVE' if agent.is_active else 'Inactive'}")
        print()

        print("Capabilities:")
        print(f"  Max reasoning turns: {agent.agent_capabilities.max_reasoning_turns}")
        print(f"  Max memory turns: {agent.agent_capabilities.max_memory_turns}")
        print()

        print(f"Authorized Tools ({len(agent.agent_capabilities.authorized_tools)}):")
        for tool in agent.agent_capabilities.authorized_tools:
            print(f"  - {tool}")
        print()

        print("System Prompt:")
        print("-" * 70)
        prompt_lines = agent.system_prompt.split('\n')
        for line in prompt_lines[:10]:  # Show first 10 lines
            print(f"  {line}")
        if len(prompt_lines) > 10:
            print(f"  ... ({len(prompt_lines) - 10} more lines)")
        print("-" * 70)
        print()

        print("Statistics:")
        print(f"  Total interactions: {agent.total_interactions}")
        if agent.last_interaction_timestamp:
            print(f"  Last interaction: {agent.last_interaction_timestamp}")
        else:
            print(f"  Last interaction: Never")
        print()

        print("="*70)
        print()
