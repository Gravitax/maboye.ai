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
    payload = request.model_dump(exclude_none=True)
    data = self.request_sender.send_post_request(url, payload, self.session, self.config)
    return EmbeddingResponse(**data)


def list_embedding_models(self) -> ModelsResponse:
    """
    List available embedding models.

    Returns:
        Models response with available models

    Raises:
        LLMWrapperError: Request failed
    """
    self._authenticate()
    url = self.request_builder.build_embedding_models_url(self.config)
    data = self.request_sender.send_get_request(url, self.session, self.config)
    return ModelsResponse(**data)
