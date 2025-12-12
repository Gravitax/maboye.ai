"""
Agent system for LLM-powered workflows

This package provides a modular agent architecture with clean separation of concerns.

Note: The new Agent implementation can be imported directly:
    from agents.agent import Agent
"""

from agents.types import (
    AgentInput,
    AgentOutput,
    Message,
    ToolCall,
    ToolResult
)

__all__ = [
    # Types
    "AgentInput",
    "AgentOutput",
    "Message",
    "ToolCall",
    "ToolResult",
]

__version__ = "2.0.0"
