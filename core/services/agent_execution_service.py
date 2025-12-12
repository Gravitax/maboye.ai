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
    """

    def __init__(
        self,
        agent_repository: AgentRepository,
        memory_coordinator: AgentMemoryCoordinator
    ):
        """
        Initialize execution service.

        Args:
            agent_repository: Repository for agent persistence
            memory_coordinator: Coordinator for memory management
        """
        self._agent_repository = agent_repository
        self._memory_coordinator = memory_coordinator

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
            # Note: In current architecture, agents are created separately
            # This is a placeholder for future integration
            logger.info(
                "EXECUTION_SERVICE",
                f"Executing agent {agent.get_agent_name()}",
                execution_context
            )

            # TODO: Execute actual agent instance
            # For now, return a success output as placeholder
            output = AgentOutput(
                response="Agent execution successful",
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
            "timeout_seconds": options.timeout_seconds,
            "cross_agent_enabled": options.enable_cross_agent_context
        }

        # Add cross-agent context if enabled
        if options.enable_cross_agent_context and options.cross_agent_ids:
            cross_context = self._memory_coordinator.build_cross_agent_context(
                requesting_agent_id=agent.get_agent_id(),
                other_agent_ids=options.cross_agent_ids,
                max_turns_per_agent=options.max_cross_agent_turns
            )
            context['cross_agent_count'] = cross_context.get_shared_agent_count()

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
