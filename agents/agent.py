"""
Modern Agent Implementation

Agent with plan-based execution workflow.
Uses AgentExecution to manage execution logic.
"""

from core.logger import logger
from core.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from tools.tool_base import ToolRegistry
from core.domain import AgentIdentity, AgentCapabilities
from core.services.memory_manager import MemoryManager
from core.services.context_manager import ContextManager
from core.services.plan_execution_service import PlanExecutionService, PlanExecutionError
from core.services.agent_execution import AgentExecution
from agents.types import AgentOutput


class Agent:
    """
    Modern agent implementation using plan-based execution.

    Workflow:
    1. Build conversation messages with history
    2. Delegate to AgentExecution for plan execution
    3. Save results to memory and return output

    The execution coordinator handles:
    - Querying LLM for execution plans
    - Parsing and executing plans
    - Retry logic on errors
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

        # Plan execution service
        self.plan_execution_service = PlanExecutionService(tool_scheduler, self._tool_registry)

        # Context manager for conversation history
        self._context_manager = ContextManager(memory_manager._memory_repository)

        # Execution coordinator (handles plan execution logic)
        self._execution_coordinator = AgentExecution(
            llm=llm,
            plan_execution_service=self.plan_execution_service,
            memory=memory_manager
        )

        pass

    def run(self, user_prompt: str, system_prompt: str = "") -> AgentOutput:
        """
        Execute agent with plan-based workflow.

        Workflow:
        1. Build conversation messages with history
        2. Delegate to execution coordinator for plan execution with retry
        3. Save results and return output
        """
        if len(system_prompt) > 0:
            system_prompt += "\n" + system_prompt
        else:
            system_prompt = self._capabilities.system_prompt
        try:
            # Build conversation messages with history using context manager
            messages = self._context_manager.build_messages(
                agent_id=self._identity.agent_id,
                system_prompt=system_prompt,
                max_turns=self._capabilities.max_memory_turns
            )

            # Save user query
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="user",
                content=user_prompt
            )

            # Execute via coordinator (handles plan execution, retry logic, etc.)
            response = self._execution_coordinator.execute(
                messages=messages,
                user_prompt=user_prompt,
                agent_id=self._identity.agent_id,
                max_turns=self._capabilities.max_reasoning_turns,
                llm_temperature=self._capabilities.llm_temperature,
                llm_max_tokens=self._capabilities.llm_max_tokens
            )

            # Save final response
            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="assistant",
                content=response.response
            )
            return response

        except (PlanExecutionError, Exception) as e:
            return AgentOutput(
                response=f"Error: {str(e)}",
                success=False,
                error=str(e),
                agent_id=self._identity.agent_id
            )


    def get_identity(self) -> AgentIdentity:
        """Get agent identity."""
        return self._identity

    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities."""
        return self._capabilities

    def __repr__(self) -> str:
        return f"<Agent name='{self._identity.agent_name}' id='{self._identity.agent_id}'>"
