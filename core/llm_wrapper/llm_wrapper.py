"""
LLM wrapper for interacting with backend API.

Provides abstraction layer for LLM API calls with error handling and logging.
"""

from typing import Optional, List, Union
import requests

from ..logger import logger
from .types import LLMMessage, LLMChatRequest, LLMChatResponse, LLMModelsResponse
from .config import LLMWrapperConfig


class LLMWrapperError(Exception):
    """Base exception for LLM wrapper errors."""
    pass


class LLMWrapper:
    """
    Wrapper for LLM API interactions.

    Handles communication with backend API for chat completions.
    """

    def __init__(self, config: Optional[LLMWrapperConfig] = None):
        """
        Initialize LLM wrapper.

        Args:
            config: LLM configuration or None for defaults
        """
        self.config = config or LLMWrapperConfig()

    def chat(
        self,
        messages: List[LLMMessage],
        verbose: bool = False
    ) -> Union[str, LLMChatResponse]:
        """
        Create chat completion.

        Args:
            messages: List of conversation messages
            verbose: If False, returns only message content (str).
                    If True, returns full response (LLMChatResponse).

        Returns:
            str if verbose=False, LLMChatResponse if verbose=True

        Raises:
            LLMWrapperError: Request failed
        """
        request = self._build_chat_request(messages)
        response = self._send_chat_request(request)

        if verbose:
            return response
        return self._extract_message_content(response)

    def list_models(self) -> LLMModelsResponse:
        """
        List available models.

        Returns:
            Models response with available models

        Raises:
            LLMWrapperError: Request failed
        """
        url = f"{self.config.base_url}/v1/models"

        try:
            response = requests.get(url, timeout=self.config.timeout)
            response.raise_for_status()
            data = response.json()
            return LLMModelsResponse(**data)

        except requests.ConnectionError as error:
            logger.error("LLM_WRAPPER", "Connection failed", {"url": url})
            raise LLMWrapperError(f"Connection failed: {error}")

        except requests.Timeout as error:
            logger.error("LLM_WRAPPER", "Request timeout", {"timeout": self.config.timeout})
            raise LLMWrapperError(f"Timeout after {self.config.timeout}s: {error}")

        except requests.HTTPError as error:
            logger.error("LLM_WRAPPER", "HTTP error", {"status": response.status_code})
            raise LLMWrapperError(f"HTTP {response.status_code}: {error}")

    def _build_chat_request(self, messages: List[LLMMessage]) -> LLMChatRequest:
        """Build chat request from messages."""
        return LLMChatRequest(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

    def _send_chat_request(self, request: LLMChatRequest) -> LLMChatResponse:
        """Send chat request to API endpoint."""
        url = f"{self.config.base_url}/v1/chat/completions"

        self._log_request_start(request)

        try:
            request_payload = request.model_dump()
            self._log_request_payload(request_payload)

            response = requests.post(
                url,
                json=request_payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            llm_response = LLMChatResponse(**data)

            self._log_response_received(llm_response)
            return llm_response

        except requests.ConnectionError as error:
            logger.error("LLM_WRAPPER", "Connection failed", {"url": url})
            raise LLMWrapperError(f"Connection failed: {error}")

        except requests.Timeout as error:
            logger.error("LLM_WRAPPER", "Request timeout", {"timeout": self.config.timeout})
            raise LLMWrapperError(f"Timeout after {self.config.timeout}s: {error}")

        except requests.HTTPError as error:
            logger.error("LLM_WRAPPER", "HTTP error", {"status": response.status_code})
            raise LLMWrapperError(f"HTTP {response.status_code}: {error}")

    def _extract_message_content(self, response: LLMChatResponse) -> str:
        """Extract message content from response."""
        if not response.choices or len(response.choices) == 0:
            raise LLMWrapperError("No choices in response")
        return response.choices[0].message.content

    def close(self) -> None:
        """
        Close LLM wrapper and cleanup resources.

        Currently a no-op as requests library manages connections automatically.
        """
        logger.debug("LLM_WRAPPER", "Closing wrapper")

    def _log_request_start(self, request: LLMChatRequest) -> None:
        """Logs start of LLM request."""
        logger.info(
            "LLM_WRAPPER",
            f"Sending request to LLM",
            {
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "message_count": len(request.messages)
            }
        )

    def _log_request_payload(self, payload: dict) -> None:
        """Logs detailed request payload."""
        logger.info(
            "LLM_WRAPPER",
            "Request payload details"
        )

        messages = payload.get("messages", [])
        for idx, msg in enumerate(messages):
            content = msg.get("content", "")
            content_preview = content[:200] if content else "[no content]"

            logger.debug(
                "LLM_WRAPPER",
                f"Message {idx + 1}/{len(messages)} to LLM",
                {
                    "role": msg.get("role"),
                    "content_length": len(content) if content else 0,
                    "content_preview": content_preview
                }
            )

    def _log_response_received(self, response: LLMChatResponse) -> None:
        """Logs LLM response received."""
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            content = choice.message.content or ""
            content_preview = content[:200] if content else "[no content]"

            logger.info(
                "LLM_WRAPPER",
                "Response received from LLM",
                {
                    "model": response.model,
                    "finish_reason": choice.finish_reason,
                    "content_length": len(content),
                    "content_preview": content_preview,
                    "has_tool_calls": bool(choice.message.tool_calls)
                }
            )
        else:
            logger.warning("LLM_WRAPPER", "Response received with no choices")
