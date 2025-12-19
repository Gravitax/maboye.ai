"""
Modern Agent Implementation

Agent with iterative single-command execution workflow.
Uses TaskExecution to execute one command at a time.
"""

from core.logger import logger
from core.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from tools.tool_base import ToolRegistry
from core.domain import AgentIdentity, AgentCapabilities
from core.services.memory_manager import MemoryManager
from core.services.context_manager import ContextManager
from agents.task_execution import TaskExecution
from agents.types import AgentOutput


class Agent:
    """
    Modern agent implementation using iterative task execution.

    Workflow:
    1. Execute single command via TaskExecution
    2. Check command result (task_completed, continue, error)
    3. Repeat until task completed or max iterations reached

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

        # Task execution coordinator (callable for single command execution)
        self._task_execution = TaskExecution(
            llm=llm,
            tool_scheduler=tool_scheduler,
            context_manager=self._context_manager
        )

    def run(self, user_prompt: str, system_prompt: str = "") -> AgentOutput:
        """
        Execute agent with iterative task execution workflow.

        Args:
            user_prompt: User input or task description
            system_prompt: Additional system prompt (optional)

        Returns:
            AgentOutput with final result
        """
        max_iterations = self._capabilities.max_reasoning_turns
        iteration = 0

        # Build system prompt
        if len(system_prompt) > 0:
            system_prompt = self._capabilities.system_prompt + "\n\n" + system_prompt
        else:
            system_prompt = self._capabilities.system_prompt

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
                user_prompt=user_prompt,
                system_prompt=system_prompt
            )

            logger.info("AGENT", "output", {
                "cmd": result.cmd,
                "result": result.response,
                "log": result.log
            })

            # Save both user prompt and agent output in memory after execution
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="user",
                content=user_prompt
            )
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="assistant",
                content=f"executed command: {result.cmd}\noutput: {result.response}\nsuccess: {result.success}"
            )

            if result.cmd == "task_completed":
                return result
            elif not result.success:
            # Continue with simple prompt - context is already in memory
                user_prompt = (
                    f"The command '{result.cmd}' failed.\n"
                    f"Error logs:\n{result.log}\n"
                    "Analyze the failure and execute a corrected approach."
                )
            else:
                user_prompt = (
                    f"The command '{result.cmd}' succeeded.\n"
                    "Determine the next logical step or use 'task_completed' if finished."
                )
        # Max iterations reached
        result.error = "Max iterations reached"
        return result

    def get_identity(self) -> AgentIdentity:
        """Get agent identity."""
        return self._identity

    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities."""
        return self._capabilities
