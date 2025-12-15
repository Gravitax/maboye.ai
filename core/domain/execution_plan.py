from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid

@dataclass(frozen=True)
class ActionStep:
    """Single action to execute"""
    tool_name: str
    arguments: Dict[str, Any]
    description: str

@dataclass(frozen=True)
class ExecutionStep:
    """Step containing one or more actions"""
    step_number: int
    description: str
    actions: List[ActionStep]
    depends_on: Optional[int] = None  # Previous step dependency

from core.logger import logger
@dataclass(frozen=True)
class ExecutionPlan:
    """Complete execution plan from LLM"""
    user_query: str
    steps: List[ExecutionStep]
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    estimated_duration: Optional[str] = None
    requires_confirmation: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_dangerous(self, tool_registry) -> bool:
        """Check if any action is marked dangerous"""
        logger.info("EXECUTION_PLAN", "Checking for dangerous tools", {"tool_registry": tool_registry})
        for step in self.steps:
            for action in step.actions:
                tool = tool_registry.get_tool(action.tool_name)
                if tool and tool.is_dangerous:
                    logger.warning("EXECUTION_PLAN", f"Dangerous tool found: {action.tool_name}")
                    return True
        return False
