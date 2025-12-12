"""
Cross-Agent Context Value Object

Immutable snapshot of context shared between multiple agents.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.domain.agent_identity import AgentIdentity
from core.domain.conversation_context import ConversationContext


@dataclass(frozen=True)
class CrossAgentContext:
    """
    Immutable cross-agent context for inter-agent communication.

    Captures contexts shared from multiple agents to enable collaboration
    and context passing between agents in the system.

    Attributes:
        requesting_agent_id: ID of the agent requesting shared context
        shared_contexts: List of contexts from other agents
        context_metadata: Additional metadata about the sharing
        created_at: When this cross-agent context was created
    """

    requesting_agent_id: str
    shared_contexts: List[ConversationContext] = field(default_factory=list)
    context_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """
        Validate cross-agent context after initialization.

        Raises:
            ValueError: If validation fails
        """
        self._validate_requesting_agent_id()
        self._validate_shared_contexts()
        self._validate_metadata()
        self._validate_timestamp()

    def _validate_requesting_agent_id(self):
        """
        Validate requesting agent ID.

        Raises:
            ValueError: If agent ID is invalid
        """
        if not self.requesting_agent_id:
            raise ValueError("requesting_agent_id cannot be empty")

        if not isinstance(self.requesting_agent_id, str):
            raise ValueError(
                f"requesting_agent_id must be string, got {type(self.requesting_agent_id)}"
            )

    def _validate_shared_contexts(self):
        """
        Validate shared contexts list.

        Raises:
            ValueError: If shared contexts are invalid
        """
        if not isinstance(self.shared_contexts, list):
            raise ValueError(
                f"shared_contexts must be a list, got {type(self.shared_contexts)}"
            )

        for idx, context in enumerate(self.shared_contexts):
            if not isinstance(context, ConversationContext):
                raise ValueError(
                    f"Shared context {idx} must be ConversationContext, "
                    f"got {type(context)}"
                )

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
    def create_from_agents(
        requesting_agent_id: str,
        agent_contexts: List[ConversationContext],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'CrossAgentContext':
        """
        Factory method to create cross-agent context from agent contexts.

        Args:
            requesting_agent_id: ID of the agent making the request
            agent_contexts: List of conversation contexts from other agents
            metadata: Optional metadata about the sharing

        Returns:
            New CrossAgentContext instance

        Example:
            cross_context = CrossAgentContext.create_from_agents(
                requesting_agent_id="agent-123",
                agent_contexts=[context1, context2],
                metadata={'purpose': 'collaboration'}
            )
        """
        final_metadata = metadata or {}
        final_metadata.update({
            'requesting_agent': requesting_agent_id,
            'total_shared_agents': len(agent_contexts),
            'agent_ids': [
                ctx.agent_identity.agent_id
                for ctx in agent_contexts
            ]
        })

        return CrossAgentContext(
            requesting_agent_id=requesting_agent_id,
            shared_contexts=agent_contexts,
            context_metadata=final_metadata,
            created_at=datetime.now()
        )

    def get_context_by_agent_id(self, agent_id: str) -> Optional[ConversationContext]:
        """
        Get shared context for a specific agent by ID.

        Args:
            agent_id: ID of the agent to find context for

        Returns:
            ConversationContext if found, None otherwise

        Example:
            context = cross_context.get_context_by_agent_id("agent-456")
            if context:
                print(f"Found context with {context.get_turn_count()} turns")
        """
        for context in self.shared_contexts:
            if context.agent_identity.agent_id == agent_id:
                return context
        return None

    def get_context_by_agent_name(self, agent_name: str) -> Optional[ConversationContext]:
        """
        Get shared context for a specific agent by name.

        Args:
            agent_name: Name of the agent to find context for

        Returns:
            ConversationContext if found, None otherwise

        Example:
            context = cross_context.get_context_by_agent_name("CodeAgent")
        """
        for context in self.shared_contexts:
            if context.agent_identity.agent_name == agent_name:
                return context
        return None

    def get_all_agent_identities(self) -> List[AgentIdentity]:
        """
        Get identities of all agents sharing context.

        Returns:
            List of AgentIdentity objects
        """
        return [context.agent_identity for context in self.shared_contexts]

    def get_total_turns_across_agents(self) -> int:
        """
        Get total number of conversation turns across all shared contexts.

        Returns:
            Sum of all turns from all agents
        """
        return sum(
            context.get_turn_count()
            for context in self.shared_contexts
        )

    def get_shared_agent_count(self) -> int:
        """
        Get the number of agents sharing context.

        Returns:
            Number of agents in shared_contexts
        """
        return len(self.shared_contexts)

    def is_empty(self) -> bool:
        """
        Check if there are no shared contexts.

        Returns:
            True if no contexts are shared, False otherwise
        """
        return len(self.shared_contexts) == 0

    def has_context_from_agent(self, agent_id: str) -> bool:
        """
        Check if context from specific agent is included.

        Args:
            agent_id: ID of the agent to check for

        Returns:
            True if agent's context is present, False otherwise
        """
        return self.get_context_by_agent_id(agent_id) is not None

    def __str__(self) -> str:
        """String representation for logging."""
        agent_count = self.get_shared_agent_count()
        return (
            f"CrossAgentContext(requesting={self.requesting_agent_id[:8]}..., "
            f"shared_agents={agent_count})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        agent_names = [
            ctx.agent_identity.agent_name
            for ctx in self.shared_contexts
        ]
        return (
            f"CrossAgentContext("
            f"requesting={self.requesting_agent_id}, "
            f"shared_agents={agent_names}, "
            f"created={self.created_at.isoformat()})"
        )
