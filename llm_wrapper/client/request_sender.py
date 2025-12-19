"""
Request Sender

Handles HTTP request sending with error handling.
"""

from typing import Dict, Any
import requests
from core.logger import logger
from ..types import ChatRequest, ChatResponse
from ..errors import LLMWrapperError
from ..config import LLMWrapperConfig


class RequestSender:
    """
    Sends HTTP requests to LLM API with error handling.

    Responsibilities:
    - Send POST/GET requests
    - Handle HTTP errors
    - Handle connection errors
    - Handle timeouts
    """

    def send_chat_request(
        self,
        url: str,
        request: ChatRequest,
        session: requests.Session,
        config: LLMWrapperConfig
    ) -> ChatResponse:
        """
        Send chat request to API endpoint.

        Args:
            url: API endpoint URL
            request: Chat request object
            session: Requests session
            config: LLM configuration

        Returns:
            ChatResponse from API

        Raises:
            LLMWrapperError: If request fails
        """
        try:
            request_payload = request.model_dump(exclude_none=True)

            response = session.post(
                url,
                json=request_payload,
                timeout=config.timeout
            )
            response.raise_for_status()

            data = response.json()
            return ChatResponse(**data)

        except requests.ConnectionError as error:
            raise LLMWrapperError(f"Connection failed: {error}")

        except requests.Timeout as error:
            raise LLMWrapperError(f"Timeout after {config.timeout}s: {error}")

        except requests.HTTPError as error:
            raise LLMWrapperError(f"HTTP {response.status_code}: {error}")

        except Exception as error:
            raise LLMWrapperError(f"Request failed: {error}")

    def send_get_request(
        self,
        url: str,
        session: requests.Session,
        config: LLMWrapperConfig
    ) -> Dict[str, Any]:
        """
        Send GET request to API endpoint.

        Args:
            url: API endpoint URL
            session: Requests session
            config: LLM configuration

        Returns:
            JSON response as dictionary

        Raises:
            LLMWrapperError: If request fails
        """
        try:
            response = session.get(url, timeout=config.timeout)
            response.raise_for_status()
            return response.json()

        except requests.ConnectionError as error:
            raise LLMWrapperError(f"Connection failed: {error}")

        except requests.Timeout as error:
            raise LLMWrapperError(f"Timeout after {config.timeout}s: {error}")

        except requests.HTTPError as error:
            raise LLMWrapperError(f"HTTP {response.status_code}: {error}")

        except Exception as error:
            raise LLMWrapperError(f"Request failed: {error}")

    def send_post_request(
        self,
        url: str,
        payload: Dict[str, Any],
        session: requests.Session,
        config: LLMWrapperConfig
    ) -> Dict[str, Any]:
        """
        Send POST request with JSON payload.

        Args:
            url: API endpoint URL
            payload: JSON payload
            session: Requests session
            config: LLM configuration

        Returns:
            JSON response as dictionary

        Raises:
            LLMWrapperError: If request fails
        """
        try:
            response = session.post(
                url,
                json=payload,
                timeout=config.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.ConnectionError as error:
            raise LLMWrapperError(f"Connection failed: {error}")

        except requests.Timeout as error:
            raise LLMWrapperError(f"Timeout after {config.timeout}s: {error}")

        except requests.HTTPError as error:
            raise LLMWrapperError(f"HTTP {response.status_code}: {error}")

        except Exception as error:
            raise LLMWrapperError(f"Request failed: {error}")
