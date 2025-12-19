"""
Request Builder

Handles construction of URLs and request objects.
"""

from typing import List, Optional
from ..types import ChatRequest, Message, EmbeddingRequest
from ..config import LLMWrapperConfig


class RequestBuilder:
    """
    Builds URLs and request objects for LLM API calls.

    Responsibilities:
    - Build API endpoint URLs
    - Construct request payloads
    - Apply configuration defaults
    """

    def build_chat_url(self, config: LLMWrapperConfig) -> str:
        """
        Build chat completions URL.

        Args:
            config: LLM configuration

        Returns:
            Full chat endpoint URL
        """
        return f"{config.base_url}/{config.api_service}/chat/completions"

    def build_embedding_url(self, config: LLMWrapperConfig) -> str:
        """
        Build embedding URL.

        Args:
            config: LLM configuration

        Returns:
            Full embedding endpoint URL
        """
        return f"{config.base_url}/{config.embed_service}/embeddings"

    def build_embedding_models_url(self, config: LLMWrapperConfig) -> str:
        """
        Build embedding models URL.

        Args:
            config: LLM configuration

        Returns:
            Full embedding models endpoint URL
        """
        return f"{config.base_url}/{config.embed_service}/models"

    def build_models_url(self, config: LLMWrapperConfig) -> str:
        """
        Build models list URL.

        Args:
            config: LLM configuration

        Returns:
            Full models endpoint URL
        """
        return f"{config.base_url}/{config.api_service}/models"

    def build_test_url(self, config: LLMWrapperConfig) -> str:
        """
        Build test plan URL.

        Args:
            config: LLM configuration

        Returns:
            Full test endpoint URL
        """
        return f"{config.base_url}/tests"

    def build_chat_request(
        self,
        messages: List[Message],
        config: LLMWrapperConfig,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None
    ) -> ChatRequest:
        """
        Build chat request with optional parameter overrides.

        Args:
            messages: Conversation messages
            config: LLM configuration
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            response_format: Optional response format ("json" or "default")

        Returns:
            ChatRequest object ready to send
        """
        format_dict = None
        if response_format == "json":
            format_dict = {"type": "json_object"}

        return ChatRequest(
            model=config.model,
            messages=messages,
            temperature=temperature if temperature is not None else config.temperature,
            max_tokens=max_tokens if max_tokens is not None else config.max_tokens,
            response_format=format_dict
        )

    def build_embedding_request(
        self,
        input_texts: List[str],
        config: LLMWrapperConfig
    ) -> EmbeddingRequest:
        """
        Build embedding request.

        Args:
            input_texts: Texts to embed
            config: LLM configuration

        Returns:
            EmbeddingRequest object
        """
        return EmbeddingRequest(
            model=config.embed_model,
            input=input_texts,
            encoding_format="float"
        )
