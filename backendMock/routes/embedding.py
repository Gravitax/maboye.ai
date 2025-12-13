"""
Embedding routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException
import time # Added for time.time()
from datetime import datetime # Added for datetime.now()
from typing import List # Added for List
import random # Added for random.uniform

from core.logger import logger
from backendMock.backendMock_types import (
    EmbeddingRequest,
    EmbeddingData,
    EmbeddingResponse,
    EmbedV1ModelsResponse,
)
# The BackendMock and its dependencies are no longer used here
# from backendMock.core_mock import BackendMock
# from backendMock.dependencies import get_backend_mock_dependency

router = APIRouter()

def _generate_mock_embedding() -> List[float]:
    """Generate mock embedding vector."""
    return [random.uniform(-1.0, 1.0) for _ in range(384)]

_request_count_embedding: int = 0 # Local request count for embedding

def generate_embeddings(request: EmbeddingRequest) -> EmbeddingResponse:
    """
    Generate embeddings.

    Args:
        request: Embedding request

    Returns:
        Embedding response
    """
    global _request_count_embedding
    _request_count_embedding += 1

    logger.info("BACKEND_MOCK", "Embedding request received", {
        "model": request.model,
        "input_count": len(request.input),
        "encoding_format": request.encoding_format,
        "request_number": _request_count_embedding
    })

    embedding_data = []
    for i, text in enumerate(request.input):
        mock_embedding = _generate_mock_embedding()
        embedding_data.append(
            EmbeddingData(
                object="embedding",
                embedding=mock_embedding,
                index=i
            )
        )

    return EmbeddingResponse(
        object="list",
        data=embedding_data,
        model=request.model
    )

def list_embedding_models() -> EmbedV1ModelsResponse:
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

@router.get("/embed/v1/models", response_model=EmbedV1ModelsResponse, tags=["Embedding"])
def embed_v1_list_models(): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """List available embedding models."""
    try:
        return list_embedding_models() # Call the local list_embedding_models function
    except Exception as error:
        logger.error("BACKEND_MOCK", "Embed models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/embed/v1/embeddings", response_model=EmbeddingResponse, tags=["Embedding"])
def embed_v1_embeddings(request: EmbeddingRequest): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """Generate embeddings via embed service."""
    try:
        logger.info("BACKEND_MOCK", "Received embedding request", {"request": request.model_dump()})
        return generate_embeddings(request) # Call the local generate_embeddings function
    except Exception as error:
        logger.error("BACKEND_MOCK", "Embed error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))