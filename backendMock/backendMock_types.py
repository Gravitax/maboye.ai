"""
Type definitions for Backend Mock API.

OpenAI-compatible Pydantic models for request and response validation.
"""

from typing import List, Literal, Optional
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
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=None, ge=1)
    max_tokens: int = Field(default=1000, ge=1)
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    stream: bool = Field(default=False)
    seed: Optional[int] = None
    stop: Optional[List[str]] = None


class BackendMockPayloadRequest(BaseModel):
    """Request wrapper with payload field for local API."""
    payload: BackendMockChatRequest


class BackendMockUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class BackendMockChatChoice(BaseModel):
    """Single choice in chat completion format."""
    index: int
    message: BackendMockMessage
    logprobs: Optional[dict] = None
    finish_reason: str
    stop_reason: Optional[str] = None


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


class BackendMockCompletionRequest(BaseModel):
    """Request for text completion."""
    model: str
    prompt: str
    max_tokens: int = Field(default=128, ge=1)
    temperature: float = Field(default=0.5, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(default=-1)
    n: int = Field(default=1, ge=1)
    stream: bool = Field(default=False)
    logprobs: Optional[int] = None
    echo: bool = Field(default=False)
    stop: Optional[List[str]] = None


class BackendMockCompletionChoice(BaseModel):
    """Single choice in text completion format."""
    text: str
    index: int
    logprobs: Optional[dict] = None
    finish_reason: str


class BackendMockCompletionResponse(BaseModel):
    """Response from text completion."""
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[BackendMockCompletionChoice]
    usage: BackendMockUsage


class OllamaGenerateRequest(BaseModel):
    """Request for Ollama generate endpoint."""
    model: str
    prompt: str
    stream: bool = False


class OllamaGenerateResponse(BaseModel):
    """Response from Ollama generate endpoint."""
    model: str
    created_at: str
    response: str
    done: bool


class OllamaEmbedRequest(BaseModel):
    """Request for Ollama embed endpoint."""
    model: str
    input: List[str]


class OllamaEmbedResponse(BaseModel):
    """Response from Ollama embed endpoint."""
    embeddings: List[List[float]]


class OllamaTagsResponse(BaseModel):
    """Response from Ollama tags endpoint."""
    models: List[dict] = []


class EmbeddingRequest(BaseModel):
    """Request for embedding generation."""
    model: str
    input: List[str]
    encoding_format: str = "float"


class EmbeddingData(BaseModel):
    """Embedding data object."""
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    """Response from embedding endpoint."""
    object: str = "list"
    data: List[EmbeddingData]
    model: str


class EmbedV1ModelsResponse(BaseModel):
    """Response with list of embedding models."""
    object: str = "list"
    data: List[dict]


class SignInRequest(BaseModel):
    """Request for user sign-in."""
    email: str
    password: str


class User(BaseModel):
    """User information."""
    id: str
    email: str


class SignInResponse(BaseModel):
    """Response for user sign-in."""
    token: str
    user: User
