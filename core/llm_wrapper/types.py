"""
Simplified Type Definitions for LLM Interactions

Contains only essential types for LLM communication.
"""

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """Tool call in message."""
    id: str
    type: str = "function"
    function: Dict[str, Any]


class Message(BaseModel):
    """Single message in conversation."""
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for chat completion - Essential fields only."""
    model: str
    messages: List[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1)
    response_format: Optional[Dict[str, str]] = None


class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    """Single choice in chat completion."""
    index: int
    message: Message
    finish_reason: str
    logprobs: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response from chat completion."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage


class Model(BaseModel):
    """Model information."""
    id: str
    object: str = "model"
    created: Optional[int] = None
    owned_by: Optional[str] = None


class ModelsResponse(BaseModel):
    """Response with list of models."""
    object: str = "list"
    data: List[Model]


class EmbeddingRequest(BaseModel):
    """Request for embedding."""
    model: str
    input: List[str]
    encoding_format: str = "float"


class EmbeddingData(BaseModel):
    """Embedding data."""
    object: str
    index: int
    embedding: List[float]


class EmbeddingResponse(BaseModel):
    """Response from embedding."""
    object: str
    data: List[EmbeddingData]
    model: str
    usage: Optional[Usage] = None
