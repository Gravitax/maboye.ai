"""
Type definitions for agent system

Provides Pydantic models for agent input/output.
Re-exports LLM types for convenience.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Re-export LLM types for convenience
from LLM.types import (
    Message,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    ChatCompletionChoice,
    CompletionChoice,
    Usage,
    Model,
    ModelsResponse
)


class AgentInput(BaseModel):
    """Input data for agent"""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentOutput(BaseModel):
    """Output data from agent"""
    response: str
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None


# Expose all types
__all__ = [
    # Agent types
    "AgentInput",
    "AgentOutput",
    # LLM types (re-exported)
    "Message",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "CompletionRequest",
    "CompletionResponse",
    "ChatCompletionChoice",
    "CompletionChoice",
    "Usage",
    "Model",
    "ModelsResponse",
]
