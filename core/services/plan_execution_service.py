from dataclasses import dataclass, field
from typing import List, Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from tools.tool_base import ToolRegistry
from core.domain.execution_plan import ExecutionPlan, ExecutionStep
from core.tool_scheduler import ToolScheduler
from core.logger import logger
from agents.types import ToolCall

class PlanExecutionError(Exception):
    """Custom exception for plan execution errors."""
    pass

@dataclass
class ActionResult:
    tool_name: str
    success: bool
    result: Any = None
    error: Optional[str] = None

@dataclass
class StepExecutionResult:
    step_number: int
    success: bool
    action_results: List[ActionResult] = field(default_factory=list)
    error: Optional[str] = None

@dataclass
class PlanExecutionResult:
    plan_id: str
    success: bool
    completed_steps: List[StepExecutionResult] = field(default_factory=list)
    error: Optional[str] = None

class PlanExecutionService:
    """
    Executes action plans step by step.

    Responsibilities:
    - Execute each step in order
    - Collect results
    - Handle errors and rollback if needed
    - Track execution state
    """

    def __init__(
        self,
        tool_scheduler: ToolScheduler,
        tool_registry: 'ToolRegistry',
        allow_dangerous: bool = False
    ):
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._allow_dangerous = allow_dangerous
        self._execution_history: List[PlanExecutionResult] = []

    def execute_plan(
        self,
        plan: ExecutionPlan,
        confirm_dangerous: bool = False
    ) -> PlanExecutionResult:
        """
        Execute complete plan step by step.

        Args:
            plan: ExecutionPlan to execute
            confirm_dangerous: User confirmed dangerous actions

        Returns:
            PlanExecutionResult with all step results
        """
        logger.info("PLAN_EXECUTION_SERVICE", "------------------------------ start")
        if plan.is_dangerous(self._tool_registry) and not confirm_dangerous:
            raise PlanExecutionError(
                "Plan contains dangerous actions and requires confirmation"
            )

        step_results = []

        for step in plan.steps:
            if step.depends_on is not None:
                if not self._dependency_satisfied(step.depends_on, step_results):
                    raise PlanExecutionError(
                        f"------------------------------ Dependency {step.depends_on} not satisfied for step {step.step_number}"
                    )

            step_result = self._execute_step(step)
            step_results.append(step_result)

            if not step_result.success:
                logger.error("PLAN_EXECUTION_SERVICE", f"------------------------------ Step {step.step_number} failed: {step_result.error}")
                return PlanExecutionResult(
                    plan_id=plan.plan_id,
                    completed_steps=step_results,
                    success=False,
                    error=f"Step {step.step_number} failed: {step_result.error}"
                )

        logger.info("PLAN_EXECUTION_SERVICE", "------------------------------ Plan executed successfully")
        return PlanExecutionResult(
            plan_id=plan.plan_id,
            completed_steps=step_results,
            success=True
        )

    def _execute_step(self, step: ExecutionStep) -> StepExecutionResult:
        """Execute single step with all its actions"""
        action_results = []
        logger.info("PLAN_EXECUTION_SERVICE", f"---------- Executing step {step.step_number}: {step.description}")

        tool_calls_for_scheduler = []
        for action in step.actions:
            tool_calls_for_scheduler.append(ToolCall(
                id=f"{action.tool_name}-{step.step_number}", # Unique ID for the tool call
                name=action.tool_name,
                args=action.arguments
            ))
        
        # Execute all actions in the step together
        tool_results = self._tool_scheduler.execute_tools(tool_calls_for_scheduler)

        for i, action in enumerate(step.actions):
            tool_result = tool_results[i]
            if tool_result["success"]:
                logger.info("PLAN_EXECUTION_SERVICE", f"Action {action.tool_name} completed successfully", {"result_preview": str(tool_result['result'])[:50]})
                action_results.append(ActionResult(
                    tool_name=action.tool_name,
                    success=True,
                    result=tool_result['result']
                ))
            else:
                logger.error("PLAN_EXECUTION_SERVICE", f"Action {action.tool_name} failed: {tool_result['result']}", {"arguments": action.arguments})
                action_results.append(ActionResult(
                    tool_name=action.tool_name,
                    success=False,
                    error=tool_result['result']
                ))
                # Stop step on first error
                return StepExecutionResult(
                    step_number=step.step_number,
                    success=False,
                    action_results=action_results,
                    error=tool_result['result']
                )

        return StepExecutionResult(
            step_number=step.step_number,
            success=True,
            action_results=action_results
        )

    def _dependency_satisfied(self, step_number: int, results: List[StepExecutionResult]) -> bool:
        """Check if a dependency is satisfied."""
        for result in results:
            if result.step_number == step_number and result.success:
                return True
        return False
