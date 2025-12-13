"""
Chat route for the LLM wrapper.
"""
from typing import List, Union
from ..llm_types import LLMMessage, LLMChatResponse

def chat(
    self,
    messages: List[LLMMessage],
    verbose: bool = False
) -> Union[str, LLMChatResponse]:
    """
    Create chat completion.

    Args:
        messages: List of conversation messages
        verbose: If False, returns only message content (str).
                 If True, returns full response (LLMChatResponse).

    Returns:
        str if verbose=False, LLMChatResponse if verbose=True

    Raises:
        LLMWrapperError: Request failed
    """
    request = self._build_chat_request(messages)
    response = self._send_chat_request(request)

    if verbose:
        return response
    return self._extract_message_content(response)
