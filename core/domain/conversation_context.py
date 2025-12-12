"""
Conversation Context Value Object

Immutable snapshot of a conversation context at a specific point in time.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List

from core.domain.agent_identity import AgentIdentity


@dataclass(frozen=True)
class ConversationContext:
    """
    Immutable snapshot of conversation context for an agent.

    Captures the full context of a conversation at a specific moment,
    including history and metadata. Used for prompt construction and
    context sharing between agents.

    Attributes:
        agent_identity: Identity of the agent this context belongs to
        conversation_history: List of conversation turns
        context_metadata: Additional contextual information
        created_at: When this snapshot was created
    """

    agent_identity: AgentIdentity
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    context_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """
        Validate context after initialization.

        Raises:
            ValueError: If validation fails
        """
        self._validate_identity()
        self._validate_history()
        self._validate_metadata()
        self._validate_timestamp()

    def _validate_identity(self):
        """
        Validate agent identity.

        Raises:
            ValueError: If identity is invalid
        """
        if not isinstance(self.agent_identity, AgentIdentity):
            raise ValueError(
                f"agent_identity must be AgentIdentity, got {type(self.agent_identity)}"
            )

    def _validate_history(self):
        """
        Validate conversation history.

        Raises:
            ValueError: If history is invalid
        """
        if not isinstance(self.conversation_history, list):
            raise ValueError(
                f"conversation_history must be a list, got {type(self.conversation_history)}"
            )

        for idx, turn in enumerate(self.conversation_history):
            if not isinstance(turn, dict):
                raise ValueError(
                    f"History turn {idx} must be dict, got {type(turn)}"
                )

            if 'role' not in turn:
                raise ValueError(f"History turn {idx} missing 'role' field")

            if 'content' not in turn:
                raise ValueError(f"History turn {idx} missing 'content' field")

    def _validate_metadata(self):
        """
        Validate context metadata.

        Raises:
            ValueError: If metadata is invalid
        """
        if not isinstance(self.context_metadata, dict):
            raise ValueError(
                f"context_metadata must be a dict, got {type(self.context_metadata)}"
            )

    def _validate_timestamp(self):
        """
        Validate created_at timestamp.

        Raises:
            ValueError: If timestamp is invalid
        """
        if not isinstance(self.created_at, datetime):
            raise ValueError(
                f"created_at must be datetime, got {type(self.created_at)}"
            )

    @staticmethod
    def create_from_memory(
        agent_identity: AgentIdentity,
        memory_manager: Any,
        max_turns: int = None
    ) -> 'ConversationContext':
        """
        Factory method to create context from memory repository.

        Args:
            agent_identity: Identity of the agent
            memory_manager: Memory repository to extract history from
            max_turns: Maximum number of turns to include (None = all)

        Returns:
            New ConversationContext instance

        Example:
            context = ConversationContext.create_from_memory(
                agent_identity=identity,
                memory_manager=memory_repository,
                max_turns=10
            )
        """
        # Extract history from memory repository
        history = memory_manager.get_conversation_history(
            agent_id=agent_identity.agent_id,
            max_turns=max_turns
        )

        # Extract metadata
        metadata = {
            'agent_id': agent_identity.agent_id,
            'agent_name': agent_identity.agent_name,
            'total_turns': len(history),
            'max_turns_requested': max_turns
        }

        return ConversationContext(
            agent_identity=agent_identity,
            conversation_history=history,
            context_metadata=metadata,
            created_at=datetime.now()
        )

    def get_turn_count(self) -> int:
        """
        Get the number of conversation turns in this context.

        Returns:
            Number of turns
        """
        return len(self.conversation_history)

    def get_last_turn(self) -> Dict[str, Any]:
        """
        Get the most recent conversation turn.

        Returns:
            Last turn dict, or empty dict if no history

        Example:
            last_turn = context.get_last_turn()
            if last_turn:
                print(f"Last role: {last_turn['role']}")
        """
        if not self.conversation_history:
            return {}
        return self.conversation_history[-1]

    def get_user_turns(self) -> List[Dict[str, Any]]:
        """
        Get only user turns from history.

        Returns:
            List of user turns
        """
        return [turn for turn in self.conversation_history if turn.get('role') == 'user']

    def get_assistant_turns(self) -> List[Dict[str, Any]]:
        """
        Get only assistant turns from history.

        Returns:
            List of assistant turns
        """
        return [
            turn for turn in self.conversation_history
            if turn.get('role') == 'assistant'
        ]

    def is_empty(self) -> bool:
        """
        Check if context has no conversation history.

        Returns:
            True if no history, False otherwise
        """
        return len(self.conversation_history) == 0

    def __str__(self) -> str:
        """String representation for logging."""
        agent_name = self.agent_identity.agent_name
        turn_count = self.get_turn_count()
        return f"ConversationContext(agent={agent_name}, turns={turn_count})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"ConversationContext("
            f"agent={self.agent_identity.agent_name}, "
            f"turns={self.get_turn_count()}, "
            f"created={self.created_at.isoformat()})"
        )
