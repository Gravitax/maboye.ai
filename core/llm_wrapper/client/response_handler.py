"""
Response Handler

Handles response extraction and logging.
"""

from typing import Dict, Any, List
from ...logger import logger
from ..types import ChatResponse, ChatRequest
from ..errors import LLMWrapperError


class ResponseHandler:
    """
    Handles response extraction and detailed logging.

    Responsibilities:
    - Extract message content from responses
    - Log requests and responses
    - Format log messages
    """

    def extract_message_content(self, response: ChatResponse) -> str:
        """
        Extract message content from chat response.

        Args:
            response: Chat response from API

        Returns:
            Message content string

        Raises:
            LLMWrapperError: If no choices in response
        """
        if not response.choices or len(response.choices) == 0:
            raise LLMWrapperError("No choices in response")

        return response.choices[0].message.content or ""

    def log_request_start(self, request: ChatRequest) -> None:
        """
        Log start of LLM request.

        Args:
            request: Chat request being sent
        """
        logger.info(
            "RESPONSE_HANDLER",
            "Sending request to LLM",
            {
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "message_count": len(request.messages)
            }
        )

    def log_request_payload(self, messages: List[Dict[str, Any]]) -> None:
        """
        Log detailed request payload (messages).

        Args:
            messages: List of message dictionaries
        """
        logger.info("RESPONSE_HANDLER", "Request payload details")

        for idx, msg in enumerate(messages):
            content = msg.get("content", "")
            content_preview = content[:200] if content else "[no content]"

            logger.debug(
                "RESPONSE_HANDLER",
                f"Message {idx + 1}/{len(messages)} to LLM",
                {
                    "role": msg.get("role"),
                    "content_length": len(content) if content else 0,
                    "content_preview": content_preview
                }
            )

    def log_response_received(self, response: ChatResponse) -> None:
        """
        Log LLM response received.

        Args:
            response: Chat response from LLM
        """
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            content = choice.message.content or ""
            content_preview = content[:200] if content else "[no content]"

            logger.info(
                "RESPONSE_HANDLER",
                "Response received from LLM",
                {
                    "model": response.model,
                    "finish_reason": choice.finish_reason,
                    "content_length": len(content),
                    "content_preview": content_preview,
                    "has_tool_calls": bool(choice.message.tool_calls)
                }
            )
        else:
            logger.warning("RESPONSE_HANDLER", "Response received with no choices")
