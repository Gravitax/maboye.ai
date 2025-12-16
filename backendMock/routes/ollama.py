"""
Ollama routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List
import random

from core.logger import logger
from backendMock.backendMock_types import (
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OllamaEmbedRequest,
    OllamaEmbedResponse,
    OllamaTagsResponse,
)

router = APIRouter()

def _generate_mock_embedding() -> List[float]:
    """Generate mock embedding vector."""
    return [random.uniform(-1.0, 1.0) for _ in range(384)]

_request_count_ollama: int = 0 # Local request count for ollama

def generate_ollama_completion(request: OllamaGenerateRequest) -> OllamaGenerateResponse:
    """
    Generate Ollama completion.

    Args:
        request: Ollama generate request

    Returns:
        Ollama completion response
    """
    global _request_count_ollama
    _request_count_ollama += 1

    logger.info("BACKEND_MOCK", "Ollama generate request received", {
        "model": request.model,
        "prompt_length": len(request.prompt),
        "stream": request.stream,
        "request_number": _request_count_ollama
    })

    response_text = f"Mock Ollama response to: {request.prompt}"

    return OllamaGenerateResponse(
        model=request.model,
        created_at=datetime.now().isoformat(),
        response=response_text,
        done=True
    )

def generate_ollama_embeddings(request: OllamaEmbedRequest) -> OllamaEmbedResponse:
    """
    Generate Ollama embeddings.

    Args:
        request: Ollama embed request

    Returns:
        Ollama embeddings response
    """
    global _request_count_ollama
    _request_count_ollama += 1

    logger.info("BACKEND_MOCK", "Ollama embed request received", {
        "model": request.model,
        "input_count": len(request.input),
        "request_number": _request_count_ollama
    })

    embeddings = []
    for _ in request.input:
        mock_embedding = _generate_mock_embedding()
        embeddings.append(mock_embedding)

    return OllamaEmbedResponse(
        embeddings=embeddings
    )

def list_ollama_models() -> OllamaTagsResponse:
    """
    List Ollama models.

    Returns:
        Ollama tags response
    """
    logger.info("BACKEND_MOCK", "Ollama tags list requested")

    return OllamaTagsResponse(models=[])


@router.get("/ollama/api/tags", response_model=OllamaTagsResponse, tags=["Ollama"])
def ollama_list_tags():
    """List available Ollama models."""
    try:
        return list_ollama_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Ollama tags error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/ollama/api/generate", response_model=OllamaGenerateResponse, tags=["Ollama"])
def ollama_generate(request: OllamaGenerateRequest):
    """Generate completion via Ollama API."""
    try:
        return generate_ollama_completion(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Ollama generate error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/ollama/api/embed", response_model=OllamaEmbedResponse, tags=["Ollama"])
def ollama_embed(request: OllamaEmbedRequest):
    """Generate embeddings via Ollama API."""
    try:
        return generate_ollama_embeddings(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Ollama embed error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))