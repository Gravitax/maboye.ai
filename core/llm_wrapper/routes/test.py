"""
Test route for the LLM wrapper.
"""
from ..types import TestPlanResponse


def test(self, test_name: str) -> TestPlanResponse:
    """
    Request a test execution plan.

    Args:
        test_name: The name of the test case.

    Returns:
        TestPlanResponse object.

    Raises:
        LLMWrapperError: Request failed.
    """
    self._authenticate()
    url = self.request_builder.build_test_url(self.config)
    payload = {"test_name": test_name}
    data = self.request_sender.send_post_request(url, payload, self.session, self.config)
    return TestPlanResponse(**data)
