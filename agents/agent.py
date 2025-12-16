"""
Modern Agent Implementation

Agent with plan-based execution workflow.
Uses AgentExecutionCoordinator to manage execution logic.
"""

from core.logger import logger
from core.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from tools.tool_base import ToolRegistry
from core.domain import AgentIdentity, AgentCapabilities
from core.services.agent_memory_coordinator import AgentMemoryCoordinator
from core.services.agent_prompt_constructor import AgentPromptConstructor
from core.services.plan_execution_service import PlanExecutionService, PlanExecutionError
from core.services.agent_execution_coordinator import AgentExecutionCoordinator
from agents.types import AgentOutput


class Agent:
    """
    Modern agent implementation using plan-based execution.

    Workflow:
    1. Build conversation messages with history
    2. Delegate to AgentExecutionCoordinator for plan execution
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
        memory_coordinator: AgentMemoryCoordinator,
    ):
        self._identity = agent_identity
        self._capabilities = agent_capabilities
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._memory_coordinator = memory_coordinator

        # Plan execution service
        self.plan_execution_service = PlanExecutionService(tool_scheduler, self._tool_registry)

        # Prompt constructor
        self._prompt_constructor = AgentPromptConstructor(
            agent_capabilities=agent_capabilities,
            memory_coordinator=memory_coordinator,
            tool_registry=tool_registry
        )

        # Execution coordinator (handles plan execution logic)
        self._execution_coordinator = AgentExecutionCoordinator(
            llm=llm,
            plan_execution_service=self.plan_execution_service,
            memory_coordinator=memory_coordinator
        )

        logger.info("AGENT", f"Agent initialized: {agent_identity.agent_name}")

    def run(self, user_prompt: str) -> AgentOutput:
        """
        Execute agent with plan-based workflow.

        Workflow:
        1. Build conversation messages with history
        2. Delegate to execution coordinator for plan execution with retry
        3. Save results and return output
        """
        logger.info("AGENT", "Starting agent execution", {
            "agent_name": self._identity.agent_name,
            "input_length": len(user_prompt)
        })

        try:
            # 1. Prepare conversation context
            context = self._memory_coordinator.get_conversation_context(
                agent_identity=self._identity,
                max_turns=self._capabilities.max_memory_turns
            )
            messages = self._prompt_constructor.build_conversation_messages(context)
            messages.append({"role": "user", "content": user_prompt})

            # Save user query
            self._memory_coordinator.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="user",
                content=user_prompt
            )

            # 2. Execute via coordinator (handles plan execution, retry logic, etc.)
            response = self._execution_coordinator.execute_with_retry(
                messages=messages,
                user_query=user_prompt,
                agent_id=self._identity.agent_id,
                max_turns=self._capabilities.max_reasoning_turns,
                llm_temperature=self._capabilities.llm_temperature,
                llm_max_tokens=self._capabilities.llm_max_tokens
            )

            # Save final response
            self._memory_coordinator.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="assistant",
                content=response.response
            )

            logger.info("AGENT", "Agent execution completed", {
                "agent_name": self._identity.agent_name,
                "response_length": len(response.response),
                "success": response.success
            })
            return response

        except (PlanExecutionError, Exception) as e:
            logger.error("AGENT", "Agent execution failed", {
                "agent_name": self._identity.agent_name,
                "error": str(e)
            })
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
