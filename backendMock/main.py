"""
Backend Mock API.

Mock implementation of LLM API for testing and development.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent

load_dotenv(backend_dir / ".env")

sys.path.insert(0, str(project_root))
from core.logger import logger
from typing import List

from backendMock.backendMock_types import (
    BackendMockMessage,
    BackendMockChatRequest,
    BackendMockChatResponse,
    BackendMockChatChoice,
    BackendMockUsage,
    BackendMockModel,
    BackendMockModelsResponse,
    BackendMockCompletionRequest,
    BackendMockCompletionResponse,
    BackendMockCompletionChoice,
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OllamaEmbedRequest,
    OllamaEmbedResponse,
    OllamaTagsResponse,
    EmbeddingRequest,
    EmbeddingData,
    EmbeddingResponse,
    EmbedV1ModelsResponse,
    SignInRequest,
    SignInResponse,
    User,
)


def get_env_variable(key: str, default: str) -> str:
    """Get environment variable with default value."""
    return os.getenv(key, default)


class BackendMock:
    """Mock backend for LLM API."""

    def __init__(self):
        self.request_count = 0
        logger.info("BACKEND_MOCK", "Initialized")

    def sign_in(self, request: SignInRequest) -> SignInResponse:
        """
        Simulate user sign-in and generate a mock JWT token.

        Args:
            request: Sign-in request with email and password.

        Returns:
            A response containing a mock token and user info.
        """
        self.request_count += 1
        logger.info("BACKEND_MOCK", "Sign-in attempt received", {
            "email": request.email,
            "request_number": self.request_count
        })

        # In a real application, you would validate credentials here
        mock_token = f"mock-jwt-token-for-{request.email}-{int(time.time())}"
        
        return SignInResponse(
            token=mock_token,
            user=User(id=f"user-mock-{self.request_count}", email=request.email)
        )

    def generate_chat_response(self, request: BackendMockChatRequest) -> BackendMockChatResponse:
        """
        Generate mock chat response.

        Args:
            request: Chat completion request

        Returns:
            Mock chat response in chat completion format
        """
        self.request_count += 1

        logger.info("BACKEND_MOCK", "Chat request received", {
            "model": request.model,
            "messages_count": len(request.messages),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
            "request_number": self.request_count
        })

        response_text = self._create_response_text(request.messages)
        usage = self._calculate_usage(request.messages, response_text)

        return BackendMockChatResponse(
            id=f"cmpl-mock-{self.request_count}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                BackendMockChatChoice(
                    index=0,
                    message=BackendMockMessage(role="assistant", content=response_text),
                    logprobs=None,
                    finish_reason="stop",
                    stop_reason=None
                )
            ],
            usage=usage
        )

    def generate_text_completion(self, request: BackendMockCompletionRequest) -> BackendMockCompletionResponse:
        """
        Generate mock text completion.

        Args:
            request: Text completion request

        Returns:
            Mock text completion response
        """
        self.request_count += 1

        logger.info("BACKEND_MOCK", "Text completion request received", {
            "model": request.model,
            "prompt_length": len(request.prompt),
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
            "request_number": self.request_count
        })

        response_text = f"Mock completion for prompt: {request.prompt[:50]}..."
        prompt_tokens = len(request.prompt.split())
        completion_tokens = len(response_text.split())

        usage = BackendMockUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )

        return BackendMockCompletionResponse(
            id=f"cmpl-mock-{self.request_count}",
            object="text_completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                BackendMockCompletionChoice(
                    text=response_text,
                    index=0,
                    logprobs=None,
                    finish_reason="stop"
                )
            ],
            usage=usage
        )

    def list_models(self) -> BackendMockModelsResponse:
        """
        List available models.

        Returns:
            List of available models
        """
        logger.info("BACKEND_MOCK", "Models list requested")

        models = [
            BackendMockModel(
                id="gpt-4",
                object="model",
                created=int(time.time()),
                owned_by="openai-mock"
            ),
            BackendMockModel(
                id="gpt-3.5-turbo",
                object="model",
                created=int(time.time()),
                owned_by="openai-mock"
            ),
            BackendMockModel(
                id="text-davinci-003",
                object="model",
                created=int(time.time()),
                owned_by="openai-mock"
            )
        ]

        return BackendMockModelsResponse(object="list", data=models)

    def get_health_status(self) -> dict:
        """
        Get detailed health status.

        Returns:
            Health status information
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "requests_processed": self.request_count
        }

    def _create_response_text(self, messages: List[BackendMockMessage]) -> str:
        """Create mock response text based on last message."""
        last_message = messages[-1].content if messages else ""
        return f"Mock response to: {last_message}"

    def _calculate_usage(self, messages: List[BackendMockMessage], response: str) -> BackendMockUsage:
        """Calculate token usage for request and response."""
        prompt_tokens = sum(len(msg.content.split()) for msg in messages)
        completion_tokens = len(response.split())

        return BackendMockUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )

    def generate_ollama_completion(self, request: OllamaGenerateRequest) -> OllamaGenerateResponse:
        """
        Generate Ollama completion.

        Args:
            request: Ollama generate request

        Returns:
            Ollama completion response
        """
        self.request_count += 1

        logger.info("BACKEND_MOCK", "Ollama generate request received", {
            "model": request.model,
            "prompt_length": len(request.prompt),
            "stream": request.stream,
            "request_number": self.request_count
        })

        response_text = f"Mock Ollama response to: {request.prompt}"

        return OllamaGenerateResponse(
            model=request.model,
            created_at=datetime.now().isoformat(),
            response=response_text,
            done=True
        )

    def generate_ollama_embeddings(self, request: OllamaEmbedRequest) -> OllamaEmbedResponse:
        """
        Generate Ollama embeddings.

        Args:
            request: Ollama embed request

        Returns:
            Ollama embeddings response
        """
        self.request_count += 1

        logger.info("BACKEND_MOCK", "Ollama embed request received", {
            "model": request.model,
            "input_length": len(request.input),
            "request_number": self.request_count
        })

        mock_embedding = self._generate_mock_embedding()

        return OllamaEmbedResponse(
            embeddings=[mock_embedding]
        )

    def list_ollama_models(self) -> OllamaTagsResponse:
        """
        List Ollama models.

        Returns:
            Ollama tags response
        """
        logger.info("BACKEND_MOCK", "Ollama tags list requested")

        return OllamaTagsResponse(models=[])

    def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """
        Generate embeddings.

        Args:
            request: Embedding request

        Returns:
            Embedding response
        """
        self.request_count += 1

        logger.info("BACKEND_MOCK", "Embedding request received", {
            "model": request.model,
            "input_length": len(request.input),
            "encoding_format": request.encoding_format,
            "request_number": self.request_count
        })

        mock_embedding = self._generate_mock_embedding()

        return EmbeddingResponse(
            object="list",
            data=[
                EmbeddingData(
                    object="embedding",
                    embedding=mock_embedding,
                    index=0
                )
            ],
            model=request.model
        )

    def list_embedding_models(self) -> EmbedV1ModelsResponse:
        """
        List embedding models.

        Returns:
            Embedding models response
        """
        logger.info("BACKEND_MOCK", "Embedding models list requested")

        return EmbedV1ModelsResponse(
            object="list",
            data=[
                {"id": "all-MiniLM-L6-v2"},
                {"id": "bge-small-en-v1.5"}
            ]
        )

    def _generate_mock_embedding(self) -> List[float]:
        """Generate mock embedding vector."""
        import random
        return [random.uniform(-1.0, 1.0) for _ in range(384)]


app = FastAPI(
    title="Backend Mock API",
    description="Mock LLM API for testing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend_mock = BackendMock()


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Backend Mock API running",
        "version": "1.0.0",
        "endpoints": {
            "health": [
                "GET  /health"
            ],
            "openai_compatible": [
                "POST /v1/chat/completions",
                "GET  /v1/models"
            ],
            "local_api_global": [
                "GET  /api/v1/models",
                "POST /api/v1/chat/completions",
                "POST /api/v1/completions"
            ],
            "local_api_chat": [
                "GET  /chat/v1/models",
                "POST /chat/v1/chat/completions",
                "POST /chat/v1/completions"
            ],
            "local_api_code": [
                "GET  /code/v1/models",
                "POST /code/v1/chat/completions",
                "POST /code/v1/completions"
            ],
            "ollama": [
                "GET  /ollama/api/tags",
                "POST /ollama/api/generate",
                "POST /ollama/api/embed"
            ],
            "embedding": [
                "GET  /embed/v1/models",
                "POST /embed/v1/embeddings"
            ]
        }
    }


@app.get("/health", tags=["Health"])
def health():
    """Detailed health status."""
    return backend_mock.get_health_status()


@app.post("/v1/chat/completions", response_model=BackendMockChatResponse, tags=["OpenAI"])
def chat_completions(request: BackendMockChatRequest):
    """
    Create chat completion.

    Args:
        request: Chat completion request

    Returns:
        Chat completion response in OpenAI format
    """
    try:
        return backend_mock.generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/v1/models", response_model=BackendMockModelsResponse, tags=["OpenAI"])
def list_models():
    """
    List available models.

    Returns:
        List of available models
    """
    try:
        return backend_mock.list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/api/v1/models", response_model=BackendMockModelsResponse, tags=["Local API - Global"])
def api_v1_list_models():
    """List available models via global API."""
    try:
        return backend_mock.list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/v1/auths/signin", response_model=SignInResponse, tags=["Local API - Auth"])
def api_v1_signin(request: SignInRequest):
    """Authenticate user and return a token."""
    try:
        return backend_mock.sign_in(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Sign-in error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/v1/chat/completions", response_model=BackendMockChatResponse, tags=["Local API - Global"])
def api_v1_chat_completions(request: BackendMockChatRequest):
    """Create chat completion via global API."""
    try:
        return backend_mock.generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/api/v1/completions", response_model=BackendMockCompletionResponse, tags=["Local API - Global"])
def api_v1_completions(request: BackendMockCompletionRequest):
    """Create text completion via global API."""
    try:
        return backend_mock.generate_text_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Completions error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/chat/v1/models", response_model=BackendMockModelsResponse, tags=["Local API - Chat"])
def chat_v1_list_models():
    """List available models via chat service."""
    try:
        return backend_mock.list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/chat/v1/chat/completions", response_model=BackendMockChatResponse, tags=["Local API - Chat"])
def chat_v1_chat_completions(request: BackendMockChatRequest):
    """Create chat completion via chat service."""
    try:
        return backend_mock.generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/chat/v1/completions", response_model=BackendMockCompletionResponse, tags=["Local API - Chat"])
def chat_v1_completions(request: BackendMockCompletionRequest):
    """Create text completion via chat service."""
    try:
        return backend_mock.generate_text_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Completions error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/code/v1/models", response_model=BackendMockModelsResponse, tags=["Local API - Code"])
def code_v1_list_models():
    """List available models via code service."""
    try:
        return backend_mock.list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/code/v1/chat/completions", response_model=BackendMockChatResponse, tags=["Local API - Code"])
def code_v1_chat_completions(request: BackendMockChatRequest):
    """Create chat completion via code service."""
    try:
        return backend_mock.generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/code/v1/completions", response_model=BackendMockCompletionResponse, tags=["Local API - Code"])
def code_v1_completions(request: BackendMockCompletionRequest):
    """Create text completion via code service."""
    try:
        return backend_mock.generate_text_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Completions error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/ollama/api/tags", response_model=OllamaTagsResponse, tags=["Ollama"])
def ollama_list_tags():
    """List available Ollama models."""
    try:
        return backend_mock.list_ollama_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Ollama tags error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/ollama/api/generate", response_model=OllamaGenerateResponse, tags=["Ollama"])
def ollama_generate(request: OllamaGenerateRequest):
    """Generate completion via Ollama API."""
    try:
        return backend_mock.generate_ollama_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Ollama generate error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/ollama/api/embed", response_model=OllamaEmbedResponse, tags=["Ollama"])
def ollama_embed(request: OllamaEmbedRequest):
    """Generate embeddings via Ollama API."""
    try:
        return backend_mock.generate_ollama_embeddings(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Ollama embed error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/embed/v1/models", response_model=EmbedV1ModelsResponse, tags=["Embedding"])
def embed_v1_list_models():
    """List available embedding models."""
    try:
        return backend_mock.list_embedding_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Embed models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/embed/v1/embeddings", response_model=EmbeddingResponse, tags=["Embedding"])
def embed_v1_embeddings(request: EmbeddingRequest):
    """Generate embeddings via embed service."""
    try:
        return backend_mock.generate_embeddings(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Embed error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    host = get_env_variable("BACKEND_MOCK_HOST", "127.0.0.1")
    port = get_env_variable("BACKEND_MOCK_PORT", "8000")
    logger.info("BACKEND_MOCK", "Server started", {"url": f"http://{host}:{port}"})


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    logger.info("BACKEND_MOCK", "Server stopped", {
        "total_requests": backend_mock.request_count
    })


if __name__ == "__main__":
    import uvicorn

    host = get_env_variable("BACKEND_MOCK_HOST", "127.0.0.1")
    port = int(get_env_variable("BACKEND_MOCK_PORT", "8000"))
    log_level = get_env_variable("BACKEND_MOCK_LOG_LEVEL", "warning")

    uvicorn.run(app, host=host, port=port, log_level=log_level)
