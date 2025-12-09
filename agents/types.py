"""
Type definitions for the agent system.

This module provides structured types for agent inputs, outputs, conversation messages,
and tool interactions, ensuring clear data contracts throughout the agent architecture.
"""

from typing import Optional, Dict, Any, List, Literal, TypedDict
from pydantic import BaseModel, Field

# Re-export LLM types for convenience, though direct use should be minimal in agents.
from core.llm_wrapper.types import (
    LLMMessage as LLMWrapperMessage,
    LLMChatRequest,
    LLMChatResponse,
)


class ToolCall(TypedDict):
    """Represents a tool call requested by the LLM."""
    id: str  # Unique identifier for the tool call
    name: str
    args: Dict[str, Any]


class ToolResult(TypedDict):
    """Represents the result of a tool execution."""
    tool_call_id: str  # The ID of the corresponding tool call
    tool_name: str
    result: str
    success: bool
    execution_time: float


class Message(TypedDict, total=False):
    """
    Represents a single message in the conversation history.
    This structure is flexible to accommodate different message types.
    """
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str]
    tool_calls: Optional[List[ToolCall]]
    tool_call_id: Optional[str] # Used for tool responses


class AgentInput(BaseModel):
    """Input data for an agent, defining the user's request."""
    prompt: str
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Output data from an agent, representing the final response."""
    response: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


# Expose all types for clear imports
__all__ = [
    # Agent-specific types
    "AgentInput",
    "AgentOutput",
    "Message",
    "ToolCall",
    "ToolResult",
    # Re-exported LLM Wrapper types (for core components)
    "LLMWrapperMessage",
    "LLMChatRequest",
    "LLMChatResponse",
]
