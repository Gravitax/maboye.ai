"""
Type definitions for Backend Mock API.

OpenAI-compatible Pydantic models for request and response validation.
"""

from typing import List, Literal
from pydantic import BaseModel, Field


class BackendMockMessage(BaseModel):
    """Single message in conversation."""
    role: Literal["system", "user", "assistant"]
    content: str


class BackendMockChatRequest(BaseModel):
    """Request for chat completion."""
    model: str
    messages: List[BackendMockMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1)


class BackendMockUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class BackendMockChatChoice(BaseModel):
    """Single choice in OpenAI format."""
    index: int
    message: BackendMockMessage
    finish_reason: str


class BackendMockChatResponse(BaseModel):
    """Response from chat completion in OpenAI format."""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[BackendMockChatChoice]
    usage: BackendMockUsage


class BackendMockModel(BaseModel):
    """Model information."""
    id: str
    object: str = "model"
    created: int
    owned_by: str


class BackendMockModelsResponse(BaseModel):
    """Response with list of models."""
    object: str = "list"
    data: List[BackendMockModel]
