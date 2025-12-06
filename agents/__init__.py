"""
Agent system for LLM-powered workflows

Provides base classes and utilities for building agents that interact
with LLM backends.
"""

from agents.agent import Agent, AgentError, AgentInputError, AgentOutputError
from LLM import LLM, LLMError, LLMConnectionError, LLMAPIError, LLMConfig
from agents.config import AgentConfig
from agents.types import (
    AgentInput,
    AgentOutput,
    Message,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    ModelsResponse
)

__all__ = [
    # Core classes
    "Agent",
    "LLM",
    # Configuration
    "AgentConfig",
    "LLMConfig",
    # Types
    "AgentInput",
    "AgentOutput",
    "Message",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "CompletionRequest",
    "CompletionResponse",
    "ModelsResponse",
    # Exceptions
    "AgentError",
    "AgentInputError",
    "AgentOutputError",
    "LLMError",
    "LLMConnectionError",
    "LLMAPIError",
]

__version__ = "1.0.0"
