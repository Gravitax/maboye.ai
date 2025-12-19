"""
Agent Identity Value Object

Represents the immutable identity of an agent in the system.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar


@dataclass(frozen=True)
class AgentIdentity:
    """
    Immutable identity of an agent.

    Value Object that guarantees uniqueness and integrity.
    Once created, the identity cannot be modified.

    Attributes:
        agent_id: Unique identifier (UUID v4 format)
        agent_name: Human-readable unique name
        creation_timestamp: When the agent was created
    """

    agent_id: str
    agent_name: str
    creation_timestamp: datetime

    # Validation patterns
    _NAME_PATTERN: ClassVar[str] = r'^[a-zA-Z][a-zA-Z0-9_]{2,49}$'
    _MIN_NAME_LENGTH: ClassVar[int] = 3
    _MAX_NAME_LENGTH: ClassVar[int] = 50

    def __post_init__(self):
        """
        Validate identity attributes after initialization.

        Raises:
            ValueError: If validation fails
        """
        self._validate_agent_id()
        self._validate_agent_name()
        self._validate_timestamp()

    def _validate_agent_id(self):
        """
        Validate that agent_id is a valid UUID v4.

        Raises:
            ValueError: If agent_id is not a valid UUID
        """
        if not self.agent_id:
            raise ValueError("agent_id cannot be empty")

        try:
            uuid_obj = uuid.UUID(self.agent_id, version=4)
            if str(uuid_obj) != self.agent_id:
                raise ValueError(f"agent_id must be a valid UUID v4: {self.agent_id}")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid agent_id format: {self.agent_id}") from e

    def _validate_agent_name(self):
        """
        Validate that agent_name follows naming conventions.

        Rules:
        - Must start with a letter
        - Can contain letters, numbers, and underscores
        - Length between 3 and 50 characters
        - Must be unique (enforced by repository)

        Raises:
            ValueError: If agent_name doesn't meet requirements
        """
        if not self.agent_name:
            raise ValueError("agent_name cannot be empty")

        if not isinstance(self.agent_name, str):
            raise ValueError(f"agent_name must be a string, got {type(self.agent_name)}")

        name_length = len(self.agent_name)
        if name_length < self._MIN_NAME_LENGTH:
            raise ValueError(
                f"agent_name too short: {name_length} chars "
                f"(minimum {self._MIN_NAME_LENGTH})"
            )

        if name_length > self._MAX_NAME_LENGTH:
            raise ValueError(
                f"agent_name too long: {name_length} chars "
                f"(maximum {self._MAX_NAME_LENGTH})"
            )

        if not re.match(self._NAME_PATTERN, self.agent_name):
            raise ValueError(
                f"agent_name '{self.agent_name}' must start with a letter "
                "and contain only letters, numbers, and underscores"
            )

    def _validate_timestamp(self):
        """
        Validate creation timestamp.

        Raises:
            ValueError: If timestamp is invalid or in the future
        """
        if not isinstance(self.creation_timestamp, datetime):
            raise ValueError(
                f"creation_timestamp must be datetime, got {type(self.creation_timestamp)}"
            )

        now = datetime.now()
        if self.creation_timestamp > now:
            raise ValueError(
                f"creation_timestamp cannot be in the future: {self.creation_timestamp}"
            )

    @classmethod
    def create_new(cls, agent_name: str) -> 'AgentIdentity':
        """
        Factory method to create a new agent identity with generated UUID.

        Args:
            agent_name: Human-readable name for the agent

        Returns:
            New AgentIdentity instance

        Example:
            identity = AgentIdentity.create_new("CodeAgent")
        """
        return cls(
            agent_id=str(uuid.uuid4()),
            agent_name=agent_name,
            creation_timestamp=datetime.now()
        )
