"""
Models route for the LLM wrapper.
"""
from ..types import ModelsResponse


def list_models(self) -> ModelsResponse:
    """
    List available models.

    Returns:
        Models response with available models

    Raises:
        LLMWrapperError: Request failed
    """
    self._authenticate()
    url = self.request_builder.build_models_url(self.config)
    headers = self.request_builder.build_headers(self.token, self.config.api_key)
    data = self.request_sender.send_get_request(url, self.session, self.config, headers=headers)
    return ModelsResponse(**data)
