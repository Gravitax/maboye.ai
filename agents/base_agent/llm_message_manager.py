"""
LLM Message Agent Manager

Handles all LLM message-related operations including format conversion,
message cleaning, and formatting for storage.
"""

import json
from typing import List, Dict, Any

from core.llm_wrapper.llm_wrapper import LLMWrapper
from core.llm_wrapper.llm_types import LLMMessage
from agents.types import Message, ToolCall


class LLMMessageAgentManager:
    """
    Manages LLM message operations for agents.

    Responsibilities:
    - Converting between LLM and internal message formats
    - Cleaning message dictionaries
    - Formatting messages for storage
    - Getting LLM responses
    """

    def __init__(self, llm: LLMWrapper):
        """
        Initialize the LLM message manager.

        Args:
            llm: The LLM wrapper instance for API communication.
        """
        self._llm = llm

    def get_llm_response(self, messages: List[Message]) -> Message:
        """
        Get response from LLM and convert to internal message format.

        Args:
            messages: Current conversation history.

        Returns:
            Converted assistant message in internal format.
        """
        llm_messages = [LLMMessage(**self._clean_message_dict(msg)) for msg in messages]
        llm_response = self._llm.chat(messages=llm_messages, verbose=True)
        llm_raw_message = llm_response.choices[0].message

        return self._convert_llm_message(llm_raw_message)

    def _clean_message_dict(self, message: Message) -> Dict[str, Any]:
        """
        Clean message dictionary by removing None values.

        Args:
            message: Message dictionary to clean.

        Returns:
            Cleaned dictionary without None values.
        """
        return {k: v for k, v in message.items() if v is not None}

    def _convert_llm_message(self, llm_message: Any) -> Message:
        """
        Convert LLM message format to internal message format.

        Args:
            llm_message: Message from LLM in Pydantic format.

        Returns:
            Message in internal TypedDict format.
        """
        converted_message: Message = {
            "role": llm_message.role,
            "content": llm_message.content,
        }

        if llm_message.tool_calls:
            converted_message["tool_calls"] = self._convert_tool_calls(llm_message.tool_calls)

        if llm_message.tool_call_id:
            converted_message["tool_call_id"] = llm_message.tool_call_id

        return converted_message

    def _convert_tool_calls(self, tool_calls: List[Any]) -> List[ToolCall]:
        """
        Convert tool calls from LLM format to internal format.

        Args:
            tool_calls: Tool calls from LLM.

        Returns:
            List of tool calls in internal format.
        """
        converted_calls = []
        for tool_call in tool_calls:
            converted_calls.append({
                "id": tool_call.id,
                "name": tool_call.function["name"],
                "args": tool_call.function["arguments"],
            })
        return converted_calls

    def format_messages_for_storage(self, messages: List[Message]) -> str:
        """
        Format messages list into OpenAI API format for storage.

        Args:
            messages: List of conversation messages.

        Returns:
            JSON-formatted string in OpenAI API format.
        """
        formatted_messages = [self._format_single_message(msg) for msg in messages]
        return json.dumps({"messages": formatted_messages}, indent=2, ensure_ascii=False)

    def _format_single_message(self, msg: Message) -> Dict[str, Any]:
        """
        Format a single message for storage.

        Args:
            msg: Message to format.

        Returns:
            Formatted message dictionary.
        """
        formatted_msg = {
            "role": msg.get("role", "unknown"),
            "content": msg.get("content", "")
        }

        if msg.get("tool_calls"):
            formatted_msg["tool_calls"] = msg["tool_calls"]

        if msg.get("tool_call_id"):
            formatted_msg["tool_call_id"] = msg["tool_call_id"]

        return formatted_msg
