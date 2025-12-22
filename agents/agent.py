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

        Returns:
            AgentOutput with final result
        """
        max_iterations = self._capabilities.max_reasoning_turns
        iteration = 0

        # Build system prompt
        if len(system_prompt) > 0:
            system_prompt = self._capabilities.system_prompt + '\n' + system_prompt
        else:
            system_prompt = self._capabilities.system_prompt
        # Build user prompt
        if len(user_prompt) > 0: user_prompt = '\n' + user_prompt
        user_prompt = task + user_prompt

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
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )

            result_str = f"command: {result.cmd}\narguments: {result.args}\noutput: {result.response}\nsuccess: {result.success}"
            logger.agent("AGENT", "output", result_str)

            # On prépare le contenu pour la mémoire en retirant les instructions de vérification
            # qui ne servent qu'au LLM pour l'étape suivante, mais polluent l'historique.
            memory_content = user_prompt
            split_marker = "VERIFICATION REQUIRED"
            # On ne garde que la partie avant le marqueur (ex: "Command 'ls' executed successfully.")
            memory_content = user_prompt.split(split_marker)[0].strip()

            # Save both agent input (cleaned) and output in memory
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="user",
                content=memory_content
            )
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="assistant",
                content=result_str
            )

            if result.cmd in [ToolId.TASK_SUCCESS.value, ToolId.TASK_ERROR.value, ToolId.TASKS_COMPLETED.value]:
                return result
            elif not result.success:
                # Cas d'échec : Gestion de l'Idempotence et de la Récupération
                user_prompt = (
                    f"Command: **{result.cmd} failed**. Analyze the failure context.\n"
                ) + self._context_manager.get_verification_prompt() + (
                    "**RECOVERY**: If Global Completion is not met, and it is a fixable error, execute a **Corrected Approach**.\n"
                )
            else:
                # Cas de succès technique : Continuité ou Erreur logique
                user_prompt = (
                    f"Command '{result.cmd}' executed successfully.\n"
                ) + self._context_manager.get_verification_prompt() + (
                    "**CONTINUE**: If the USER QUERY is not yet fully complete, proceed to the next logical step.\n"
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
