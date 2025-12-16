"""
Authentication routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException
import time

from core.logger import logger
from backendMock.backendMock_types import (
    SignInRequest,
    SignInResponse,
    User,
)

router = APIRouter()

def sign_in(request: SignInRequest) -> SignInResponse:
    """
    Simulate user sign-in and generate a mock JWT token.

    Args:
        request: Sign-in request with email and password.

    Returns:
        A response containing a mock token and user info.
    """
    logger.info("BACKEND_MOCK", "Sign-in attempt received", {
        "email": request.email
    })

    # In a real application, you would validate credentials here
    mock_token = f"mock-jwt-token-for-{request.email}-{int(time.time())}"
    
    return SignInResponse(
        token=mock_token,
        user=User(id=f"user-mock-{request.email}", email=request.email) # Changed ID to be unique per email
    )

@router.post("/api/v1/auths/signin", response_model=SignInResponse, tags=["Local API - Auth"])
def api_v1_signin(request: SignInRequest):
    """Authenticate user and return a token."""
    try:
        return sign_in(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Sign-in error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))