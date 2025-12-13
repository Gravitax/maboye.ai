"""
Authentication routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException, Depends # Removed Depends for now
import time # Added for time.time()
from datetime import datetime # Added for datetime.now()
from typing import List # Added for List

from core.logger import logger
from backendMock.backendMock_types import (
    SignInRequest,
    SignInResponse,
    User,
)
# We no longer need BackendMock or get_backend_mock_dependency here
# from backendMock.core_mock import BackendMock
# from backendMock.dependencies import get_backend_mock_dependency

router = APIRouter()

def sign_in(request: SignInRequest) -> SignInResponse:
    """
    Simulate user sign-in and generate a mock JWT token.

    Args:
        request: Sign-in request with email and password.

    Returns:
        A response containing a mock token and user info.
    """
    # request_count is handled by main BackendMock instance, so we can't directly increment it here
    # For now, let's just log the request
    logger.info("BACKEND_MOCK", "Sign-in attempt received", {
        "email": request.email,
        # "request_number": self.request_count # Cannot access self.request_count here
    })

    # In a real application, you would validate credentials here
    mock_token = f"mock-jwt-token-for-{request.email}-{int(time.time())}"
    
    return SignInResponse(
        token=mock_token,
        user=User(id=f"user-mock-{request.email}", email=request.email) # Changed ID to be unique per email
    )

@router.post("/api/v1/auths/signin", response_model=SignInResponse, tags=["Local API - Auth"])
def api_v1_signin(request: SignInRequest): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """Authenticate user and return a token."""
    try:
        return sign_in(request) # Call the local sign_in function
    except Exception as error:
        logger.error("BACKEND_MOCK", "Sign-in error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))