"""
Registered Agent Entity

Mutable entity representing an agent registered in the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from core.domain.agent_identity import AgentIdentity
from core.domain.agent_capabilities import AgentCapabilities


@dataclass
class RegisteredAgent:
    """
    Mutable entity representing a registered agent in the system.

    Unlike Value Objects, this entity has a lifecycle and can be modified.
    It combines identity, capabilities, and operational state.

    Required fields for agent creation:
        - name (via agent_identity)
        - id (via agent_identity)
        - description (via agent_capabilities)
        - authorized_tools (via agent_capabilities)
        - system_prompt

    Attributes:
        agent_identity: Immutable identity of the agent
        agent_capabilities: Capabilities and constraints
        system_prompt: System prompt defining agent behavior
        is_active: Whether the agent is currently active
        created_at: When the agent was registered
        updated_at: Last modification timestamp
        metadata: Additional agent metadata
    """

    agent_identity: AgentIdentity
    agent_capabilities: AgentCapabilities
    system_prompt: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Validate registered agent after initialization.

        Raises:
            ValueError: If validation fails
        """
        self._validate_identity()
        self._validate_capabilities()
        self._validate_system_prompt()
        self._validate_timestamps()
        self._validate_metadata()

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

    def _validate_capabilities(self):
        """
        Validate agent capabilities.

        Raises:
            ValueError: If capabilities are invalid
        """
        if not isinstance(self.agent_capabilities, AgentCapabilities):
            raise ValueError(
                f"agent_capabilities must be AgentCapabilities, "
                f"got {type(self.agent_capabilities)}"
            )

    def _validate_system_prompt(self):
        """
        Validate system prompt.

        Raises:
            ValueError: If system prompt is invalid
        """
        if not self.system_prompt:
            raise ValueError("system_prompt cannot be empty")

        if not isinstance(self.system_prompt, str):
            raise ValueError(
                f"system_prompt must be a string, got {type(self.system_prompt)}"
            )

        if len(self.system_prompt) < 10:
            raise ValueError(
                f"system_prompt too short: {len(self.system_prompt)} chars (minimum 10)"
            )

        if len(self.system_prompt) > 5000:
            raise ValueError(
                f"system_prompt too long: {len(self.system_prompt)} chars (maximum 5000)"
            )

    def _validate_timestamps(self):
        """
        Validate timestamp fields.

        Raises:
            ValueError: If timestamps are invalid
        """
        if not isinstance(self.created_at, datetime):
            raise ValueError(
                f"created_at must be datetime, got {type(self.created_at)}"
            )

        if not isinstance(self.updated_at, datetime):
            raise ValueError(
                f"updated_at must be datetime, got {type(self.updated_at)}"
            )

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at cannot be before created_at"
            )

    def _validate_metadata(self):
        """
        Validate metadata.

        Raises:
            ValueError: If metadata is invalid
        """
        if not isinstance(self.metadata, dict):
            raise ValueError(
                f"metadata must be a dict, got {type(self.metadata)}"
            )

    @classmethod
    def create_new(
        cls,
        name: str,
        description: str,
        authorized_tools: list,
        system_prompt: str,
        max_reasoning_turns: int = 10,
        max_memory_turns: int = 10,
        specialization_tags: Optional[list] = None,
        llm_temperature: float = 0.7,
        llm_max_tokens: int = 1000,
        llm_timeout: int = 30,
        llm_response_format: str = "default",
        is_active: bool = True
    ) -> 'RegisteredAgent':
        """
        Factory method to create a new registered agent.

        All required fields must be provided:
        - name: Agent name
        - description: Brief description of agent's role
        - authorized_tools: List of tool IDs the agent can use
        - system_prompt: System prompt defining behavior

        Args:
            name: Unique agent name
            description: Brief description of agent role
            authorized_tools: List of authorized tool IDs
            system_prompt: System prompt for the agent
            max_reasoning_turns: Maximum reasoning iterations (default 10)
            max_memory_turns: Maximum memory turns (default 10)
            specialization_tags: Optional specialization tags

        Returns:
            New RegisteredAgent instance

        Example:
            agent = RegisteredAgent.create_new(
                name="CodeAgent",
                description="Specialized in code analysis and generation",
                authorized_tools=["read_file", "write_file", "execute_command"],
                system_prompt="You are a code analysis assistant..."
            )
        """
        identity = AgentIdentity.create_new(agent_name=name)

        capabilities = AgentCapabilities(
            description=description,
            system_prompt=system_prompt,
            authorized_tools=authorized_tools,
            max_reasoning_turns=max_reasoning_turns,
            max_memory_turns=max_memory_turns,
            specialization_tags=specialization_tags or [],
            llm_temperature=llm_temperature,
            llm_max_tokens=llm_max_tokens,
            llm_timeout=llm_timeout,
            llm_response_format=llm_response_format
        )

        return RegisteredAgent(
            agent_identity=identity,
            agent_capabilities=capabilities,
            system_prompt=system_prompt,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )

    def update_capabilities(self, new_capabilities: AgentCapabilities):
        """
        Update agent capabilities.

        Args:
            new_capabilities: New capabilities to set

        Raises:
            ValueError: If capabilities are invalid
        """
        if not isinstance(new_capabilities, AgentCapabilities):
            raise ValueError(
                f"new_capabilities must be AgentCapabilities, got {type(new_capabilities)}"
            )

        self.agent_capabilities = new_capabilities
        self.updated_at = datetime.now()

    def update_system_prompt(self, new_prompt: str):
        """
        Update system prompt.

        Args:
            new_prompt: New system prompt

        Raises:
            ValueError: If prompt is invalid
        """
        if not new_prompt or not isinstance(new_prompt, str):
            raise ValueError("new_prompt must be a non-empty string")

        if len(new_prompt) < 10:
            raise ValueError(
                f"new_prompt too short: {len(new_prompt)} chars (minimum 10)"
            )

        if len(new_prompt) > 5000:
            raise ValueError(
                f"new_prompt too long: {len(new_prompt)} chars (maximum 5000)"
            )

        self.system_prompt = new_prompt
        self.updated_at = datetime.now()

    def activate(self):
        """
        Activate the agent.

        Makes the agent available for execution.
        """
        self.is_active = True
        self.updated_at = datetime.now()

    def deactivate(self):
        """
        Deactivate the agent.

        Prevents the agent from being executed.
        """
        self.is_active = False
        self.updated_at = datetime.now()

    def update_metadata(self, key: str, value: any):
        """
        Update a metadata key-value pair.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def get_agent_id(self) -> str:
        """
        Get the agent's unique ID.

        Returns:
            Agent ID string
        """
        return self.agent_identity.agent_id

    def get_agent_name(self) -> str:
        """
        Get the agent's name.

        Returns:
            Agent name string
        """
        return self.agent_identity.agent_name

    def get_description(self) -> str:
        """
        Get the agent's description.

        Returns:
            Description string
        """
        return self.agent_capabilities.description

    def get_authorized_tools(self) -> list:
        """
        Get list of authorized tools.

        Returns:
            List of tool IDs
        """
        return self.agent_capabilities.authorized_tools

    def can_use_tool(self, tool_id: str) -> bool:
        """
        Check if agent can use a specific tool.

        Args:
            tool_id: Tool identifier

        Returns:
            True if authorized, False otherwise
        """
        return self.agent_capabilities.can_use_tool(tool_id)

    def __str__(self) -> str:
        """String representation for logging."""
        status = "active" if self.is_active else "inactive"
        return (
            f"RegisteredAgent(name={self.agent_identity.agent_name}, "
            f"status={status})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"RegisteredAgent("
            f"id={self.agent_identity.agent_id}, "
            f"name={self.agent_identity.agent_name}, "
            f"tools={len(self.agent_capabilities.authorized_tools)}, "
            f"active={self.is_active}, "
            f"created={self.created_at.isoformat()})"
        )
