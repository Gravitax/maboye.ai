"""
Memory Agent Manager

Handles all memory-related operations including message building,
storage, and conversation history management.
"""

from typing import List, Dict, Any, Tuple

from core.memory import MemoryManager
from core.prompt_builder import PromptBuilder
from agents.config import AgentConfig
from agents.types import Message, ToolCall
from agents.base_agent.llm_message_manager import LLMMessageAgentManager


class MemoryAgentManager:
    """
    Manages memory operations for agents.

    Responsibilities:
    - Building message lists from history and prompts
    - Storing user turns with context
    - Storing assistant messages with tool interactions
    - Extracting and collecting tool-related data for storage
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        prompt_builder: PromptBuilder,
        llm_message_manager: LLMMessageAgentManager,
        config: AgentConfig
    ):
        """
        Initialize the memory agent manager.

        Args:
            memory_manager: The central memory system.
            prompt_builder: Component for constructing prompts.
            llm_message_manager: Manager for LLM message formatting.
            config: Agent configuration.
        """
        self._memory_manager = memory_manager
        self._prompt_builder = prompt_builder
        self._llm_message_manager = llm_message_manager
        self._config = config

    def build_message_list(self, user_prompt: str) -> List[Message]:
        """
        Build the message list from history and current user prompt.

        Args:
            user_prompt: The input string from the user.

        Returns:
            List of messages including history and current prompt.
        """
        history = self._memory_manager.get_conversation_history(
            max_turns=self._config.max_history_turns
        )
        messages = self._prompt_builder.build_from_history(history)

        user_message: Message = {
            "role": "user",
            "content": user_prompt
        }
        messages.append(user_message)

        return messages

    def store_user_turn(self, user_prompt: str, messages: List[Message]) -> None:
        """
        Store the user turn with context information in memory.

        Args:
            user_prompt: The user's input.
            messages: The complete message list.
        """
        full_prompt_str = self._llm_message_manager.format_messages_for_storage(messages)
        history = self._memory_manager.get_conversation_history(
            max_turns=self._config.max_history_turns
        )

        context_info = {
            "history_turns": len(history),
            "total_messages": len(messages),
            "agent_name": self._config.name
        }

        self._memory_manager.add_conversation_turn(
            role="user",
            content=user_prompt,
            query=user_prompt,
            prompt=full_prompt_str,
            context=context_info
        )

    def store_messages_with_tools(self, new_messages: List[Message]) -> None:
        """
        Store messages with their associated tool calls and results.

        Args:
            new_messages: List of new messages to store.
        """
        idx = 0
        while idx < len(new_messages):
            msg = new_messages[idx]

            if msg["role"] == "assistant":
                idx = self._process_assistant_message(new_messages, idx)

            idx += 1

    def _process_assistant_message(self, messages: List[Message], start_idx: int) -> int:
        """
        Process and store an assistant message with its tool calls and results.

        Args:
            messages: List of all messages.
            start_idx: Index of the assistant message to process.

        Returns:
            Index of the last processed message.
        """
        msg = messages[start_idx]
        tool_calls_list = None
        tool_results_list = None
        next_idx = start_idx

        if msg.get("tool_calls"):
            tool_calls_list = self._extract_tool_calls(msg["tool_calls"])
            tool_results_list, next_idx = self._collect_tool_results(messages, start_idx + 1)

        self._memory_manager.add_conversation_turn(
            role="assistant",
            content=msg.get("content"),
            tool_calls=tool_calls_list,
            tool_results=tool_results_list
        )

        return next_idx

    def _extract_tool_calls(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """
        Extract tool call information for storage.

        Args:
            tool_calls: List of tool calls from message.

        Returns:
            List of formatted tool call dictionaries.
        """
        extracted_calls = []
        for tc in tool_calls:
            extracted_calls.append({
                "id": tc.get("id"),
                "name": tc.get("name"),
                "args": tc.get("args")
            })
        return extracted_calls

    def _collect_tool_results(
        self, messages: List[Message], start_idx: int
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Collect consecutive tool result messages.

        Args:
            messages: List of all messages.
            start_idx: Index to start collecting from.

        Returns:
            Tuple of (tool results list, index of last tool result).
        """
        tool_results = []
        idx = start_idx

        while idx < len(messages) and messages[idx]["role"] == "tool":
            tool_msg = messages[idx]
            tool_results.append({
                "tool_call_id": tool_msg.get("tool_call_id"),
                "result": tool_msg.get("content")
            })
            idx += 1

        return tool_results, idx - 1

    def get_conversation_history(self, max_turns: int = None) -> List[Dict[str, Any]]:
        """
        Get conversation history from memory.

        Args:
            max_turns: Maximum number of turns to retrieve.

        Returns:
            List of conversation turns.
        """
        if max_turns is None:
            max_turns = self._config.max_history_turns

        return self._memory_manager.get_conversation_history(max_turns=max_turns)
