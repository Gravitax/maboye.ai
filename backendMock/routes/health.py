"""
Health routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime

from core.logger import logger
# We no longer need BackendMock or get_backend_mock_dependency here
# from backendMock.core_mock import BackendMock
# from backendMock.dependencies import get_backend_mock_dependency

router = APIRouter()

_request_count_health: int = 0 # Local request count for health

def get_health_status() -> dict:
    """
    Get detailed health status.

    Returns:
        Health status information
    """
    global _request_count_health
    _request_count_health += 1 # Increment local request count

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "requests_processed": _request_count_health # Use local request count
    }

@router.get("/health", tags=["Health"])
def health_endpoint(): # Renamed to avoid conflict with the function
    """Detailed health status."""
    try:
        return get_health_status() # Call the local get_health_status function
    except Exception as error:
        logger.error("BACKEND_MOCK", "Health error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))

@router.get("/", tags=["Health"])
def root_endpoint(): # Renamed to avoid conflict with the function
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Backend Mock API running",
        "version": "1.0.0",
        "endpoints": {
            "health": [
                "GET  /health"
            ],
            # All other endpoints will be dynamically added by main.py
        }
    }