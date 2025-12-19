"""
LLM Wrapper - Simplified

Provides abstraction layer for LLM API calls.
Delegates to specialized client components for clean separation of concerns.
"""

from typing import Optional, Union, List, Dict
import requests

from ..logger import logger
from .types import Message, ChatResponse, ModelsResponse, EmbeddingResponse
from .config import LLMWrapperConfig
from .client import RequestBuilder, RequestSender, ResponseHandler
from .routes import auth, chat, embedding, models


class LLMWrapper:
    """
    Simplified wrapper for LLM API interactions.

    Delegates request building, sending, and response handling
    to specialized components for better maintainability.
    """

    def __init__(self, config: Optional[LLMWrapperConfig] = None):
        """
        Initialize LLM wrapper.

        Args:
            config: LLM configuration or None for defaults
        """
        self.config = config or LLMWrapperConfig()
        self.session = requests.Session()
        self.session.verify = False
        self.token: Optional[str] = None

        # Initialize client components
        self.request_builder = RequestBuilder()
        self.request_sender = RequestSender()
        self.response_handler = ResponseHandler()

        # Auto-initialize model from API
        self._initialize_model()

    def _authenticate(self) -> None:
        """Authenticate with API."""
        auth.authenticate(self)

    def _initialize_model(self) -> None:
        """
        Initialize model by fetching available models from API.
        Falls back to configured model if initialization fails.
        """
        try:
            self._authenticate()
            models_response = self.list_models()

            if not models_response.data:
                return

            available_models = [model.id for model in models_response.data]
            configured_model = self.config.model

            if configured_model in available_models:
                pass
            else:
                self.config.model = available_models[0]

        except Exception as error:
            pass

    def chat(
        self,
        messages: List[Message],
        verbose: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None
    ) -> Union[str, ChatResponse]:
        """
        Send chat completion request.

        Args:
            messages: Conversation messages
            verbose: Return full response if True, content only if False
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            response_format: Optional response format ("json" or "default")

        Returns:
            ChatResponse if verbose=True, message content string if verbose=False
        """
        return chat.chat(self, messages, verbose, temperature, max_tokens, response_format)

    def embedding(self, input_texts: List[str]) -> EmbeddingResponse:
        """
        Get embeddings for input texts.

        Args:
            input_texts: Texts to embed

        Returns:
            EmbeddingResponse with embeddings
        """
        return embedding.embedding(self, input_texts)

    def list_models(self) -> ModelsResponse:
        """
        List available models.

        Returns:
            ModelsResponse with available models
        """
        return models.list_models(self)

    def list_embedding_models(self) -> ModelsResponse:
        """
        List available embedding models.

        Returns:
            ModelsResponse with embedding models
        """
        return embedding.list_embedding_models(self)

    def close(self) -> None:
        """
        Close LLM wrapper and cleanup resources.
        """
        pass
