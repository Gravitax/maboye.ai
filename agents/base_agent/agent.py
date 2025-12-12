"""
Defines the abstract base class for all agents.

This module provides the core structure and reasoning loop for agents, ensuring a
consistent, scalable, and extensible architecture for creating specialized agents.
"""

from abc import ABC

from core.llm_wrapper.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from core.prompt_builder import PromptBuilder
from core.memory import MemoryManager
from tools.tool_base import ToolRegistry
from agents.types import AgentOutput
from agents.config import AgentConfig
from agents.base_agent.llm_message_manager import LLMMessageAgentManager
from agents.base_agent.tools_manager import ToolsAgentManager
from agents.base_agent.memory_agent_manager import MemoryAgentManager
from agents.base_agent.workflow_manager import WorkflowManager
from agents.base_agent.think_loop_manager import ThinkLoopManager


class BaseAgent(ABC):
    """
    Abstract Base Class for LLM-powered agents.

    This class provides a foundational structure for building specialized agents.
    It orchestrates the interaction between specialized managers that handle
    different aspects of agent execution (memory, tools, workflow, reasoning).

    The agent follows a clean separation of concerns:
    - LLMMessageAgentManager: Handles LLM message operations
    - ToolsAgentManager: Manages tool execution
    - MemoryAgentManager: Handles memory and message storage
    - WorkflowManager: Manages execution lifecycle
    - ThinkLoopManager: Executes the think-act-observe loop

    Attributes:
        _config (AgentConfig): Configuration specific to the agent.
        _llm_message_manager (LLMMessageAgentManager): Handles LLM message operations.
        _tools_manager (ToolsAgentManager): Handles tool execution and storage.
        _memory_agent_manager (MemoryAgentManager): Handles memory operations.
        _workflow_manager (WorkflowManager): Manages execution lifecycle.
        _think_loop_manager (ThinkLoopManager): Executes reasoning loop.
    """

    def __init__(
        self,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
        config: AgentConfig,
    ):
        """
        Initializes the BaseAgent with specialized managers.

        Args:
            llm: An instance of the LLM wrapper.
            tool_scheduler: An instance of the tool scheduler.
            tool_registry: The tool registry containing all available tools.
            memory_manager: An instance of the memory manager.
            config: The agent's configuration object.
        """
        self._config = config

        # Create agent-specific prompt builder with filtered tools and custom system prompt
        system_prompt = config.system_prompt or "You are a helpful AI assistant."

        # Handle allowed_tools:
        # - None: no tools available
        # - []: all tools available
        # - ["tool1", "tool2"]: only these tools available
        if config.tools is None:
            allowed_tools = None
        else:
            allowed_tools = config.get_tools()

        prompt_builder = PromptBuilder(
            system_prompt=system_prompt,
            tool_registry=tool_registry,
            allowed_tools=allowed_tools
        )

        # Initialize specialized managers
        self._llm_message_manager = LLMMessageAgentManager(llm)
        self._tools_manager = ToolsAgentManager(tool_scheduler, memory_manager, config)
        self._memory_agent_manager = MemoryAgentManager(
            memory_manager, prompt_builder, self._llm_message_manager, config
        )
        self._workflow_manager = WorkflowManager(
            memory_manager, self._llm_message_manager, config
        )
        self._think_loop_manager = ThinkLoopManager(
            self._llm_message_manager, self._tools_manager, config
        )

    def run(self, user_prompt: str) -> AgentOutput:
        """
        Main entry point for the agent with built-in memory management.

        Orchestrates a full conversational turn by delegating to specialized
        managers for each phase of execution.

        Args:
            user_prompt: The input string from the user.

        Returns:
            The final result of the agent's execution.
        """
        # Build initial context from history and user prompt
        messages = self._memory_agent_manager.build_message_list(user_prompt)
        self._memory_agent_manager.store_user_turn(user_prompt, messages)
        messages_before_think = len(messages)

        try:
            # Execute the think-act-observe reasoning loop
            self._think_loop_manager.execute_thinking_loop(messages)

            # Finalize and validate the response
            final_message = self._workflow_manager.get_final_message(messages)
            self._workflow_manager.validate_final_message(final_message)

            # Store all new messages with their tool interactions
            new_messages = messages[messages_before_think:]
            self._memory_agent_manager.store_messages_with_tools(new_messages)

            # Create and return the final output
            return self._workflow_manager.create_agent_output(final_message, messages)

        except Exception as e:
            # Handle any errors and create error output
            return self._workflow_manager.handle_error(e)

    def update_config(self, description: str = None, tools: list = None):
        """
        Update the agent's configuration with new description and/or tools.

        This method allows dynamic modification of the agent's capabilities
        by updating its description and available tools list.

        Args:
            description: New description summarizing the agent's role
            tools: New list of tool IDs the agent can use (ToolId enum or strings)

        Example:
            from tools.tool_ids import ToolId

            agent.update_config(
                description="A specialized file management agent",
                tools=[ToolId.READ_FILE, ToolId.WRITE_FILE, ToolId.EDIT_FILE]
            )
        """
        self._config.update(description=description, tools=tools)

    def get_config(self) -> AgentConfig:
        """
        Get the current agent configuration.

        Returns:
            The agent's current configuration object
        """
        return self._config

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self._config.name}'>"
