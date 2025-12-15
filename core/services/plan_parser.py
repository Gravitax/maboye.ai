import json
from typing import Dict, Any, List
from core.domain.execution_plan import ExecutionPlan, ExecutionStep, ActionStep

class PlanParseError(Exception):
    """Custom exception for plan parsing errors."""
    pass

def parse_json_to_plan(json_data: str, user_query: str) -> ExecutionPlan:
    """
    Parses a JSON string into an ExecutionPlan object.

    Args:
        json_data: The JSON string representing the plan.
        user_query: The original user query.

    Returns:
        An ExecutionPlan object.

    Raises:
        PlanParseError: If the JSON is invalid or doesn't match the expected structure.
    """
    try:
        data = json.loads(json_data)
    except json.JSONDecodeError as e:
        raise PlanParseError(f"Invalid JSON format: {e}")

    if not isinstance(data, dict) or "steps" not in data:
        raise PlanParseError("Missing 'steps' key in plan JSON")

    try:
        steps_data = data["steps"]
        steps = []
        for step_data in steps_data:
            actions_data = step_data["actions"]
            actions = [
                ActionStep(
                    tool_name=action["tool_name"],
                    arguments=action["arguments"],
                    description=action.get("description", "")
                )
                for action in actions_data
            ]
            
            step = ExecutionStep(
                step_number=step_data["step_number"],
                description=step_data["description"],
                actions=actions,
                depends_on=step_data.get("depends_on")
            )
            steps.append(step)

        return ExecutionPlan(
            user_query=user_query,
            steps=steps,
            estimated_duration=data.get("estimated_duration"),
            requires_confirmation=data.get("requires_confirmation", True),
            metadata=data.get("metadata", {})
        )
    except KeyError as e:
        raise PlanParseError(f"Missing expected key in plan data: {e}")
    except TypeError as e:
        raise PlanParseError(f"Type error in plan data: {e}")
