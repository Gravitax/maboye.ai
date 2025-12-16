"""
Iterative chat endpoint for simulating LLM iterative workflow.
This endpoint simulates a real LLM that responds with tool calls or text.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from core.logger import logger

router = APIRouter()


class ToolCall(BaseModel):
    """Tool call structure matching OpenAI format."""
    id: str
    type: str = "function"
    function: Dict[str, Any]


class Message(BaseModel):
    """Chat message structure."""
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None


class ChatIterativeRequest(BaseModel):
    """Request for iterative chat."""
    messages: List[Message]
    scenario: str = "default"


class ChatIterativeResponse(BaseModel):
    """Response from iterative chat."""
    role: str = "assistant"
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None


_conversation_states: Dict[str, Dict[str, Any]] = {}


def _extract_scenario_from_messages(messages: List[Message]) -> str:
    """Extract scenario name from user messages."""
    for msg in messages:
        if msg.role == "user" and msg.content:
            content_lower = msg.content.lower()
            if "fix the following error" in content_lower:
                return "fix_error"
            elif "generate_todolist" in content_lower or "generate todolist" in content_lower:
                return "generate_todolist"
            elif "find errors" in content_lower:
                return "find_errors"
            elif "supervised_error" in content_lower:
                return "supervised_error"
            elif "supervised_analyze" in content_lower:
                return "supervised_analyze"
            elif "supervised_simple" in content_lower:
                return "supervised_simple"
    return "default"


def _count_tool_results(messages: List[Message]) -> int:
    """Count how many tool results have been provided."""
    return sum(1 for msg in messages if msg.role == "tool")


def _get_last_tool_result(messages: List[Message]) -> Optional[str]:
    """Get the last tool result content."""
    for msg in reversed(messages):
        if msg.role == "tool":
            return msg.content
    return None


def _create_list_files_tool_call(call_id: str, directory: str) -> ToolCall:
    """Create tool call for listing files."""
    return ToolCall(
        id=call_id,
        type="function",
        function={
            "name": "list_files",
            "arguments": {"directory": directory}
        }
    )


def _create_read_file_tool_call(call_id: str, file_path: str) -> ToolCall:
    """Create tool call for reading file."""
    return ToolCall(
        id=call_id,
        type="function",
        function={
            "name": "read_file",
            "arguments": {"file_path": file_path}
        }
    )


def _generate_architecture_analysis_text() -> str:
    """Generate final architecture analysis text."""
    return """Based on my analysis of the codebase:

## Architecture Analysis

The project follows a domain-driven architecture with clear separation of concerns:

1. **Entry Point (main.py)**:
   - Initializes the orchestrator
   - Handles user input loop
   - Manages application lifecycle

2. **Core Layer (core/)**:
   - Orchestrator: Central coordinator for multi-agent system
   - LLM Wrapper: Abstraction over LLM API
   - Tool Scheduler: Manages tool execution
   - Memory: Conversation and context management

3. **Agents Layer (agents/)**:
   - Agent base class with planning and execution modes
   - Identity and capabilities management
   - Support for reasoning loops

4. **Tools Layer (tools/)**:
   - File operations: read, write, edit
   - Search operations: grep, find, code search
   - Bash operations: command execution, git operations

The architecture enables flexible agent behavior with proper separation between infrastructure, domain logic, and tools."""


def _generate_supervised_analyze_response(
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Simulate analyze architecture workflow."""
    if tool_results_count == 0:
        return ChatIterativeResponse(
            role="assistant",
            content="I'll analyze the architecture by first exploring the project structure.",
            tool_calls=[_create_list_files_tool_call("call_001", ".")]
        )

    if tool_results_count == 1:
        return ChatIterativeResponse(
            role="assistant",
            content="Now let me read the main entry point.",
            tool_calls=[_create_read_file_tool_call("call_002", "main.py")]
        )

    if tool_results_count == 2:
        return ChatIterativeResponse(
            role="assistant",
            content="Let me also check the core orchestrator.",
            tool_calls=[_create_read_file_tool_call("call_003", "core/orchestrator.py")]
        )

    return ChatIterativeResponse(
        role="assistant",
        content=_generate_architecture_analysis_text(),
        tool_calls=None
    )


def _create_grep_tool_call(call_id: str, pattern: str, path: str) -> ToolCall:
    """Create tool call for grep search."""
    return ToolCall(
        id=call_id,
        type="function",
        function={
            "name": "grep",
            "arguments": {"pattern": pattern, "path": path}
        }
    )


def _create_bash_tool_call(call_id: str, command: str) -> ToolCall:
    """Create tool call for bash command."""
    return ToolCall(
        id=call_id,
        type="function",
        function={
            "name": "bash",
            "arguments": {"command": command}
        }
    )


def _generate_summary_text(content_length: int) -> str:
    """Generate file summary text."""
    return f"""Here is a summary of the file:

The file contains project documentation explaining the purpose and structure of the codebase.
It describes the main features and how to get started with the project.

Key points extracted:
- Multi-agent system architecture
- Support for various tools and operations
- Modular and extensible design

Total content length: {content_length} characters."""


def _generate_supervised_simple_response(
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Simulate read and summarize workflow."""
    if tool_results_count == 0:
        return ChatIterativeResponse(
            role="assistant",
            content="I'll read the file to summarize it.",
            tool_calls=[_create_read_file_tool_call("call_101", "README.md")]
        )

    last_result = _get_last_tool_result(messages)
    content_length = len(last_result) if last_result else 0

    return ChatIterativeResponse(
        role="assistant",
        content=_generate_summary_text(content_length),
        tool_calls=None
    )


def _generate_error_report_text() -> str:
    """Generate error analysis report text."""
    return """Error Analysis Report:

I've completed the error search across the codebase. Here are the findings:

1. **ERROR occurrences**: Found in logging statements and error handling code
   - These are intentional error handling patterns
   - No unexpected errors detected

2. **FIXME comments**: Found several TODO items
   - Division by zero handling needs attention
   - Some edge cases in file operations

Recommendation: Review FIXME comments and prioritize based on criticality."""


def _generate_find_errors_response(
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Simulate find errors workflow."""
    if tool_results_count == 0:
        return ChatIterativeResponse(
            role="assistant",
            content="I'll search for ERROR patterns in the codebase.",
            tool_calls=[_create_grep_tool_call("call_201", "ERROR", ".")]
        )

    if tool_results_count == 1:
        return ChatIterativeResponse(
            role="assistant",
            content="Now let me search for FIXME comments.",
            tool_calls=[_create_grep_tool_call("call_202", "FIXME", ".")]
        )

    return ChatIterativeResponse(
        role="assistant",
        content=_generate_error_report_text(),
        tool_calls=None
    )


def _generate_default_response(
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Simulate default workflow."""
    if tool_results_count == 0:
        return ChatIterativeResponse(
            role="assistant",
            content="Let me check the current directory.",
            tool_calls=[_create_bash_tool_call("call_301", "pwd")]
        )

    return ChatIterativeResponse(
        role="assistant",
        content="Task completed successfully. All operations executed without errors.",
        tool_calls=None
    )


def _generate_todolist_from_query(query: str) -> str:
    """Generate TodoList JSON based on query."""
    if "supervised_error" in query:
        return """{
  "todo_list": [
    {
      "step_id": "step_1",
      "description": "First step that succeeds",
      "agent_type": "general_agent",
      "priority": 1,
      "depends_on": null,
      "metadata": {
        "complexity": "low"
      }
    },
    {
      "step_id": "step_2",
      "description": "supervised_error",
      "agent_type": "error_agent",
      "priority": 2,
      "depends_on": "step_1",
      "metadata": {
        "complexity": "high",
        "will_fail": true
      }
    },
    {
      "step_id": "step_3",
      "description": "Third step that should not execute",
      "agent_type": "general_agent",
      "priority": 3,
      "depends_on": "step_2",
      "metadata": {
        "complexity": "low"
      }
    }
  ],
  "query": \"""" + query + """\",
  "total_steps": 3
}"""
    elif "supervised_analyze" in query:
        return """{
  "todo_list": [
    {
      "step_id": "step_1",
      "description": "List project files and understand structure",
      "agent_type": "file_explorer",
      "priority": 1,
      "depends_on": null,
      "metadata": {
        "complexity": "low",
        "estimated_tools": 2
      }
    },
    {
      "step_id": "step_2",
      "description": "Read main entry point and core modules",
      "agent_type": "file_reader",
      "priority": 2,
      "depends_on": "step_1",
      "metadata": {
        "complexity": "medium",
        "estimated_tools": 3
      }
    },
    {
      "step_id": "step_3",
      "description": "Analyze code patterns and architecture",
      "agent_type": "code_analyst",
      "priority": 3,
      "depends_on": "step_2",
      "metadata": {
        "complexity": "high",
        "estimated_tools": 2
      }
    }
  ],
  "query": \"""" + query + """\",
  "total_steps": 3
}"""
    elif "supervised_simple" in query:
        return """{
  "todo_list": [
    {
      "step_id": "step_1",
      "description": "Execute task",
      "agent_type": "general_agent",
      "priority": 1,
      "depends_on": null,
      "metadata": {
        "complexity": "low",
        "estimated_tools": 1
      }
    }
  ],
  "query": \"""" + query + """\",
  "total_steps": 1
}"""
    else:
        return None

def _generate_generate_todolist_response(
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Generate TodoList from user query."""
    user_query = ""
    for msg in messages:
        if msg.role == "user" and msg.content:
            user_query = msg.content
            break

    # Extract actual query from "generate_todolist: <query>" format
    if "generate_todolist:" in user_query.lower():
        actual_query = user_query.split(":", 1)[1].strip()
    else:
        actual_query = user_query

    todolist_json = _generate_todolist_from_query(actual_query)

    # If no todolist is needed for this simple query, return a clear message
    if todolist_json is None:
        return ChatIterativeResponse(
            role="assistant",
            content="No TodoList needed for this simple query.",
            tool_calls=None
        )

    return ChatIterativeResponse(
        role="assistant",
        content=todolist_json,
        tool_calls=None
    )


def _generate_supervised_error_response(
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Simulate an error scenario."""
    return ChatIterativeResponse(
        role="assistant",
        content="ERROR: Simulated failure in step execution. This step intentionally failed for testing error handling.",
        tool_calls=None
    )


def _generate_fix_error_response(
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Simulate successful error correction."""
    return ChatIterativeResponse(
        role="assistant",
        content="Error fixed successfully. The step has been corrected and can now proceed.",
        tool_calls=None
    )


def _route_to_scenario_handler(
    scenario: str,
    messages: List[Message],
    tool_results_count: int
) -> ChatIterativeResponse:
    """Route request to appropriate scenario handler."""
    handlers = {
        "fix_error": _generate_fix_error_response,
        "supervised_error": _generate_supervised_error_response,
        "supervised_analyze": _generate_supervised_analyze_response,
        "supervised_simple": _generate_supervised_simple_response,
        "generate_todolist": _generate_generate_todolist_response,
        "find_errors": _generate_find_errors_response
    }

    handler = handlers.get(scenario, _generate_default_response)
    return handler(messages, tool_results_count)


@router.post("/tests/iterative", response_model=ChatIterativeResponse, tags=["Tests"])
def test_iterative(request: ChatIterativeRequest):
    """Simulate iterative LLM chat with tool calls."""
    try:
        scenario = request.scenario
        if scenario == "auto":
            scenario = _extract_scenario_from_messages(request.messages)

        tool_results_count = _count_tool_results(request.messages)

        logger.info("BACKEND_MOCK", "Iterative chat request", {
            "scenario": scenario,
            "message_count": len(request.messages),
            "tool_results_count": tool_results_count
        })

        response = _route_to_scenario_handler(scenario, request.messages, tool_results_count)

        logger.info("BACKEND_MOCK", "Iterative chat response", {
            "has_tool_calls": response.tool_calls is not None,
            "is_final": response.tool_calls is None
        })

        return response

    except Exception as error:
        logger.error("BACKEND_MOCK", "Iterative chat error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))
