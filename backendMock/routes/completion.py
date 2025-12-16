"""
Completion routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException
import time
from core.logger import logger
from backendMock.backendMock_types import (
    BackendMockCompletionRequest,
    BackendMockCompletionResponse,
    BackendMockCompletionChoice,
    BackendMockUsage,
)

router = APIRouter()

_request_count_completion: int = 0 # Local request count for completion

def _calculate_usage(prompt: str, response: str) -> BackendMockUsage:
    """Calculate token usage for request and response."""
    prompt_tokens = len(prompt.split())
    completion_tokens = len(response.split())

    return BackendMockUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens
    )

def generate_text_completion(request: BackendMockCompletionRequest) -> BackendMockCompletionResponse:
    """
    Generate mock text completion.

    Args:
        request: Text completion request

    Returns:
        Mock text completion response
    """
    global _request_count_completion
    _request_count_completion += 1

    logger.info("BACKEND_MOCK", "Text completion request received", {
        "model": request.model,
        "prompt_length": len(request.prompt),
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "stream": request.stream,
        "request_number": _request_count_completion
    })

    response_text = f"Mock completion for prompt: {request.prompt[:50]}..."
    usage = _calculate_usage(request.prompt, response_text)

    return BackendMockCompletionResponse(
        id=f"cmpl-mock-{_request_count_completion}",
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

@router.post("/api/v1/completions", response_model=BackendMockCompletionResponse, tags=["Local API - Global"])
def api_v1_completions(request: BackendMockCompletionRequest):
    """Create text completion via global API."""
    try:
        return generate_text_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Completions error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/chat/v1/completions", response_model=BackendMockCompletionResponse, tags=["Local API - Chat"])
def chat_v1_completions(request: BackendMockCompletionRequest):
    """Create text completion via chat service."""
    try:
        return generate_text_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Completions error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/code/v1/completions", response_model=BackendMockCompletionResponse, tags=["Local API - Code"])
def code_v1_completions(request: BackendMockCompletionRequest):
    """Create text completion via code service."""
    try:
        return generate_text_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Completions error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))