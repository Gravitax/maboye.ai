"""
Chat iterative route for LLM wrapper.
"""
import requests
from typing import List, Dict, Any, Optional
from ..errors import LLMWrapperError
from ...logger import logger


def chat_iterative(self, messages: List[Dict[str, Any]], scenario: str = "auto") -> Dict[str, Any]:
    """
    Send messages to iterative chat endpoint.

    Args:
        messages: List of message dictionaries with role, content, tool_calls, etc.
        scenario: Scenario name for backend mock routing

    Returns:
        Dictionary with role, content, and optional tool_calls

    Raises:
        LLMWrapperError: Request failed
    """
    self._authenticate()
    url = f"{self.config.base_url}/chat/iterative"

    request_data = {
        "messages": messages,
        "scenario": scenario
    }

    try:
        response = self.session.post(
            url,
            json=request_data,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        data = response.json()

        logger.info("LLM_WRAPPER", "Iterative chat response received", {
            "has_tool_calls": data.get("tool_calls") is not None,
            "is_final": data.get("tool_calls") is None
        })

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
