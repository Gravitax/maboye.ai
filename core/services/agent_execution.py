"""
Agent Execution Coordinator

Manages the plan-based execution workflow for agents.
Handles LLM querying, plan parsing, execution, and retry logic.
"""

from typing import Optional
from core.logger import logger
from core.domain import ExecutionPlan, ExecutionStep, ActionStep
from core.services.plan_execution_service import PlanExecutionService, PlanExecutionResult
from core.services.memory_manager import MemoryManager
from agents.types import AgentOutput


class AgentExecution:
    """
    Coordinates plan-based execution workflow for agents.

    Responsibilities:
    - Query LLM for execution plans
    - Parse LLM responses into ExecutionPlan
    - Execute plans via PlanExecutionService
    - Handle retry logic on errors
    - Save execution results to memory
    """

    def __init__(
        self,
        llm,
        plan_execution_service: PlanExecutionService,
        memory: MemoryManager
    ):
        """
        Initialize execution coordinator.

        Args:
            llm: LLM wrapper for querying
            plan_execution_service: Service for executing plans
            memory: Coordinator for memory management
        """
        self._llm = llm
        self._plan_execution_service = plan_execution_service
        self._memory = memory

    def execute_with_retry(
        self,
        messages: list,
        user_query: str,
        agent_id: str,
        max_turns: int,
        llm_temperature: float,
        llm_max_tokens: int
    ) -> AgentOutput:
        """
        Execute plan-based workflow with retry on errors.

        Workflow per turn:
        1. Query LLM for execution plan
        2. Parse response to ExecutionPlan
        3. Execute plan with PlanExecutionService
        4. If success: return result
        5. If error: add error context and retry

        Args:
            messages: Conversation messages
            user_query: Original user query
            agent_id: Agent identifier
            max_turns: Maximum retry attempts
            llm_temperature: LLM temperature setting
            llm_max_tokens: LLM max tokens setting

        Returns:
            AgentOutput with execution result
        """
        for turn in range(max_turns):
            logger.info("EXECUTION_COORDINATOR", f"Plan execution turn {turn + 1}/{max_turns}")

            # messages.append({
            #     "role": "user",
            #     "content": user_query
            # })
            # Query LLM for execution plan
            llm_response = self._llm.chat(
                messages,
                verbose=True,
                temperature=llm_temperature,
                max_tokens=llm_max_tokens
            )

            message = llm_response.choices[0].message if llm_response.choices else None
            if not message:
                logger.error("EXECUTION_COORDINATOR", "No message in LLM response")
                return AgentOutput(
                    response="Error: No response from LLM",
                    success=False,
                    error="no_llm_response",
                    agent_id=agent_id
                )

            # Parse response to ExecutionPlan
            execution_plan = self._parse_llm_response_to_plan(message, user_query)

            if execution_plan is None:
                # LLM returned text response (no plan)
                content = message.content or ""
                logger.info("EXECUTION_COORDINATOR", "Text response received (no execution plan)")
                return AgentOutput(
                    response=content,
                    success=True,
                    agent_id=agent_id
                )

            logger.info("EXECUTION_COORDINATOR", f"Executing plan with {len(execution_plan.steps)} steps")

            # Execute plan
            plan_result = self._plan_execution_service.execute_plan(
                execution_plan,
                confirm_dangerous=True
            )

            # Save execution results to memory
            self._save_plan_execution_to_memory(plan_result, agent_id)

            # Check if execution succeeded
            if plan_result.success:
                response = self._format_success_response(plan_result)
                logger.info("EXECUTION_COORDINATOR", "Plan execution succeeded")
                return AgentOutput(
                    response=response,
                    success=True,
                    agent_id=agent_id
                )

            # Execution failed - prepare retry with error context
            error_message = self._format_error_for_retry(plan_result)
            messages.append({
                "role": "system",
                "content": f"Execution failed: {error_message}. Please provide a corrected plan."
            })

            logger.warning("EXECUTION_COORDINATOR", f"Plan execution failed, retrying...", {
                "error": error_message,
                "turn": turn + 1
            })

        # Max turns reached
        logger.error("EXECUTION_COORDINATOR", f"Max turns ({max_turns}) reached without success")
        return AgentOutput(
            response=f"Failed to execute successfully after {max_turns} attempts",
            success=False,
            error="max_turns_reached",
            agent_id=agent_id
        )

    def _parse_llm_response_to_plan(
        self,
        message,
        user_query: str
    ) -> Optional[ExecutionPlan]:
        """
        Parse LLM response to ExecutionPlan.

        Args:
            message: LLM message object
            user_query: Original user query

        Returns:
            ExecutionPlan if tool_calls present, None otherwise
        """
        # If no tool_calls, it's a text response
        if not message.tool_calls:
            return None

        # Parse tool_calls into ExecutionPlan
        steps = []
        for idx, tool_call in enumerate(message.tool_calls):
            action = ActionStep(
                tool_name=tool_call.function.get("name"),
                arguments=tool_call.function.get("arguments", {}),
                description=f"Execute {tool_call.function.get('name')}"
            )
            step = ExecutionStep(
                step_number=idx + 1,
                description=f"Step {idx + 1}: {tool_call.function.get('name')}",
                actions=[action]
            )
            steps.append(step)

        if not steps:
            return None

        logger.info("EXECUTION_COORDINATOR", f"Parsed {len(steps)} steps from LLM response")
        return ExecutionPlan(user_query=user_query, steps=steps)

    def _save_plan_execution_to_memory(
        self,
        plan_result: PlanExecutionResult,
        agent_id: str
    ) -> None:
        """
        Save plan execution results to memory.

        Args:
            plan_result: Execution result from PlanExecutionService
            agent_id: Agent identifier
        """
        for step_result in plan_result.completed_steps:
            for action_result in step_result.action_results:
                self._memory.save_conversation_turn(
                    agent_id=agent_id,
                    role="tool",
                    content=str(action_result.result),
                    metadata={
                        "tool_name": action_result.tool_name,
                        "success": action_result.success
                    }
                )

    def _format_success_response(self, plan_result: PlanExecutionResult) -> str:
        """
        Format successful execution result into response.

        Args:
            plan_result: Successful execution result

        Returns:
            Formatted response string
        """
        results = []
        for step_result in plan_result.completed_steps:
            for action_result in step_result.action_results:
                result_preview = str(action_result.result)[:200]
                results.append(f"{action_result.tool_name}: {result_preview}")

        if not results:
            return "Plan executed successfully (no output)"

        return "\n".join(results)

    def _format_error_for_retry(self, plan_result: PlanExecutionResult) -> str:
        """
        Format error message for retry.

        Args:
            plan_result: Failed execution result

        Returns:
            Error message string
        """
        if plan_result.error:
            return plan_result.error

        # Find failed step
        for step_result in plan_result.completed_steps:
            if not step_result.success:
                return f"Step {step_result.step_number} failed: {step_result.error}"

        return "Unknown error"
