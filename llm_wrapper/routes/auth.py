"""
Authentication route for the LLM wrapper.
"""
import requests
from ..errors import LLMWrapperError
from core.logger import logger

def authenticate(self) -> None:
    """
    Authenticate and retrieve JWT token.

    Raises:
        LLMWrapperError: Authentication failed
    """
    # Skip if authentication is disabled (e.g. for standard OpenAI/DeepSeek usage)
    if not self.config.auth_enabled:
        return

    if self.token:
        return

    if not self.config.email or not self.config.password:
        return

    url = f"{self.config.base_url}/{self.config.auth_service}"
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
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            raise LLMWrapperError("Authentication failed: No token in response")

    except requests.RequestException as error:
        raise LLMWrapperError(f"Authentication failed: {error}")
