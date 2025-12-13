"""
Test route for the LLM wrapper.
"""
import requests
from ..llm_types import LLMTestPlanRequest, LLMTestPlanResponse
from ...logger import logger
from ..errors import LLMWrapperError


def test(self, test_name: str) -> LLMTestPlanResponse:
    """
    Request a test execution plan.

    Args:
        test_name: The name of the test case.

    Returns:
        LLMTestPlanResponse object.

    Raises:
        LLMWrapperError: Request failed.
    """
    self._authenticate()
    url = self._build_test_url()

    request = LLMTestPlanRequest(test_name=test_name)

    try:
        response = self.session.post(
            url,
            json=request.model_dump(exclude_none=True),
            timeout=self.config.timeout
        )
        response.raise_for_status()
        data = response.json()
        return LLMTestPlanResponse(**data)

    except requests.ConnectionError as error:
        logger.error("LLM_WRAPPER", "Connection failed", {"url": url})
        raise LLMWrapperError(f"Connection failed: {error}")

    except requests.Timeout as error:
        logger.error("LLM_WRAPPER", "Request timeout", {"timeout": self.config.timeout})
        raise LLMWrapperError(f"Timeout after {self.config.timeout}s: {error}")

    except requests.HTTPError as error:
        logger.error("LLM_WRAPPER", "HTTP error", {"status": response.status_code})
        raise LLMWrapperError(f"HTTP {response.status_code}: {error}")
