"""
Health routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from core.logger import logger

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
def health_endpoint():
    """Detailed health status."""
    try:
        return get_health_status()
    except Exception as error:
        logger.error("BACKEND_MOCK", "Health error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))

@router.get("/", tags=["Health"])
def root_endpoint():
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