"""
Test iterative route for LLM wrapper.
"""
import requests
from typing import List, Dict, Any, Optional
from ..errors import LLMWrapperError
from ...logger import logger


def test_iterative(
    self,
    messages: List[Dict[str, Any]],
    scenario: str = "auto",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Send messages to iterative test endpoint.

    Args:
        messages: List of message dictionaries with role, content, tool_calls, etc.
        scenario: Scenario name for backend mock routing
        temperature: Optional temperature override for this call
        max_tokens: Optional max_tokens override for this call
        timeout: Optional timeout override for this call

    Returns:
        Dictionary with role, content, and optional tool_calls

    Raises:
        LLMWrapperError: Request failed
    """
    self._authenticate()
    url = f"{self.config.base_url}/tests/iterative"

    request_data = {
        "messages": messages,
        "scenario": scenario,
        "temperature": temperature if temperature is not None else self.config.temperature,
        "max_tokens": max_tokens if max_tokens is not None else self.config.max_tokens
    }

    request_timeout = timeout if timeout is not None else self.config.timeout

    try:
        response = self.session.post(
            url,
            json=request_data,
            timeout=request_timeout
        )
        response.raise_for_status()
        data = response.json()
        return data

    except requests.ConnectionError as error:
        logger.error("LLM_WRAPPER", "Connection failed", {"url": url})
        raise LLMWrapperError(f"Connection failed: {error}")

    except requests.Timeout as error:
        logger.error("LLM_WRAPPER", "Request timeout", {"timeout": self.config.timeout})
        raise LLMWrapperError(f"Timeout after {self.config.timeout}s: {error}")

    except requests.HTTPError as error:
        logger.error("LLM_WRAPPER", "HTTP error", {"status": response.status_code})
        raise LLMWrapperError(f"HTTP {response.status_code}: {error}")
