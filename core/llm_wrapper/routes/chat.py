"""
Chat route for the LLM wrapper.
"""
from typing import List, Union, Optional
from ..types import Message, ChatResponse


def chat(
    self,
    messages: List[Message],
    verbose: bool = False,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    response_format: Optional[str] = None

) -> Union[str, ChatResponse]:
    """
    Create chat completion.

    Args:
        messages: List of conversation messages
        verbose: If False, returns only message content (str).
                 If True, returns full response (ChatResponse).
        temperature: Optional temperature override for this call
        max_tokens: Optional max_tokens override for this call

    Returns:
        str if verbose=False, ChatResponse if verbose=True

    Raises:
        LLMWrapperError: Request failed
    """
    self._authenticate()
    url = self.request_builder.build_chat_url(self.config)
    request = self.request_builder.build_chat_request(messages, self.config, temperature, max_tokens, response_format)
    response = self.request_sender.send_chat_request(url, request, self.session, self.config)

    if verbose:
        return response
    return self.response_handler.extract_message_content(response)
