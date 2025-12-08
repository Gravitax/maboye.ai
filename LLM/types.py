"""
Type definitions for LLM interactions

Provides Pydantic models for LLM request/response validation.
"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Single message in conversation"""
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    """Request for chat completion"""
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class CompletionRequest(BaseModel):
    """Request for text completion"""
    model: str
    prompt: Union[str, List[str]]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    """Single choice in chat completion response"""
    index: int
    message: Message
    finish_reason: str


class CompletionChoice(BaseModel):
    """Single choice in text completion response"""
    index: int
    text: str
    finish_reason: str
    logprobs: Optional[Any] = None


class Usage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response from chat completion"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage


class CompletionResponse(BaseModel):
    """Response from text completion"""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: Usage


class Model(BaseModel):
    """Model information"""
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    """Response with list of models"""
    object: str = "list"
    data: List[Model]
