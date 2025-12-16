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
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1)
    max_tokens: int = Field(default=1000, ge=1)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stream: bool = Field(default=False)
    seed: Optional[int] = None
    stop: Optional[List[str]] = None


class LLMUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMChatChoice(BaseModel):
    """Single choice in chat completion format."""
    index: int
    message: LLMMessage
    logprobs: Optional[Dict[str, Any]] = None
    finish_reason: str
    stop_reason: Optional[str] = None


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
    created: Optional[int] = None
    owned_by: Optional[str] = None


class LLMModelsResponse(BaseModel):
    """Response with list of models."""
    object: str = "list"
    data: List[LLMModel]


class LLMEmbeddingRequest(BaseModel):
    """Request for embedding."""
    model: str
    input: List[str]
    encoding_format: str = "float"


class LLMEmbeddingData(BaseModel):
    """Embedding data."""
    object: str
    index: int
    embedding: List[float]


class LLMEmbeddingResponse(BaseModel):
    """Response from embedding."""
    object: str
    data: List[LLMEmbeddingData]
    model: str
    usage: Optional[LLMUsage] = None


class LLMTestPlanRequest(BaseModel):
    """Request for a test execution plan."""
    test_name: str


class LLMActionStep(BaseModel):
    """Single action to execute"""
    tool_name: str
    arguments: dict
    description: str


class LLMExecutionStep(BaseModel):
    """Step containing one or more actions"""
    step_number: int
    description: str
    actions: List[LLMActionStep]
    depends_on: Optional[int] = None


class LLMTestPlanResponse(BaseModel):
    """Response with a test execution plan."""
    steps: List[LLMExecutionStep]
    role: str = "assistant"
    content: Optional[str] = None
