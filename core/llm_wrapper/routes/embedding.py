"""
Embedding routes for the LLM wrapper.
"""
from typing import List
import requests
from ..errors import LLMWrapperError
from ..llm_types import LLMEmbeddingRequest, LLMEmbeddingResponse, LLMModelsResponse
from ...logger import logger


def embedding(self, input_texts: List[str]) -> LLMEmbeddingResponse:
    """
    Create embeddings for a list of texts.

    Args:
        input_texts: List of texts to embed.

    Returns:
        LLMEmbeddingResponse object.

    Raises:
        LLMWrapperError: Request failed.
    """
    self._authenticate()
    url = self._build_embedding_url()

    request = LLMEmbeddingRequest(model=self.config.model, input=input_texts)

    try:
        response = self.session.post(
            url,
            json=request.model_dump(exclude_none=True),
            timeout=self.config.timeout
        )
        response.raise_for_status()
        data = response.json()
        return LLMEmbeddingResponse(**data)

    except requests.ConnectionError as error:
        logger.error("LLM_WRAPPER", "Connection failed", {"url": url})
        raise LLMWrapperError(f"Connection failed: {error}")

    except requests.Timeout as error:
        logger.error("LLM_WRAPPER", "Request timeout", {"timeout": self.config.timeout})
        raise LLMWrapperError(f"Timeout after {self.config.timeout}s: {error}")

    except requests.HTTPError as error:
        logger.error("LLM_WRAPPER", "HTTP error", {"status": response.status_code})
        raise LLMWrapperError(f"HTTP {response.status_code}: {error}")

def list_embedding_models(self) -> LLMModelsResponse:
    """
    List available embedding models.

    Returns:
        Models response with available models

    Raises:
        LLMWrapperError: Request failed
    """
    self._authenticate()
    url = self._build_embedding_models_url()

    try:
        response = self.session.get(url, timeout=self.config.timeout)
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
