"""
TodoList Generator endpoint for orchestrator agent.
This endpoint simulates an orchestrator agent that generates a TodoList from user query.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from core.logger import logger

router = APIRouter()


class GenerateTodoListRequest(BaseModel):
    """Request for generating TodoList."""
    query: str
    context: Optional[Dict[str, Any]] = None


class TodoStep(BaseModel):
    """Single step in TodoList."""
    step_id: str
    description: str
    agent_type: str
    priority: int
    depends_on: Optional[str] = None
    metadata: Dict[str, Any] = {}


class TodoListResponse(BaseModel):
    """Response containing TodoList."""
    todo_list: List[TodoStep]
    query: str
    total_steps: int


def _extract_scenario_from_query(query: str) -> str:
    """Extract scenario from user query."""
    query_lower = query.lower()
    if "analyze" in query_lower and ("architecture" in query_lower or "codebase" in query_lower):
        return "analyze_codebase"
    elif "create" in query_lower or "implement" in query_lower:
        return "create_feature"
    elif "fix" in query_lower or "debug" in query_lower:
        return "fix_issue"
    return "simple_task"


def _generate_analyze_codebase_todolist(query: str) -> TodoListResponse:
    """Generate TodoList for codebase analysis scenario."""
    steps = [
        TodoStep(
            step_id="step_1",
            description="List project files and understand structure",
            agent_type="file_explorer",
            priority=1,
            depends_on=None,
            metadata={
                "complexity": "low",
                "estimated_tools": 2,
                "tools": ["list_files", "get_file_structure"]
            }
        ),
        TodoStep(
            step_id="step_2",
            description="Read main entry point and core modules",
            agent_type="file_reader",
            priority=2,
            depends_on="step_1",
            metadata={
                "complexity": "medium",
                "estimated_tools": 3,
                "tools": ["read_file"]
            }
        ),
        TodoStep(
            step_id="step_3",
            description="Analyze code patterns and architecture",
            agent_type="code_analyst",
            priority=3,
            depends_on="step_2",
            metadata={
                "complexity": "high",
                "estimated_tools": 2,
                "tools": ["code_search", "grep"]
            }
        )
    ]

    return TodoListResponse(
        todo_list=steps,
        query=query,
        total_steps=len(steps)
    )


def _generate_create_feature_todolist(query: str) -> TodoListResponse:
    """Generate TodoList for feature creation scenario."""
    steps = [
        TodoStep(
            step_id="step_1",
            description="Analyze existing code structure",
            agent_type="code_analyst",
            priority=1,
            depends_on=None,
            metadata={
                "complexity": "medium",
                "estimated_tools": 3
            }
        ),
        TodoStep(
            step_id="step_2",
            description="Create new feature files",
            agent_type="file_writer",
            priority=2,
            depends_on="step_1",
            metadata={
                "complexity": "high",
                "estimated_tools": 2,
                "requires_confirmation": True
            }
        ),
        TodoStep(
            step_id="step_3",
            description="Run tests to validate implementation",
            agent_type="test_runner",
            priority=3,
            depends_on="step_2",
            metadata={
                "complexity": "medium",
                "estimated_tools": 1,
                "tools": ["bash"]
            }
        )
    ]

    return TodoListResponse(
        todo_list=steps,
        query=query,
        total_steps=len(steps)
    )


def _generate_fix_issue_todolist(query: str) -> TodoListResponse:
    """Generate TodoList for bug fix scenario."""
    steps = [
        TodoStep(
            step_id="step_1",
            description="Search for error patterns in codebase",
            agent_type="error_finder",
            priority=1,
            depends_on=None,
            metadata={
                "complexity": "medium",
                "estimated_tools": 2,
                "tools": ["grep", "code_search"]
            }
        ),
        TodoStep(
            step_id="step_2",
            description="Read problematic files and analyze",
            agent_type="file_reader",
            priority=2,
            depends_on="step_1",
            metadata={
                "complexity": "medium",
                "estimated_tools": 2
            }
        ),
        TodoStep(
            step_id="step_3",
            description="Apply fix to identified files",
            agent_type="file_editor",
            priority=3,
            depends_on="step_2",
            metadata={
                "complexity": "high",
                "estimated_tools": 1,
                "requires_confirmation": True
            }
        )
    ]

    return TodoListResponse(
        todo_list=steps,
        query=query,
        total_steps=len(steps)
    )


def _generate_simple_task_todolist(query: str) -> TodoListResponse:
    """Generate TodoList for simple task scenario."""
    steps = [
        TodoStep(
            step_id="step_1",
            description="Execute basic operation",
            agent_type="general_agent",
            priority=1,
            depends_on=None,
            metadata={
                "complexity": "low",
                "estimated_tools": 1
            }
        )
    ]

    return TodoListResponse(
        todo_list=steps,
        query=query,
        total_steps=len(steps)
    )


def _route_to_scenario_handler(scenario: str, query: str) -> TodoListResponse:
    """Route to appropriate TodoList generator."""
    handlers = {
        "analyze_codebase": _generate_analyze_codebase_todolist,
        "create_feature": _generate_create_feature_todolist,
        "fix_issue": _generate_fix_issue_todolist
    }

    handler = handlers.get(scenario, _generate_simple_task_todolist)
    return handler(query)


@router.post("/chat/generate_todolist", response_model=TodoListResponse, tags=["Chat"])
def generate_todolist(request: GenerateTodoListRequest):
    """Generate TodoList from user query."""
    try:
        scenario = _extract_scenario_from_query(request.query)

        logger.info("BACKEND_MOCK", "Generating TodoList", {
            "query": request.query,
            "scenario": scenario
        })

        response = _route_to_scenario_handler(scenario, request.query)

        logger.info("BACKEND_MOCK", "TodoList generated", {
            "total_steps": response.total_steps,
            "scenario": scenario
        })

        return response

    except Exception as error:
        logger.error("BACKEND_MOCK", "TodoList generation error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))
