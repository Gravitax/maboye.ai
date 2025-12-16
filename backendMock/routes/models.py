"""
Models routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException
import time

from core.logger import logger
from backendMock.backendMock_types import (
    BackendMockModel,
    BackendMockModelsResponse,
)

router = APIRouter()

_request_count_models: int = 0 # Local request count for models

def list_models() -> BackendMockModelsResponse:
    """
    List available models.

    Returns:
        List of available models
    """
    global _request_count_models
    _request_count_models += 1
    logger.info("BACKEND_MOCK", "Models list requested", {
        "request_number": _request_count_models
    })

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

@router.get("/v1/models", response_model=BackendMockModelsResponse, tags=["OpenAI"])
def list_models_endpoint():
    """
    List available models.

    Returns:
        List of available models
    """
    try:
        return list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/api/v1/models", response_model=BackendMockModelsResponse, tags=["Local API - Global"])
def api_v1_list_models():
    """List available models via global API."""
    try:
        return list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/chat/v1/models", response_model=BackendMockModelsResponse, tags=["Local API - Chat"])
def chat_v1_list_models():
    """List available models via chat service."""
    try:
        return list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/code/v1/models", response_model=BackendMockModelsResponse, tags=["Local API - Code"])
def code_v1_list_models():
    """List available models via code service."""
    try:
        return list_models()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Models error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))