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
    if self.token:
        return

    if not self.config.email or not self.config.password:
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
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            raise LLMWrapperError("Authentication failed: No token in response")

    except requests.RequestException as error:
        raise LLMWrapperError(f"Authentication failed: {error}")
