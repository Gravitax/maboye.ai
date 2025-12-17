"""
Memory Formatter

Formats memory content for display in CLI.
Handles both conversation view and agent view.
"""

from typing import List, Dict, Any, Optional
from core.repositories.memory_repository import MemoryRepository

from core.logger import logger


class MemoryFormatter:
    """
    Formats memory content for display.

    Provides two views:
    - Conversations: Orchestrator conversations (user input → orchestrator output)
    - Agents: All agents with their conversation references
    """

    def __init__(self, memory_repository: MemoryRepository):
        """
        Initialize memory formatter.

        Args:
            memory_repository: Repository to fetch memory from
        """
        self._memory_repository = memory_repository

    def get_conversation_stats(self, orchestrator_id: str = "orchestrator") -> Dict[str, Any]:
        """
        Get conversation statistics for orchestrator.

        Args:
            orchestrator_id: ID of the orchestrator agent

        Returns:
            Dictionary with conversation stats
        """
        if not self._memory_repository.exists(orchestrator_id):
            return {
                "size": 0,
                "is_empty": True
            }

        turns = self._memory_repository.get_conversation_history(
            agent_id=orchestrator_id,
            max_turns=None
        )

        # Count user turns (each represents a conversation)
        user_turns = sum(1 for turn in turns if turn.get("role") == "user")

        return {
            "size": user_turns,
            "is_empty": user_turns == 0
        }

    def get_agent_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all agents.

        Returns:
            Dictionary with agent stats
        """
        all_agent_ids = self._memory_repository.get_all_agent_ids()

        # Filter out orchestrator and agents with no conversation data
        agent_ids = [
            aid for aid in all_agent_ids
            if aid != "orchestrator" and self._memory_repository.get_turn_count(aid) > 0
        ]

        return {
            "size": len(agent_ids),
            "is_empty": len(agent_ids) == 0
        }

    def format_conversations(self, orchestrator_id: str = "orchestrator") -> List[str]:
        """
        Format orchestrator conversations for display.

        Args:
            orchestrator_id: ID of the orchestrator agent

        Returns:
            List of formatted conversation strings
        """
        if not self._memory_repository.exists(orchestrator_id):
            return []

        turns = self._memory_repository.get_conversation_history(
            agent_id=orchestrator_id,
            max_turns=None
        )

        formatted = []
        conversation_num = 1
        idx = 0

        while idx < len(turns):
            turn = turns[idx]

            logger.info("[format_conversations]", "loop")

            if turn.get("role") == "user":
                called_agents = []
                # Start of a conversation
                user_input = turn.get("content", "")
                timestamp = turn.get("timestamp", "N/A")

                logger.info("[format_conversations]", "user_input", {"user_input":user_input})

                # Check metadata for agents called
                metadata = turn.get("metadata", {})
                if "called_agents" in metadata:
                    called_agents = metadata["called_agents"]

                # Find next assistant turn
                next_idx = idx + 1
                if next_idx < len(turns) and turns[next_idx].get("role") == "assistant":
                    orchestrator_output = turns[next_idx].get("content", "")
                    # Check metadata for agents called
                    metadata = turns[next_idx].get("metadata", {})
                    if "called_agents" in metadata:
                        called_agents += metadata["called_agents"]

                # Format this conversation
                formatted.append(self._format_single_conversation(
                    conversation_num,
                    timestamp,
                    user_input,
                    called_agents,
                    orchestrator_output
                ))

                conversation_num += 1
                idx = next_idx + 1 if orchestrator_output else idx + 1
            else:
                idx += 1

        return formatted

    def _format_single_conversation(
        self,
        num: int,
        timestamp: str,
        user_input: str,
        called_agents: List[str],
        output: Optional[str]
    ) -> str:
        """
        Format a single conversation.

        Args:
            num: Conversation number
            timestamp: Timestamp
            user_input: User input text
            called_agents: List of agent names/IDs
            output: Orchestrator output

        Returns:
            Formatted string
        """
        lines = [
            f"\n{'='*60}",
            f"CONVERSATION {num}",
            f"{'='*60}",
            f"Timestamp: {timestamp}",
            f"\n--- USER INPUT ---",
            user_input
        ]

        if called_agents:
            lines.append(f"\n--- AGENTS CALLED ---")
            for i, agent in enumerate(called_agents, 1):
                lines.append(f"  {i}. {agent.get('agent_name', agent)}")

        if output:
            lines.append(f"\n--- ORCHESTRATOR OUTPUT ---")
            lines.append(output)

        return "\n".join(lines)

    def format_agents(self) -> List[str]:
        """
        Format all agents with their conversation references.

        Returns:
            List of formatted agent strings
        """
        all_agent_ids = self._memory_repository.get_all_agent_ids()

        # Filter out orchestrator and agents with no conversation data
        agent_ids = [
            aid for aid in all_agent_ids
            if aid != "orchestrator" and self._memory_repository.get_turn_count(aid) > 0
        ]

        if not agent_ids:
            return []

        formatted = []

        for idx, agent_id in enumerate(agent_ids, 1):
            turns = self._memory_repository.get_conversation_history(
                agent_id=agent_id,
                max_turns=None
            )

            # Get last turn to find conversation reference
            conversation_ref = "N/A"
            query = "N/A"
            response = "N/A"
            timestamp = "N/A"

            if turns:
                # Look for user turn (query) and assistant turn (response)
                for turn in turns:
                    if turn.get("role") == "user":
                        query = turn.get("content", "N/A")
                        timestamp = turn.get("timestamp", "N/A")
                        metadata = turn.get("metadata", {})
                        conversation_ref = metadata.get("conversation_id", "N/A")
                    elif turn.get("role") == "assistant":
                        response = turn.get("content", "N/A")

            formatted.append(self._format_single_agent(
                idx,
                agent_id,
                conversation_ref,
                timestamp,
                query,
                response,
                len(turns)
            ))

        return formatted

    def _format_single_agent(
        self,
        num: int,
        agent_id: str,
        conversation_ref: str,
        timestamp: str,
        query: str,
        response: str,
        total_turns: int
    ) -> str:
        """
        Format a single agent's information.

        Args:
            num: Agent number in list
            agent_id: Agent identifier
            conversation_ref: Reference to parent conversation
            timestamp: Last interaction timestamp
            query: Query sent to agent
            response: Response from agent
            total_turns: Total number of turns

        Returns:
            Formatted string
        """
        lines = [
            f"\n{'='*60}",
            f"AGENT {num}: {agent_id}",
            f"{'='*60}",
            f"Conversation ID: {conversation_ref}",
            f"Timestamp: {timestamp}",
            f"Total Turns: {total_turns}",
            f"\n--- QUERY SENT TO LLM ---",
            query[:500] + "..." if len(query) > 500 else query,
            f"\n--- RESPONSE FROM LLM ---",
            response[:500] + "..." if len(response) > 500 else response
        ]

        return "\n".join(lines)

    def get_agent_detail(self, agent_id: str) -> Optional[str]:
        """
        Get detailed view of a specific agent's memory.

        Args:
            agent_id: Agent identifier

        Returns:
            Formatted string with full agent history, or None if not found
        """
        if not self._memory_repository.exists(agent_id):
            return None

        turns = self._memory_repository.get_conversation_history(
            agent_id=agent_id,
            max_turns=None
        )

        lines = [
            f"\n{'='*60}",
            f"AGENT DETAIL: {agent_id}",
            f"{'='*60}",
            f"Total Turns: {len(turns)}",
            f"\n--- FULL CONVERSATION HISTORY ---\n"
        ]

        for idx, turn in enumerate(turns, 1):
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
            timestamp = turn.get("timestamp", "N/A")
            metadata = turn.get("metadata", {})

            lines.append(f"\n[{idx}] {role.upper()} - {timestamp}")
            if metadata:
                lines.append(f"Metadata: {metadata}")
            lines.append(content[:300] + "..." if len(content) > 300 else content)
            lines.append("-" * 40)

        return "\n".join(lines)
