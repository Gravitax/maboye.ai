"""
LLM wrapper for interacting with backend API

Provides abstraction layer for LLM API calls with error handling,
retries, and logging.
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.logger import logger
from LLM.types import (
    Message,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    ModelsResponse
)
from LLM.config import LLMConfig


class LLMError(Exception):
    """Base exception for LLM errors"""
    pass


class LLMConnectionError(LLMError):
    """Connection-related errors"""
    pass


class LLMAPIError(LLMError):
    """API response errors"""
    pass


class LLM:
    """
    Wrapper for LLM API interactions

    Handles communication with backend API endpoints including
    chat completions, text completions, and model listings.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM wrapper

        Args:
            config: LLM configuration (uses defaults if None)
        """
        self.config = config or LLMConfig()
        self._session = self._create_session()
        self._last_response: Optional[Union[ChatCompletionResponse, CompletionResponse]] = None
        self._request_count = 0

        logger.info("LLM", "LLM wrapper initialized", {
            "base_url": self.config.base_url,
            "model": self.config.model,
            "timeout": self.config.timeout
        })

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry logic

        Returns:
            Configured session with retry adapter
        """
        session = requests.Session()

        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        if self.config.api_key:
            session.headers.update({"Authorization": f"Bearer {self.config.api_key}"})

        return session

    def _make_request(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API

        Args:
            endpoint: API endpoint path
            method: HTTP method
            data: Request payload

        Returns:
            Response data as dictionary

        Raises:
            LLMConnectionError: Connection failed
            LLMAPIError: API returned error
        """
        url = f"{self.config.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self._session.get(url, timeout=self.config.timeout)
            elif method == "POST":
                response = self._session.post(
                    url,
                    json=data,
                    timeout=self.config.timeout
                )
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.ConnectionError as e:
            logger.error("LLM", "Connection error", {"url": url, "error": str(e)})
            raise LLMConnectionError(f"Failed to connect to {url}: {e}")

        except requests.Timeout as e:
            logger.error("LLM", "Request timeout", {"url": url, "timeout": self.config.timeout})
            raise LLMConnectionError(f"Request timeout after {self.config.timeout}s: {e}")

        except requests.HTTPError as e:
            logger.error("LLM", "API error", {
                "url": url,
                "status": response.status_code,
                "error": str(e)
            })
            raise LLMAPIError(f"API error {response.status_code}: {e}")

    def chat_completion(
        self,
        messages: List[Message],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatCompletionResponse:
        """
        Create chat completion

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens to generate (overrides config)
            **kwargs: Additional parameters for API

        Returns:
            Chat completion response

        Raises:
            LLMError: Request failed
        """
        self._request_count += 1

        request = ChatCompletionRequest(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            **kwargs
        )

        logger.info("LLM", "Chat completion request", {
            "request_id": self._request_count,
            "model": request.model,
            "messages_count": len(messages),
            "temperature": request.temperature
        })

        response_data = self._make_request(
            "/v1/chat/completions",
            method="POST",
            data=request.model_dump(exclude_none=True)
        )

        response = ChatCompletionResponse(**response_data)
        self._last_response = response

        logger.info("LLM", "Chat completion response received", {
            "request_id": self._request_count,
            "response_id": response.id,
            "tokens_used": response.usage.total_tokens
        })

        return response

    def completion(
        self,
        prompt: Union[str, List[str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> CompletionResponse:
        """
        Create text completion

        Args:
            prompt: Text prompt or list of prompts
            temperature: Sampling temperature (overrides config)
            max_tokens: Max tokens to generate (overrides config)
            **kwargs: Additional parameters for API

        Returns:
            Completion response

        Raises:
            LLMError: Request failed
        """
        self._request_count += 1

        request = CompletionRequest(
            model=self.config.model,
            prompt=prompt,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            **kwargs
        )

        logger.info("LLM", "Completion request", {
            "request_id": self._request_count,
            "model": request.model,
            "temperature": request.temperature
        })

        response_data = self._make_request(
            "/v1/completions",
            method="POST",
            data=request.model_dump(exclude_none=True)
        )

        response = CompletionResponse(**response_data)
        self._last_response = response

        logger.info("LLM", "Completion response received", {
            "request_id": self._request_count,
            "response_id": response.id,
            "tokens_used": response.usage.total_tokens
        })

        return response

    def list_models(self) -> ModelsResponse:
        """
        List available models

        Returns:
            Models response with available models

        Raises:
            LLMError: Request failed
        """
        logger.debug("LLM", "Listing models")

        response_data = self._make_request("/v1/models", method="GET")
        response = ModelsResponse(**response_data)

        logger.debug("LLM", "Models retrieved", {"count": len(response.data)})

        return response

    def get_last_response(self) -> Optional[Union[ChatCompletionResponse, CompletionResponse]]:
        """
        Get last response from LLM

        Returns:
            Last response or None if no requests made
        """
        return self._last_response

    def get_request_count(self) -> int:
        """
        Get total number of requests made

        Returns:
            Request count
        """
        return self._request_count

    def reset_session(self):
        """Reset session and clear state"""
        self._session.close()
        self._session = self._create_session()
        self._last_response = None
        logger.info("LLM", "Session reset")

    def close(self):
        """Close session and cleanup resources"""
        self._session.close()
        logger.info("LLM", "LLM wrapper closed", {
            "total_requests": self._request_count
        })

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
