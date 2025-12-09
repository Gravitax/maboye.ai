"""
Type definitions for LLM interactions.

Provides simplified Pydantic models for LLM request and response validation.
"""

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMToolCall(BaseModel):
    """Tool call in message."""
    id: str
    type: str = "function"
    function: Dict[str, Any]


class LLMMessage(BaseModel):
    """Single message in conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[LLMToolCall]] = None
    tool_call_id: Optional[str] = None


class LLMChatRequest(BaseModel):
    """Request for chat completion."""
    model: str
    messages: List[LLMMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1)


class LLMUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMChatChoice(BaseModel):
    """Single choice in OpenAI format."""
    index: int
    message: LLMMessage
    finish_reason: str


class LLMChatResponse(BaseModel):
    """Response from chat completion in OpenAI format."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[LLMChatChoice]
    usage: LLMUsage


class LLMModel(BaseModel):
    """Model information."""
    id: str
    object: str = "model"
    created: int
    owned_by: str


class LLMModelsResponse(BaseModel):
    """Response with list of models."""
    object: str = "list"
    data: List[LLMModel]
