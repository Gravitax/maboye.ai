"""
Memory Command

Display and inspect conversation memory.
"""

from typing import List
from .base_command import BaseCommand


class MemoryCommand(BaseCommand):
    """Command to display memory statistics and content."""

    @property
    def description(self) -> str:
        """Command description."""
        return "Show memory statistics or content. Usage: /memory [ID|clear]"

    def execute(self, args: List[str]) -> bool:
        """Execute memory command."""
        if not args:
            self._display_memory_stats()
        elif args[0].lower() == "clear":
            self._clear_memory()
        elif args[0].lower() == "conversation":
            self._display_conversations()
        elif args[0].lower() == "agents":
            self._display_agents()
        elif args[0].lower() == "agent" and len(args) > 1:
            self._display_agent_detail(args[1])
        else:
            print(f"\nUnknown memory command: {args[0]}")
            print("Usage: /memory [conversation|agents|agent <id>|clear]\n")

        return True

    def _clear_memory(self) -> None:
        """Clear all conversation memory."""
        try:
            self._orchestrator.reset_conversation()
            print("All conversation history has been cleared.\n")
        except Exception as e:
            print(f"\nError clearing memory: {e}\n")

    def _display_memory_stats(self) -> None:
        """Display memory statistics overview."""
        stats = self._orchestrator.get_memory_stats()

        print("\nMemory Overview:")
        print("-" * 60)

        # Conversation stats
        conv_stats = stats.get("conversation", {})
        conv_count = conv_stats.get("size", 0)
        conv_status = "Empty" if conv_stats.get("is_empty", True) else "Has data"

        print(f"\n[1] CONVERSATIONS (Orchestrator):")
        print(f"    Total: {conv_count}")
        print(f"    Status: {conv_status}")

        # Agent stats
        agent_stats = stats.get("agents", {})
        agent_count = agent_stats.get("size", 0)
        agent_status = "Empty" if agent_stats.get("is_empty", True) else "Has data"

        print(f"\n[2] AGENTS:")
        print(f"    Total: {agent_count}")
        print(f"    Status: {agent_status}")

        print("-" * 60)
        print("\nUsage:")
        print("  /memory conversation    - View orchestrator conversations")
        print("  /memory agents          - View all agents")
        print("  /memory agent <id>      - View specific agent details")
        print("  /memory clear           - Clear all memory")
        print()

    def _display_conversations(self) -> None:
        """Display orchestrator conversations."""
        content = self._orchestrator.get_memory_content("conversation")

        print("\n" + "=" * 60)
        print("ORCHESTRATOR CONVERSATIONS")
        print("=" * 60)

        if not content:
            print("\nNo conversations found.")
        else:
            for conv_str in content:
                print(conv_str)

        print("\n" + "=" * 60 + "\n")

    def _display_agents(self) -> None:
        """Display all agents."""
        content = self._orchestrator.get_memory_content("agents")

        print("\n" + "=" * 60)
        print("AGENTS LIST")
        print("=" * 60)

        if not content:
            print("\nNo agents found.")
        else:
            for agent_str in content:
                print(agent_str)

        print("\n" + "=" * 60 + "\n")

    def _display_agent_detail(self, agent_id: str) -> None:
        """Display details for a specific agent."""
        content = self._orchestrator.get_memory_content("agents", agent_id=agent_id)

        if not content or not content[0]:
            print(f"\nAgent '{agent_id}' not found.\n")
        else:
            print(content[0])
            print()

