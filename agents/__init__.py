"""
Agent system for LLM-powered workflows

This package provides a modular agent architecture with clean separation of concerns.

Note: To avoid circular imports, BaseAgent and DefaultAgent are not imported by default.
Import them explicitly when needed:
    from agents.base_agent import BaseAgent, AgentError
    from agents.default_agent import DefaultAgent
"""

from agents.config import AgentConfig
from agents.types import (
    AgentInput,
    AgentOutput,
    Message,
    ToolCall,
    ToolResult
)

__all__ = [
    # Configuration
    "AgentConfig",
    # Types
    "AgentInput",
    "AgentOutput",
    "Message",
    "ToolCall",
    "ToolResult",
]

__version__ = "2.0.0"
