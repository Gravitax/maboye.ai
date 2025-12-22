"""
Request Builder

Handles construction of URLs and request objects.
"""

from typing import List, Optional, Dict
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

    def _join_url(self, base: str, path: str) -> str:
        """Safely join base URL and path."""
        if not path:
            return base
        return f"{base.rstrip('/')}/{path.lstrip('/')}"

    def build_chat_url(self, config: LLMWrapperConfig) -> str:
        """
        Build chat completions URL.
        """
        return self._join_url(config.base_url, config.api_service)

    def build_embedding_url(self, config: LLMWrapperConfig) -> str:
        """
        Build embedding URL.
        """
        return self._join_url(config.base_url, config.embed_service)

    def build_embedding_models_url(self, config: LLMWrapperConfig) -> str:
        """
        Build embedding models URL.
        """
        # Assuming embed_service points to the embedding endpoint (e.g. /embeddings)
        # We might need a separate config for embedding models if it differs standardly
        # But for now, let's assume standard OpenAI-like structure isn't strictly followed 
        # or config handles it. 
        # If embed_service is "embeddings", this might be wrong if models is "models".
        # Let's use models_service for generic models, but if there's specific embedding models...
        # For simplicty and cleaning up the hardcoded paths:
        return self._join_url(config.base_url, "models") 

    def build_models_url(self, config: LLMWrapperConfig) -> str:
        """
        Build models list URL.
        """
        return self._join_url(config.base_url, config.models_service)

    def build_test_url(self, config: LLMWrapperConfig) -> str:
        """
        Build test plan URL.
        """
        return self._join_url(config.base_url, "tests")


    def build_headers(self, token: Optional[str], api_key: Optional[str]) -> Dict[str, str]:
        """
        Build headers with authorization.
        Prioritize token if present, otherwise API key.
        """
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            
        return headers

    def build_chat_request(
        self,
        messages: List[Message],
        config: LLMWrapperConfig,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
        stream: Optional[bool] = None
    ) -> ChatRequest:
        """
        Build chat request with optional parameter overrides.

        Args:
            messages: Conversation messages
            config: LLM configuration
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            response_format: Optional response format ("json" or "default")
            stream: Optional stream override (True for streaming responses)

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
            response_format=format_dict,
            stream=stream if stream is not None else config.stream
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
