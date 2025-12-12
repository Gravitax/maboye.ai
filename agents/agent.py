"""
Modern Agent Implementation

Refactored agent that uses the new domain-driven architecture directly.
No longer depends on legacy MemoryManager or PromptBuilder.
"""

from core.logger import logger
from core.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from tools.tool_base import ToolRegistry
from core.domain import AgentIdentity, AgentCapabilities
from core.services import AgentMemoryCoordinator, AgentPromptConstructor
from agents.types import AgentOutput


class Agent:
    """
    Modern agent implementation using domain-driven architecture.

    Uses:
    - AgentIdentity for agent identification
    - AgentCapabilities for constraints and permissions
    - AgentMemoryCoordinator for memory management
    - AgentPromptConstructor for prompt building
    - ToolScheduler for tool execution
    """

    def __init__(
        self,
        agent_identity: AgentIdentity,
        agent_capabilities: AgentCapabilities,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        tool_registry: ToolRegistry,
        memory_coordinator: AgentMemoryCoordinator,
    ):
        """
        Initialize agent with domain components.

        Args:
            agent_identity: Agent identity (ID and name)
            agent_capabilities: Agent capabilities and constraints
            llm: LLM wrapper for inference
            tool_scheduler: Tool scheduler for execution
            tool_registry: Registry of available tools
            memory_coordinator: Memory coordinator for conversation history
        """
        self._identity = agent_identity
        self._capabilities = agent_capabilities
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._memory_coordinator = memory_coordinator

        # Create prompt constructor
        self._prompt_constructor = AgentPromptConstructor(
            agent_capabilities=agent_capabilities,
            memory_coordinator=memory_coordinator,
            tool_registry=tool_registry
        )

        logger.info("AGENT", f"Agent initialized: {agent_identity.agent_name}")

    def run(self, user_prompt: str) -> AgentOutput:
        """
        Execute agent with user input.

        Args:
            user_prompt: User's input message

        Returns:
            AgentOutput with response and metadata
        """
        logger.info("AGENT", "Starting agent execution", {
            "agent_name": self._identity.agent_name,
            "input_length": len(user_prompt)
        })

        try:
            # 1. Get conversation context
            context = self._memory_coordinator.get_conversation_context(
                agent_identity=self._identity,
                max_turns=self._capabilities.max_memory_turns
            )

            # 2. Build messages with prompt constructor
            messages = self._prompt_constructor.build_conversation_messages(context)

            # 3. Add user message
            messages.append({
                "role": "user",
                "content": user_prompt
            })

            # 4. Save user turn
            self._memory_coordinator.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="user",
                content=user_prompt
            )

            # 5. Think loop (reasoning with tool calls)
            final_response = self._execute_reasoning_loop(messages)

            # 6. Save assistant response
            self._memory_coordinator.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="assistant",
                content=final_response
            )

            logger.info("AGENT", "Agent execution completed", {
                "agent_name": self._identity.agent_name,
                "response_length": len(final_response)
            })

            return AgentOutput(
                response=final_response,
                success=True
            )

        except Exception as e:
            logger.error("AGENT", "Agent execution failed", {
                "agent_name": self._identity.agent_name,
                "error": str(e)
            })
            return AgentOutput(
                response=f"Error: {str(e)}",
                success=False,
                error=str(e)
            )

    def _execute_reasoning_loop(self, messages: list) -> str:
        """
        Execute the think-act-observe reasoning loop.

        Args:
            messages: List of messages

        Returns:
            Final response text
        """
        max_turns = self._capabilities.max_reasoning_turns

        for turn in range(max_turns):
            logger.info("AGENT", f"Reasoning turn {turn + 1}/{max_turns}")

            # Call LLM
            response = self._llm.chat(messages, verbose=True)

            # Extract message from response (first choice)
            message = response.choices[0].message if response.choices else None
            if not message:
                logger.error("AGENT", "No message in LLM response")
                return "Error: No response from LLM"

            # Check for tool calls
            tool_calls = message.tool_calls if message.tool_calls else []

            if not tool_calls:
                # No tool calls, final response
                content = message.content or ""
                logger.info("AGENT", "Final response received (no tool calls)")
                return content

            # Add assistant message with tool calls (convert to dict format)
            tool_calls_dict = []
            for tc in tool_calls:
                tool_calls_dict.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": tc.function
                })

            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls_dict
            })

            # Execute tools and add results
            for tool_call in tool_calls:
                tool_name = tool_call.function.get("name")
                tool_args = tool_call.function.get("arguments", {})
                tool_id = tool_call.id

                logger.info("AGENT", f"Executing tool: {tool_name}")

                # Check authorization
                if not self._capabilities.can_use_tool(tool_name):
                    result = f"Error: Tool '{tool_name}' not authorized"
                    logger.warning("AGENT", f"Tool not authorized: {tool_name}")
                else:
                    # Execute tool
                    result = self._tool_scheduler.execute_tool(tool_name, tool_args)

                # Add tool result message
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": str(result)
                })

        # Max turns reached, return last message
        logger.warning("AGENT", f"Max reasoning turns ({max_turns}) reached")
        last_content = messages[-1].get("content", "Max reasoning turns reached")
        return str(last_content)

    def get_identity(self) -> AgentIdentity:
        """Get agent identity."""
        return self._identity

    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities."""
        return self._capabilities

    def __repr__(self) -> str:
        return f"<Agent name='{self._identity.agent_name}' id='{self._identity.agent_id}'>"
