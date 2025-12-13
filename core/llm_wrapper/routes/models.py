"""
Models route for the LLM wrapper.
"""
import requests
from ..llm_types import LLMModelsResponse
from ...logger import logger
from ..errors import LLMWrapperError


def list_models(self) -> LLMModelsResponse:
    """
    List available models.

    Returns:
        Models response with available models

    Raises:
        LLMWrapperError: Request failed
    """
    self._authenticate()
    url = self._build_models_url()

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
