"""
Defines the abstract base class for all agents.

This module provides the core structure and reasoning loop for agents, ensuring a
consistent, scalable, and extensible architecture for creating specialized agents.
"""

from abc import ABC
from typing import List, Dict, Any, Generator, Tuple

from core.logger import logger
from core.llm_wrapper.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from core.prompt_builder import PromptBuilder
from core.memory import MemoryManager
from agents.types import Message, AgentInput, AgentOutput, ToolCall, ToolResult
from agents.config import AgentConfig


class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class BaseAgent(ABC):
    """
    Abstract Base Class for LLM-powered agents.

    This class provides a foundational structure for building specialized agents.
    It encapsulates the core 'think-act-observe' loop, tool usage, and interaction
    with the LLM, while leaving the specific implementation of the agent's task
    to its subclasses.

    Attributes:
        _llm (LLMWrapper): The language model wrapper for API communication.
        _config (AgentConfig): Configuration specific to the agent.
        _tool_scheduler (ToolScheduler): The component responsible for executing tools.
        _memory_manager (MemoryManager): The central memory system.
        _prompt_builder (PromptBuilder): The component for constructing prompts.
    """

    def __init__(
        self,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        prompt_builder: PromptBuilder,
        memory_manager: MemoryManager,
        config: AgentConfig,
    ):
        """
        Initializes the BaseAgent.

        Args:
            llm: An instance of the LLM wrapper.
            tool_scheduler: An instance of the tool scheduler.
            prompt_builder: An instance of the prompt builder.
            memory_manager: An instance of the memory manager.
            config: The agent's configuration object.
        """
        self._llm = llm
        self._config = config
        self._tool_scheduler = tool_scheduler
        self._prompt_builder = prompt_builder
        self._memory_manager = memory_manager

    def run(self, user_prompt: str) -> AgentOutput:
        """
        Main entry point for the agent with built-in memory management.

        Orchestrates a full conversational turn by building the prompt,
        executing the think-act-observe loop, and storing results.

        Args:
            user_prompt: The input string from the user.

        Returns:
            The final result of the agent's execution.
        """
        messages = self._build_message_list(user_prompt)
        self._store_user_turn(user_prompt, messages)
        messages_before_think = len(messages)

        try:
            self._execute_thinking_loop(messages)
            final_message = self._get_final_message(messages)
            self._validate_final_message(final_message)

            new_messages = messages[messages_before_think:]
            self._store_messages_with_tools(new_messages)

            return self._create_agent_output(final_message, messages)

        except Exception as e:
            return self._handle_error(e)

    def _build_message_list(self, user_prompt: str) -> List[Message]:
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

    def _store_user_turn(self, user_prompt: str, messages: List[Message]) -> None:
        """
        Store the user turn with context information in memory.

        Args:
            user_prompt: The user's input.
            messages: The complete message list.
        """
        full_prompt_str = self._format_messages_for_storage(messages)
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

    def _execute_thinking_loop(self, messages: List[Message]) -> None:
        """
        Execute the think-act-observe loop.

        Args:
            messages: The message list to process.
        """
        for step in self._think(messages, max_turns=self._config.max_agent_turns):
            logger.debug("AGENT_RUN", "Think step", {"step": step})

    def _get_final_message(self, messages: List[Message]) -> Message:
        """
        Retrieve or generate the final message from the conversation.

        Args:
            messages: The complete message list.

        Returns:
            The final assistant message.

        Raises:
            AgentError: If the last message has an unexpected role.
        """
        last_message = messages[-1]

        if last_message["role"] == "tool":
            logger.info("AGENT_RUN", "Loop ended on tool result, querying for final response.")
            final_llm_response = self._llm.chat_completion(messages=messages)
            final_message = final_llm_response.choices[0].message
            messages.append(final_message)
            return final_message

        if last_message["role"] == "assistant":
            return last_message

        raise AgentError(f"Loop ended unexpectedly with role: {last_message['role']}")

    def _validate_final_message(self, final_message: Message) -> None:
        """
        Validate that the final message contains content.

        Args:
            final_message: The message to validate.

        Raises:
            AgentError: If the message is empty or has no content.
        """
        if not final_message or not final_message.get("content"):
            raise AgentError("Agent failed to produce a final content response.")

    def _create_agent_output(self, final_message: Message, messages: List[Message]) -> AgentOutput:
        """
        Create the final agent output object.

        Args:
            final_message: The final assistant message.
            messages: The complete message list.

        Returns:
            The formatted agent output.
        """
        history = self._memory_manager.get_conversation_history(
            max_turns=self._config.max_history_turns
        )

        output = AgentOutput(
            response=final_message["content"],
            metadata={"turn_count": len(history) // 2}
        )
        logger.info("AGENT_RUN", "Agent run completed successfully.")
        return output

    def _handle_error(self, error: Exception) -> AgentOutput:
        """
        Handle errors during agent execution.

        Args:
            error: The exception that occurred.

        Returns:
            An agent output object with error information.
        """
        logger.error("AGENT_RUN", f"Agent run failed: {error}")

        self._memory_manager.add_conversation_turn(
            role="assistant",
            content=f"An error occurred: {error}"
        )

        return AgentOutput(
            response=f"An error occurred: {error}",
            success=False,
            error=str(error)
        )

    def _think(
        self, messages: List[Message], max_turns: int = 10
    ) -> Generator[Dict[str, Any], None, Message]:
        """
        Core reasoning loop implementing the Think-Act-Observe pattern.

        Orchestrates LLM interaction and tool usage through a generator,
        yielding each step for observation by the caller.

        Args:
            messages: The current conversation history.
            max_turns: Maximum number of turns to prevent infinite loops.

        Yields:
            Dictionary representing current step (llm_response, tool_call, tool_results).

        Returns:
            Final message from the LLM containing the answer.

        Raises:
            AgentError: If maximum turns exceeded.
        """
        for turn in range(max_turns):
            logger.info("AGENT", f"Starting turn {turn + 1}/{max_turns}")

            assistant_message = self._get_llm_response(messages)
            messages.append(assistant_message)
            yield {"llm_response": assistant_message}

            if not assistant_message.get("tool_calls"):
                logger.info("AGENT", "No tool calls requested. Final response received.")
                return assistant_message

            tool_calls: List[ToolCall] = assistant_message["tool_calls"]
            yield {"tool_calls": tool_calls}

            tool_results = self._execute_and_store_tools(tool_calls, messages)
            yield {"tool_results": tool_results}

        raise AgentError(f"Agent exceeded maximum turns ({max_turns}).")

    def _get_llm_response(self, messages: List[Message]) -> Message:
        """
        Get response from LLM and convert to internal message format.

        Args:
            messages: Current conversation history.

        Returns:
            Converted assistant message in internal format.
        """
        llm_response = self._llm.chat(messages=messages, verbose=True)
        llm_raw_message = llm_response.choices[0].message

        return self._convert_llm_message(llm_raw_message)

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

    def _execute_and_store_tools(
        self, tool_calls: List[ToolCall], messages: List[Message]
    ) -> List[ToolResult]:
        """
        Execute tools and store their results in memory and messages.

        Args:
            tool_calls: List of tool calls to execute.
            messages: Message list to append results to.

        Returns:
            List of tool results.
        """
        tool_results = self._tool_scheduler.execute_tools(tool_calls)

        for tool_result in tool_results:
            self._store_single_tool_result(tool_result)
            self._append_tool_result_to_messages(tool_result, messages)

        return tool_results

    def _store_single_tool_result(self, tool_result: ToolResult) -> None:
        """
        Store a single tool result in memory.

        Args:
            tool_result: The tool result to store.
        """
        self._memory_manager.add_tool_result(
            tool_name=tool_result["tool_name"],
            result=tool_result["result"],
            success=tool_result["success"],
            execution_time=tool_result["execution_time"]
        )

    def _append_tool_result_to_messages(
        self, tool_result: ToolResult, messages: List[Message]
    ) -> None:
        """
        Append a tool result to the message list.

        Args:
            tool_result: The tool result to append.
            messages: The message list.
        """
        messages.append({
            "role": "tool",
            "tool_call_id": tool_result["tool_call_id"],
            "content": tool_result["result"],
        })

    def _format_messages_for_storage(self, messages: List[Message]) -> str:
        """
        Format messages list into OpenAI API format for storage.

        Args:
            messages: List of conversation messages.

        Returns:
            JSON-formatted string in OpenAI API format.
        """
        import json

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

    def _store_messages_with_tools(self, new_messages: List[Message]) -> None:
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

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self._config.name}'>"

