"""
Chat routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException, Depends
import time # Needed for time.time()
from datetime import datetime # Needed for datetime.now()
from typing import List

from core.logger import logger
from backendMock.backendMock_types import (
    BackendMockMessage,
    BackendMockChatRequest,
    BackendMockChatResponse,
    BackendMockChatChoice,
    BackendMockUsage,
)
# We no longer need BackendMock or get_backend_mock_dependency here
# from backendMock.core_mock import BackendMock
# from backendMock.dependencies import get_backend_mock_dependency

router = APIRouter()

def _create_response_text(messages: List[BackendMockMessage]) -> str:
    """Create mock response text based on last message."""
    last_message = messages[-1].content if messages else ""
    return f"Mock response to: {last_message}"

def _calculate_usage(messages: List[BackendMockMessage], response: str) -> BackendMockUsage:
    """Calculate token usage for request and response."""
    prompt_tokens = sum(len(msg.content.split()) for msg in messages)
    completion_tokens = len(response.split())

    return BackendMockUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )

_request_count_chat: int = 0 # Local request count for chat

def generate_chat_response(request: BackendMockChatRequest) -> BackendMockChatResponse:
    """
    Generate mock chat response.

    Args:
        request: Chat completion request

    Returns:
        Mock chat response in chat completion format
    """
    global _request_count_chat
    _request_count_chat += 1

    logger.info("BACKEND_MOCK", "Chat request received", {
        "model": request.model,
        "messages_count": len(request.messages),
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "stream": request.stream,
        "request_number": _request_count_chat
    })

    response_text = _create_response_text(request.messages)
    usage = _calculate_usage(request.messages, response_text)

    return BackendMockChatResponse(
        id=f"cmpl-mock-{_request_count_chat}",
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

@router.post("/v1/chat/completions", response_model=BackendMockChatResponse, tags=["OpenAI"])
def chat_completions(request: BackendMockChatRequest): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """
    Create chat completion.

    Args:
        request: Chat completion request

    Returns:
        Chat completion response in OpenAI format
    """
    try:
        return generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/api/v1/chat/completions", response_model=BackendMockChatResponse, tags=["Local API - Global"])
def api_v1_chat_completions(request: BackendMockChatRequest): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """Create chat completion via global API."""
    try:
        return generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/chat/v1/chat/completions", response_model=BackendMockChatResponse, tags=["Local API - Chat"])
def chat_v1_chat_completions(request: BackendMockChatRequest): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """Create chat completion via chat service."""
    try:
        return generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/code/v1/chat/completions", response_model=BackendMockChatResponse, tags=["Local API - Code"])
def code_v1_chat_completions(request: BackendMockChatRequest): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """Create chat completion via code service."""
    try:
        return generate_chat_response(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))