"""
Authentication route for the LLM wrapper.
"""
import requests
from ..errors import LLMWrapperError
from ...logger import logger

def authenticate(self) -> None:
    """
    Authenticate and retrieve JWT token.

    Raises:
        LLMWrapperError: Authentication failed
    """
    if self.token:
        return

    if not self.config.email or not self.config.password:
        logger.warning("LLM_WRAPPER", "Missing credentials for authentication")
        return

    url = f"{self.config.base_url}/api/v1/auths/signin"
    payload = {
        "email": self.config.email,
        "password": self.config.password
    }

    try:
        response = self.session.post(url, json=payload, timeout=self.config.timeout)
        response.raise_for_status()
        data = response.json()
        self.token = data.get("token")

        if self.token:
            logger.info("LLM_WRAPPER", "Authentication successful")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            raise LLMWrapperError("Authentication failed: No token in response")

    except requests.RequestException as error:
        logger.error("LLM_WRAPPER", "Authentication request failed", {"error": str(error)})
        raise LLMWrapperError(f"Authentication failed: {error}")
