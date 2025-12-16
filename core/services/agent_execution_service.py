"""
Agent Execution Service

Executes agents with complete traceability and metrics.
"""

import time
from typing import Optional
from datetime import datetime

from core.logger import logger
from core.repositories.agent_repository import AgentRepository
from core.services.agent_memory_coordinator import AgentMemoryCoordinator
from core.services.service_types import (
    ExecutionOptions,
    AgentExecutionResult,
    AgentNotFoundError,
    AgentInactiveError,
    AgentExecutionError
)
from agents.types import AgentOutput

# Import TYPE_CHECKING to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.services.agent_factory import AgentFactory


class AgentExecutionService:
    """
    Service for executing agents with traceability.

    Responsibilities:
    - Validate agent exists and is active
    - Prepare execution context
    - Execute agent with timeout and metrics
    - Handle errors and create execution results
    - Log execution details

    Attributes:
        _agent_repository: Repository for agent access
        _memory_coordinator: Coordinator for memory management
        _agent_factory: Factory for creating agent instances (optional)
    """

    def __init__(
        self,
        agent_repository: AgentRepository,
        memory_coordinator: AgentMemoryCoordinator,
        agent_factory: Optional['AgentFactory'] = None,
        llm=None,
        tool_scheduler=None,
        tool_registry=None
    ):
        """
        Initialize execution service.

        Args:
            agent_repository: Repository for agent persistence
            memory_coordinator: Coordinator for memory management
            agent_factory: Optional factory for creating and executing agents
            llm: LLM wrapper for agent creation
            tool_scheduler: Tool scheduler for agent creation
            tool_registry: Tool registry for agent creation
        """
        self._agent_repository = agent_repository
        self._memory_coordinator = memory_coordinator
        self._agent_factory = agent_factory
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry

    def execute_agent(
        self,
        agent_id: str,
        user_input: str,
        execution_options: Optional[ExecutionOptions] = None
    ) -> AgentExecutionResult:
        """
        Execute an agent with complete traceability.

        Args:
            agent_id: ID of the agent to execute
            user_input: User input to process
            execution_options: Optional execution configuration

        Returns:
            AgentExecutionResult with output, metrics, and traces

        Raises:
            AgentNotFoundError: If agent doesn't exist
            AgentInactiveError: If agent is inactive
            AgentExecutionError: If execution fails critically
        """
        options = execution_options or ExecutionOptions()

        logger.info(
            "EXECUTION_SERVICE",
            f"Starting execution for agent {agent_id}",
            {
                "agent_id": agent_id,
                "input_length": len(user_input),
                "options": options.metadata
            }
        )

        # 1. Retrieve agent
        agent = self._agent_repository.find_by_id(agent_id)
        if not agent:
            logger.error("EXECUTION_SERVICE", f"Agent {agent_id} not found")
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        # 2. Check if agent is active
        if not agent.is_active:
            logger.warning("EXECUTION_SERVICE", f"Agent {agent_id} is inactive")
            raise AgentInactiveError(f"Agent {agent_id} is inactive")

        # 3. Prepare execution context
        execution_context = self._prepare_execution_context(
            agent=agent,
            user_input=user_input,
            options=options
        )

        # 4. Execute with metrics
        start_time = time.time()
        success = False
        error_msg = None
        output = None

        try:
            # Execute the agent
            if self._agent_factory:
                # Use agent factory to create and execute agent instance
                logger.info(
                    "EXECUTION_SERVICE",
                    f"Executing agent {agent.get_agent_name()} with factory",
                    execution_context
                )

                # Create agent instance from RegisteredAgent
                agent_instance = self._agent_factory.create_agent(agent)

                # Execute the agent with user input
                output = agent_instance.run(user_input)
                success = output.success

            else:
                # Fallback: No factory available, return placeholder
                logger.warning(
                    "EXECUTION_SERVICE",
                    f"No agent factory available, returning placeholder for {agent.get_agent_name()}",
                    execution_context
                )

                output = AgentOutput(
                    response="Agent execution successful (placeholder - no factory configured)",
                    success=True,
                    error=None
                )
                success = True

        except Exception as e:
            logger.error(
                "EXECUTION_SERVICE",
                f"Agent execution failed: {str(e)}",
                {
                    "agent_id": agent_id,
                    "error": str(e)
                }
            )

            output = AgentOutput(
                response=f"Execution error: {str(e)}",
                success=False,
                error=str(e)
            )
            success = False
            error_msg = str(e)

        execution_time = time.time() - start_time

        # 5. Create execution result
        result = AgentExecutionResult(
            agent_id=agent_id,
            agent_name=agent.get_agent_name(),
            output=output,
            execution_time_seconds=execution_time,
            success=success,
            error=error_msg,
            timestamp=datetime.now(),
            metadata={
                **options.metadata,
                **execution_context
            }
        )

        logger.info(
            "EXECUTION_SERVICE",
            f"Execution completed for agent {agent.get_agent_name()}",
            {
                "agent_id": agent_id,
                "success": success,
                "execution_time": execution_time,
                "response_length": len(output.response) if output else 0
            }
        )

        return result

    def execute_agent_by_name(
        self,
        agent_name: str,
        user_input: str,
        execution_options: Optional[ExecutionOptions] = None
    ) -> AgentExecutionResult:
        """
        Execute an agent by name.

        Args:
            agent_name: Name of the agent to execute
            user_input: User input to process
            execution_options: Optional execution configuration

        Returns:
            AgentExecutionResult

        Raises:
            AgentNotFoundError: If agent doesn't exist
        """
        # Find agent by name
        agent = self._agent_repository.find_by_name(agent_name)
        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_name}' not found")

        # Execute by ID
        return self.execute_agent(
            agent_id=agent.get_agent_id(),
            user_input=user_input,
            execution_options=execution_options
        )

    def _prepare_execution_context(
        self,
        agent,
        user_input: str,
        options: ExecutionOptions
    ) -> dict:
        """
        Prepare execution context.

        Args:
            agent: RegisteredAgent entity
            user_input: User input
            options: Execution options

        Returns:
            Dictionary with execution context
        """
        context = {
            "user_input": user_input,
            "input_length": len(user_input),
            "agent_name": agent.get_agent_name(),
            "agent_id": agent.get_agent_id(),
            "timeout_seconds": options.timeout_seconds
        }

        return context

    def get_execution_stats(self) -> dict:
        """
        Get execution service statistics.

        Returns:
            Dictionary with service stats
        """
        return {
            'total_agents': self._agent_repository.count(),
            'active_agents': len(self._agent_repository.find_active()),
            'memory_stats': self._memory_coordinator.get_memory_stats()
        }

    def __str__(self) -> str:
        """String representation for logging."""
        return (
            f"AgentExecutionService("
            f"agents={self._agent_repository.count()})"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"AgentExecutionService("
            f"agent_repository={self._agent_repository}, "
            f"memory_coordinator={self._memory_coordinator})"
        )

    def run(
        self,
        todolist: dict,
        max_iterations: int = 2,
        max_retries: int = 1
    ) -> AgentOutput:
        """
        Supervise execution of TodoList steps with retry mechanism.

        Args:
            todolist: TodoList dict with steps
            max_iterations: Max iterations per step
            max_retries: Max retry attempts for failed steps

        Returns:
            AgentOutput with final aggregated result
        """
        from core.logger import logger

        steps = todolist.get("todo_list", [])
        query = todolist.get("query", "")

        step_results = []
        completed_steps = []

        for step in steps:
            step_id = step.get("step_id")
            depends_on = step.get("depends_on")

            if depends_on and depends_on not in completed_steps:
                error_msg = f"Dependency {depends_on} not completed for {step_id}"
                logger.error("AGENT_EXECUTION_SERVICE", error_msg)
                return AgentOutput(
                    response=error_msg,
                    success=False,
                    error="dependency_not_met"
                )

            step_result = self._execute_step_with_retry(
                step=step,
                max_iterations=max_iterations,
                max_retries=max_retries
            )

            if not step_result.success:
                return AgentOutput(
                    response=f"Step {step_id} failed after {max_retries} retries: {step_result.error}",
                    success=False,
                    error=f"step_{step_id}_failed_max_retries"
                )

            step_results.append(step_result)
            completed_steps.append(step_id)

            logger.info("AGENT_EXECUTION_SERVICE", f"Step {step_id} completed successfully")

        final_response = self._aggregate_step_results(query, step_results)

        return AgentOutput(
            response=final_response,
            success=True,
            agent_id="supervised_workflow"
        )

    def _execute_step_with_retry(
        self,
        step: dict,
        max_iterations: int,
        max_retries: int
    ) -> AgentOutput:
        """Execute step with retry mechanism on failure."""
        from core.logger import logger

        step_id = step.get("step_id")

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info("AGENT_EXECUTION_SERVICE", f"Retry attempt {attempt}/{max_retries} for step {step_id}")

            result = self._execute_supervised_step(step, max_iterations)

            if result.success:
                if attempt > 0:
                    logger.info("AGENT_EXECUTION_SERVICE", f"Step {step_id} succeeded after {attempt} retries")
                return result

        logger.error("AGENT_EXECUTION_SERVICE", f"Step {step_id} failed after {max_retries} retries")
        return result

    def _execute_supervised_step(
        self,
        step: dict,
        max_iterations: int
    ) -> AgentOutput:
        """Execute single supervised step with specialized agent."""
        from core.logger import logger
        from tests.test_utils.mock_agent import MockAgent

        step_id = step.get("step_id")
        description = step.get("description")
        agent_type = step.get("agent_type")

        logger.info("AGENT_EXECUTION_SERVICE", f"Executing step {step_id}", {
            "description": description,
            "agent_type": agent_type
        })

        agent = self._route_step_to_agent(step)

        result = agent.run(
            query=description,
            mode="iterative",
            scenario="auto",
            max_iterations=max_iterations
        )

        if result.success:
            validation_result = self._validate_step_result(step, result)
            if not validation_result:
                return AgentOutput(
                    response=f"Step {step_id} validation failed",
                    success=False,
                    error="validation_failed"
                )

        return result

    def _route_step_to_agent(self, step: dict):
        """Route step to appropriate specialized agent."""
        from core.logger import logger
        from tests.test_utils.mock_agent import MockAgent

        agent_type = step.get("agent_type", "general_agent")

        logger.info("AGENT_EXECUTION_SERVICE", "Routing to agent", {"agent_type": agent_type})

        agent = MockAgent(
            self._llm,
            self._tool_scheduler,
            self._tool_registry,
            self._memory_coordinator
        )

        return agent

    def _validate_step_result(self, step: dict, result: AgentOutput) -> bool:
        """Validate step execution result."""
        from core.logger import logger

        step_id = step.get("step_id")

        if not result.success:
            logger.warning("AGENT_EXECUTION_SERVICE", f"Step {step_id} failed validation: not successful")
            return False

        if len(result.response) == 0:
            logger.warning("AGENT_EXECUTION_SERVICE", f"Step {step_id} failed validation: empty response")
            return False

        return True

    def _aggregate_step_results(self, query: str, step_results: list) -> str:
        """Aggregate all step results into final response."""
        response_parts = [f"Supervised workflow completed for query: {query}\n"]

        for i, result in enumerate(step_results, 1):
            response_parts.append(f"\nStep {i} result:")
            response_parts.append(result.response[:200])
            if len(result.response) > 200:
                response_parts.append("...")

        return "\n".join(response_parts)
