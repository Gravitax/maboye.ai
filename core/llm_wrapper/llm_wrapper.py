"""
LLM wrapper for interacting with backend API.

Provides abstraction layer for LLM API calls with error handling and logging.
"""

from typing import Optional, Union, List, Dict
import requests

from ..logger import logger

from .llm_types import (
    LLMMessage,
    LLMChatRequest,
    LLMChatResponse,
    LLMModelsResponse,
    LLMEmbeddingRequest,
    LLMEmbeddingResponse,
    LLMTestPlanRequest,
    LLMTestPlanResponse,
)

from .config import LLMWrapperConfig
from .errors import LLMWrapperError
from .routes import auth, chat, embedding, models, test


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
        self.session = requests.Session()
        self.session.verify = False  # To disable SSL verification
        self.token: Optional[str] = None
        # Auto-initialize model from API
        self._initialize_model()

    def _authenticate(self) -> None:
        auth.authenticate(self)

    def _initialize_model(self) -> None:
        """
        Initialize model by fetching available models from API.
        If configured model doesn't exist, uses the first available model.
        """
        try:
            self._authenticate()
            models_response = self.list_models()
            if not models_response.data:
                logger.warning("LLM_WRAPPER", "No models available from API")
                return
            available_models = [model.id for model in models_response.data]
            configured_model = self.config.model
            # Check if configured model exists
            if configured_model in available_models:
                logger.info("LLM_WRAPPER", f"Using configured model: {configured_model}")
            else:
                # Use first available model
                self.config.model = available_models[0]
                logger.warning(
                    "LLM_WRAPPER",
                    f"Configured model '{configured_model}' not found. Using '{self.config.model}' instead.",
                    {"available_models": available_models}
                )

        except Exception as error:
            logger.error("LLM_WRAPPER", "Model initialization failed", {"error": str(error)})
            # Keep the configured model as fallback
            logger.warning("LLM_WRAPPER", f"Continuing with configured model: {self.config.model}")

    def chat(
        self,
        messages: List[LLMMessage],
        verbose: bool = False
    ) -> Union[str, LLMChatResponse]:
        return chat.chat(self, messages, verbose)

    def embedding(self, input_texts: List[str]) -> LLMEmbeddingResponse:
        return embedding.embedding(self, input_texts)

    def list_models(self) -> LLMModelsResponse:
        return models.list_models(self)

    def list_embedding_models(self) -> LLMModelsResponse:
        return embedding.list_embedding_models(self)

    def test(self, test_name: str) -> LLMTestPlanResponse:
        return test.test(self, test_name)

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
        self._authenticate()
        url = self._build_chat_url()
        self._log_request_start(request)

        try:
            request_payload = self._prepare_request_payload(request)
            self._log_request_payload(request_payload)
            response = self.session.post(
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
            logger.error("LLM_WRAPPER", "HTTP error", {"status": response.status_code, "response": response.text})
            raise LLMWrapperError(f"HTTP {response.status_code}: {error}")

    def _extract_message_content(self, response: LLMChatResponse) -> str:
        """Extract message content from response."""
        if not response.choices or len(response.choices) == 0:
            raise LLMWrapperError("No choices in response")
        return response.choices[0].message.content

    def _build_chat_url(self) -> str:
        """Build chat completions URL based on service configuration."""
        return f"{self.config.base_url}/{self.config.api_service}/chat/completions"

    def _build_embedding_url(self) -> str:
        """Build embedding URL based on service configuration."""
        return f"{self.config.base_url}/{self.config.embed_service}/embeddings"

    def _build_embedding_models_url(self) -> str:
        """Build embedding models URL based on service configuration."""
        return f"{self.config.base_url}/{self.config.embed_service}/models"

    def _build_models_url(self) -> str:
        """build models list URL based on service configuration."""
        return f"{self.config.base_url}/{self.config.api_service}/models"

    def _build_test_url(self) -> str:
        """Build test plan URL."""
        return f"{self.config.base_url}/tests"

    def _prepare_request_payload(self, request: LLMChatRequest) -> Dict:
        """Prepare request payload with optional wrapper."""
        return request.model_dump(exclude_none=True)

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

    def _log_request_payload(self, payload: Dict) -> None:
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
