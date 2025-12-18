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

    def execute(
        self,
        messages: list,
        user_prompt: str,
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
            user_prompt: Original user query
            agent_id: Agent identifier
            max_turns: Maximum retry attempts
            llm_temperature: LLM temperature setting
            llm_max_tokens: LLM max tokens setting

        Returns:
            AgentOutput with execution result
        """
        for turn in range(max_turns):
            if turn == 0:
                messages.append({
                    "role": "user",
                    "content": user_prompt
                })

            llm_response = self._llm.chat(
                messages,
                verbose=True,
                temperature=llm_temperature,
                max_tokens=llm_max_tokens
            )

            message = llm_response.choices[0].message if llm_response.choices else None
            if not message:
                return AgentOutput(
                    response="Error: No response from LLM",
                    success=False,
                    error="no_llm_response",
                    agent_id=agent_id
                )

            # Parse response to ExecutionPlan
            execution_plan = self._parse_llm_response_to_plan(message, user_prompt)

            if execution_plan is None:
                content = message.content or ""
                return AgentOutput(
                    response=content,
                    success=True,
                    agent_id=agent_id
                )

            # Log execution plan as JSON
            self._log_execution_plan_json(execution_plan)

            # Check for dangerous tools and ask confirmation
            confirm_dangerous = self._check_dangerous_and_confirm(execution_plan)

            if not confirm_dangerous:
                return AgentOutput(
                    response="Execution cancelled by user",
                    success=False,
                    error="user_cancelled_dangerous_tools",
                    agent_id=agent_id
                )

            # Execute plan
            plan_result = self._plan_execution_service.execute_plan(
                execution_plan,
                confirm_dangerous=confirm_dangerous
            )

            # Log execution results
            self._log_execution_results(plan_result)

            # Log step status
            if plan_result.success:
                logger.info("STEP_STATUS", "Success")
            else:
                logger.error("STEP_STATUS", f"Failed: {plan_result.error}")

            # Check if execution succeeded
            if plan_result.success:
                response = self._format_success_response(plan_result)
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

        # Max turns reached
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
            ExecutionPlan if tool_calls or JSON content present, None otherwise
        """
        # Try parsing tool_calls first
        if message.tool_calls:
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

            if steps:
                return ExecutionPlan(user_query=user_query, steps=steps)

        # Try parsing JSON from content
        if message.content:
            plan = self._parse_json_plan_from_content(message.content, user_query)
            if plan:
                return plan
        return None

    def _parse_json_plan_from_content(self, content: str, user_query: str) -> Optional[ExecutionPlan]:
        """
        Parse execution plan from JSON in message content.

        Args:
            content: Message content containing JSON
            user_query: Original user query

        Returns:
            ExecutionPlan if valid JSON found, None otherwise
        """
        import json
        import re

        try:
            content_stripped = content.strip()

            # Extract JSON from markdown code blocks if wrapped
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content_stripped, re.DOTALL)
            if json_match:
                content_stripped = json_match.group(1).strip()

            # Remove timestamp prefix if present
            content_stripped = re.sub(r'^\[\d{2}:\d{2}:\d{2}\]\s*', '', content_stripped)

            plan_data = json.loads(content_stripped)

            if "steps" not in plan_data:
                return None

            steps = []
            for step_data in plan_data["steps"]:
                actions = []
                for action_data in step_data.get("actions", []):
                    action = ActionStep(
                        tool_name=action_data.get("tool_name"),
                        arguments=action_data.get("arguments", {}),
                        description=action_data.get("description", "")
                    )
                    actions.append(action)

                step = ExecutionStep(
                    step_number=step_data.get("step_number"),
                    description=step_data.get("description", ""),
                    actions=actions
                )
                steps.append(step)

            if not steps:
                return None

            return ExecutionPlan(user_query=user_query, steps=steps)

        except json.JSONDecodeError:
            return None
        except Exception as e:
            return None

    def _log_execution_plan_json(self, execution_plan: ExecutionPlan) -> None:
        """Log execution plan as complete JSON."""
        import json

        plan_dict = {
            "steps": []
        }

        for step in execution_plan.steps:
            step_dict = {
                "step_number": step.step_number,
                "description": step.description,
                "actions": []
            }
            for action in step.actions:
                action_dict = {
                    "tool_name": action.tool_name,
                    "arguments": action.arguments,
                    "description": action.description
                }
                step_dict["actions"].append(action_dict)
            plan_dict["steps"].append(step_dict)

        plan_json = json.dumps(plan_dict, indent=2, ensure_ascii=False)
        logger.info("EXECUTION_PLAN", f"\n{plan_json}")

    def _log_execution_results(self, plan_result: PlanExecutionResult) -> None:
        """Log execution results in readable format."""
        for step_result in plan_result.completed_steps:
            for action_result in step_result.action_results:
                status = "OK" if action_result.success else "FAILED"
                result_str = str(action_result.result)

                # Format result based on type
                if len(result_str) > 300:
                    result_preview = result_str[:300] + "..."
                else:
                    result_preview = result_str

                logger.info("TOOL_EXEC", f"{action_result.tool_name}: {status}")
                if action_result.success:
                    logger.info("TOOL_RESULT", f"{result_preview}")
                else:
                    logger.error("TOOL_ERROR", f"{result_preview}")

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

    def _check_dangerous_and_confirm(self, execution_plan: ExecutionPlan) -> bool:
        """
        Check if plan contains dangerous tools and ask user confirmation.

        Args:
            execution_plan: Plan to check

        Returns:
            True if user confirms or no dangerous tools, False otherwise
        """
        tool_registry = self._plan_execution_service._tool_registry

        if not execution_plan.is_dangerous(tool_registry):
            return True

        dangerous_tools = []
        for step in execution_plan.steps:
            for action in step.actions:
                tool = tool_registry.get_tool(action.tool_name)
                if tool and tool.is_dangerous:
                    dangerous_tools.append({
                        "name": action.tool_name,
                        "args": action.arguments
                    })

        if not dangerous_tools:
            return True

        logger.warning("EXECUTION_PLAN", "Dangerous tool(s) detected")

        for tool_info in dangerous_tools:
            args_str = ", ".join(f"{k}={v}" for k, v in tool_info["args"].items())
            print(f"  - {tool_info['name']}({args_str})")

        try:
            response = input("\nAre you sure you want to execute these dangerous commands? (yes/no): ")
            return response.lower() in ['yes', 'y']
        except (KeyboardInterrupt, EOFError):
            return False
