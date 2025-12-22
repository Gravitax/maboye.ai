"""
Embedding routes for the LLM wrapper.
"""
from typing import List
from ..types import EmbeddingResponse, ModelsResponse


def embedding(self, input_texts: List[str]) -> EmbeddingResponse:
    """
    Create embeddings for a list of texts.

    Args:
        input_texts: List of texts to embed.

    Returns:
        EmbeddingResponse object.

    Raises:
        LLMWrapperError: Request failed.
    """
    self._authenticate()
    url = self.request_builder.build_embedding_url(self.config)
    request = self.request_builder.build_embedding_request(input_texts, self.config)
    headers = self.request_builder.build_headers(self.token, self.config.api_key)
    
    # Using send_post_request directly as it matches the signature
    data = self.request_sender.send_post_request(
        url, request.model_dump(), self.session, self.config, headers=headers
    )
    return EmbeddingResponse(**data)


def list_embedding_models(self) -> ModelsResponse:
    """
    List available embedding models.

    Returns:
        Models response with available models
    """
    self._authenticate()
    url = self.request_builder.build_embedding_models_url(self.config)
    headers = self.request_builder.build_headers(self.token, self.config.api_key)
    
    data = self.request_sender.send_get_request(
        url, self.session, self.config, headers=headers
    )
    return ModelsResponse(**data)
