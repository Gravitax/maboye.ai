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
    BackendMockModelsResponse
)


def get_env_variable(key: str, default: str) -> str:
    """Get environment variable with default value."""
    return os.getenv(key, default)


class BackendMock:
    """Mock backend for LLM API."""

    def __init__(self):
        self.request_count = 0
        logger.info("BACKEND_MOCK", "Initialized")

    def generate_chat_response(self, request: BackendMockChatRequest) -> BackendMockChatResponse:
        """
        Generate mock chat response.

        Args:
            request: Chat completion request

        Returns:
            Mock chat response in OpenAI format
        """
        self.request_count += 1

        logger.info("BACKEND_MOCK", "Chat request received", {
            "model": request.model,
            "messages_count": len(request.messages),
            "request_number": self.request_count
        })

        response_text = self._create_response_text(request.messages)
        usage = self._calculate_usage(request.messages, response_text)

        return BackendMockChatResponse(
            id=f"chatcmpl-mock-{self.request_count}",
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                BackendMockChatChoice(
                    index=0,
                    message=BackendMockMessage(role="assistant", content=response_text),
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
        "endpoints": [
            "POST /v1/chat/completions",
            "GET  /v1/models",
            "GET  /health"
        ]
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
