"""
Service Layer Types

Data types for agent execution services.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from agents.types import AgentOutput


@dataclass
class ExecutionOptions:
    """
    Options for agent execution.

    Attributes:
        timeout_seconds: Maximum execution time in seconds
        enable_cross_agent_context: Whether to include context from other agents
        cross_agent_ids: List of agent IDs to include in context
        max_cross_agent_turns: Maximum turns to retrieve per agent
        include_metrics: Whether to collect detailed metrics
        metadata: Additional execution metadata
    """

    timeout_seconds: Optional[int] = None
    enable_cross_agent_context: bool = False
    cross_agent_ids: list = field(default_factory=list)
    max_cross_agent_turns: int = 5
    include_metrics: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate execution options."""
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        if self.max_cross_agent_turns <= 0:
            raise ValueError("max_cross_agent_turns must be positive")


@dataclass
class AgentExecutionResult:
    """
    Result of agent execution with metrics and traceability.

    Attributes:
        agent_id: ID of the executed agent
        agent_name: Name of the executed agent
        output: Agent output (response, success, error)
        execution_time_seconds: Time taken to execute
        success: Whether execution was successful
        error: Error message if execution failed
        timestamp: When execution completed
        metadata: Additional execution metadata
    """

    agent_id: str
    agent_name: str
    output: AgentOutput
    execution_time_seconds: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate execution result."""
        if self.execution_time_seconds < 0:
            raise ValueError("execution_time_seconds cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'output': {
                'response': self.output.response,
                'success': self.output.success,
                'error': self.output.error
            },
            'execution_time_seconds': self.execution_time_seconds,
            'success': self.success,
            'error': self.error,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    def __str__(self) -> str:
        """String representation for logging."""
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"AgentExecutionResult("
            f"agent={self.agent_name}, "
            f"status={status}, "
            f"time={self.execution_time_seconds:.3f}s)"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"AgentExecutionResult("
            f"agent_id='{self.agent_id}', "
            f"agent_name='{self.agent_name}', "
            f"success={self.success}, "
            f"execution_time={self.execution_time_seconds:.3f}s, "
            f"timestamp='{self.timestamp.isoformat()}')"
        )


class AgentNotFoundError(Exception):
    """Exception raised when agent is not found."""
    pass


class AgentInactiveError(Exception):
    """Exception raised when agent is inactive."""
    pass


class AgentExecutionError(Exception):
    """Exception raised during agent execution."""
    pass
