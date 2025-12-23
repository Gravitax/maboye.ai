"""
Modern Agent Implementation

Agent with iterative single-command execution workflow.
Uses TaskExecution to execute one command at a time.
"""

from core.logger import logger
from llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from tools.tool_base import ToolRegistry
from core.domain import AgentIdentity, AgentCapabilities
from core.services.memory_manager import MemoryManager
from core.services.context_manager import ContextManager
from agents.task_execution import TaskExecution
from agents.types import AgentOutput
from tools.tool_ids import ToolId
from core.prompt_builder import PromptBuilder, PromptRole


class Agent:
    """
    Modern agent implementation using iterative task execution.

    Workflow:
    1. Execute single command via TaskExecution
    2. Check command result (task_success, continue, error)
    3. Repeat until task success, error or max iterations reached

    The task execution coordinator handles:
    - Querying LLM for next command
    - Parsing JSON response
    - Executing single tool
    - Returning result with cmd status
    """

    def __init__(
        self,
        agent_identity: AgentIdentity,
        agent_capabilities: AgentCapabilities,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        tool_registry: ToolRegistry,
        memory_manager: MemoryManager,
    ):
        self._identity = agent_identity
        self._capabilities = agent_capabilities
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._memory_manager = memory_manager

        # Context manager for conversation history
        self._context_manager = ContextManager(memory_manager._memory_repository)

        # Prompt builder for constructing prompts
        self._prompt_builder = PromptBuilder()

        # Task execution coordinator (callable for single command execution)
        self._task_execution = TaskExecution(
            llm=llm,
            tool_scheduler=tool_scheduler,
            context_manager=self._context_manager
        )

    def run(self, task: str, system_prompt: str = "", user_prompt: str = "") -> AgentOutput:
        """
        Execute agent with iterative task execution workflow.

        Args:
            task: task description
            system_prompt: Additional system prompt (optional)
            user_prompt: Additional user prompt (optional)

        Returns:
            AgentOutput with final result
        """
        max_iterations = self._capabilities.max_reasoning_turns
        iteration = 0

        # Clear previous prompts
        self._prompt_builder.clear_prompts()

        # Build system prompt
        self._prompt_builder.add_line(PromptRole.SYSTEM, self._capabilities.system_prompt)
        if len(system_prompt) > 0: self._prompt_builder.add_line(PromptRole.SYSTEM, system_prompt)

        # Build initial user prompt with task and context
        self._prompt_builder.add_line(PromptRole.USER, task)
        if len(user_prompt) > 0: self._prompt_builder.add_line(PromptRole.USER, user_prompt)

        # Clear agent memory
        self._memory_manager.clear_agent_memory(self._identity.agent_id)

        result = AgentOutput(
            response="",
            success=False,
            error="not_started",
            agent_id=self._identity.agent_id
        )

        # Iterative execution loop
        while iteration < max_iterations:
            iteration += 1

            logger.info("AGENT", "iteration", {
                "iteration": iteration,
                "max_iterations": max_iterations
            })

            # Execute single command
            result = self._task_execution(
                agent=self,
                system_prompt=self._prompt_builder.get_prompt(PromptRole.SYSTEM),
                user_prompt=self._prompt_builder.get_prompt(PromptRole.USER)
            )

            result_str = f"\ncommand: {result.cmd}\narguments: {result.args}\noutput: {result.response}\nsuccess: {result.success}"
            logger.agent("AGENT", "output", result_str)

            # Save both agent input and output in memory
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="user",
                content=self._prompt_builder.get_prompt(PromptRole.USER)
            )
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="assistant",
                content=result_str
            )

            self._prompt_builder.clear_prompt(PromptRole.USER)
            if result.cmd in [ToolId.TASK_SUCCESS.value, ToolId.TASK_ERROR.value, ToolId.TASKS_COMPLETED.value]:
                return result
            elif not result.success:
                # Build failure continuation prompt with initial context preserved
                self._prompt_builder.add_line(PromptRole.USER, f"\nCommand: **{result.cmd} failed**. Analyze the failure context.")
                self._prompt_builder.add_line(PromptRole.USER, "If Global Completion is not met, and it is a fixable error, execute a **Corrected Approach**.")
            else:
                # Build success continuation prompt with initial context preserved
                self._prompt_builder.add_line(PromptRole.USER, f"\nCommand '{result.cmd}' executed successfully.")
                self._prompt_builder.add_line(PromptRole.USER, "If the CURRENT ASSIGNMENT is not yet fully complete, proceed to the next logical step.")
        # Max iterations reached
        result.error = "Max iterations reached"
        return result

    def get_identity(self) -> AgentIdentity:
        """Get agent identity."""
        return self._identity

    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities."""
        return self._capabilities
