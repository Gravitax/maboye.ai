"""
Defines the abstract base class for all agents.

This module provides the core structure and reasoning loop for agents, ensuring a
consistent, scalable, and extensible architecture for creating specialized agents.
"""

from abc import ABC
from typing import List, Dict, Any, Generator

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
        The main entry point for the agent, with built-in memory management.

        This method orchestrates a full conversational turn:
        1. Adds the user's prompt to conversation memory.
        2. Retrieves the recent history.
        3. Builds a complete prompt for the LLM.
        4. Executes the think-act-observe loop (_think).
        5. Adds the assistant's final response to memory.
        6. Returns the final output.

        Args:
            user_prompt: The input string from the user.

        Returns:
            The final result of the agent's execution.
        """
        # 1. Add user turn to memory
        self._memory_manager.add_conversation_turn(role="user", content=user_prompt)

        # 2. Get conversation history for the prompt
        history = self._memory_manager.get_conversation_history(
            max_turns=self._config.max_history_turns
        )

        # 3. Build the list of messages for the LLM
        messages = self._prompt_builder.build_from_history(history)
        
        # Keep track of message count before the think loop
        messages_before_think = len(messages)

        try:
            # 4. Run the thinking loop
            final_message: Message = None
            for step in self._think(messages, max_turns=self._config.max_agent_turns):
                logger.debug("AGENT_RUN", "Think step", {"step": step})

            # The _think loop mutates the `messages` list. The final message is the last one.
            last_message = messages[-1]

            if last_message["role"] == "tool":
                # If the loop ended on a tool result, get a final summary from the LLM
                logger.info("AGENT_RUN", "Loop ended on tool result, querying for final response.")
                final_llm_response = self._llm.chat_completion(messages=messages)
                final_message = final_llm_response.choices[0].message
                messages.append(final_message)
            elif last_message["role"] == "assistant":
                final_message = last_message
            else:
                 raise AgentError(f"Loop ended unexpectedly with role: {last_message['role']}")

            if not final_message or not final_message.get("content"):
                raise AgentError("Agent failed to produce a final content response.")

            # 5. Add newly generated messages (assistant and tool responses) to memory
            new_messages = messages[messages_before_think:]
            for msg in new_messages:
                # The user message is already in memory, so we only add assistant/tool messages
                if msg["role"] != "user":
                    self._memory_manager.add_conversation_turn(
                        role=msg["role"],
                        content=msg.get("content"),
                        metadata=msg # Store full message as metadata
                    )
            
            # 6. Format and return the output
            output = AgentOutput(
                response=final_message["content"],
                metadata={"turn_count": len(history) // 2}
            )
            logger.info("AGENT_RUN", "Agent run completed successfully.")
            return output

        except Exception as e:
            logger.error("AGENT_RUN", f"Agent run failed: {e}")
            # Add a failed response to memory to maintain context
            self._memory_manager.add_conversation_turn(
                role="assistant",
                content=f"An error occurred: {e}"
            )
            return AgentOutput(response=f"An error occurred: {e}", success=False, error=str(e))

    def _think(
        self, messages: List[Message], max_turns: int = 10
    ) -> Generator[Dict[str, Any], None, Message]:
        """
        The core reasoning loop of the agent (Think-Act-Observe).

        This generator function orchestrates the interaction between the LLM and the tools.
        It yields each step of the process (thought, tool call, tool result) to allow
        the caller (`run` method) to observe the agent's internal state.

        Args:
            messages: The current conversation history to start the loop with.
            max_turns: The maximum number of agent turns to prevent infinite loops.

        Yields:
            A dictionary representing the current step (e.g., llm_response, tool_call).

        Returns:
            The final message from the LLM containing the answer.
        """
        for turn in range(max_turns):
            logger.info("AGENT", f"Starting turn {turn + 1}/{max_turns}")

            # 1. THINK: Call the LLM with the current message history
            llm_response = self._llm.chat(messages=messages, verbose=True)
            
            # Convert the Pydantic LLMMessage to the internal TypedDict Message
            llm_raw_assistant_message = llm_response.choices[0].message
            converted_assistant_message: Message = {
                "role": llm_raw_assistant_message.role,
                "content": llm_raw_assistant_message.content,
            }
            if llm_raw_assistant_message.tool_calls:
                converted_tool_calls = []
                for llm_tool_call in llm_raw_assistant_message.tool_calls:
                    converted_tool_calls.append({
                        "id": llm_tool_call.id,
                        "name": llm_tool_call.function["name"],
                        "args": llm_tool_call.function["arguments"],
                    })
                converted_assistant_message["tool_calls"] = converted_tool_calls
            if llm_raw_assistant_message.tool_call_id:
                converted_assistant_message["tool_call_id"] = llm_raw_assistant_message.tool_call_id

            assistant_message = converted_assistant_message
            messages.append(assistant_message)
            yield {"llm_response": assistant_message}

            # 2. ACT: Check if the LLM wants to use a tool
            if not assistant_message.get("tool_calls"):
                logger.info("AGENT", "No tool calls requested. Final response received.")
                return assistant_message  # Final answer

            tool_calls: List[ToolCall] = assistant_message["tool_calls"]
            yield {"tool_calls": tool_calls}

            # 3. OBSERVE: Execute tools and gather results
            tool_results: List[ToolResult] = self._tool_scheduler.execute_tools(tool_calls)
            yield {"tool_results": tool_results}
            
            # Persist tool results to memory and append to conversation
            for tool_result in tool_results:
                self._memory_manager.add_tool_result(
                    tool_name=tool_result["tool_name"],
                    result=tool_result["result"],
                    success=tool_result["success"],
                    execution_time=tool_result["execution_time"]
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": tool_result["result"],
                })

        raise AgentError(f"Agent exceeded maximum turns ({max_turns}).")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self._config.name}'>"

