"""
Test routes for the Backend Mock API.
"""
from fastapi import APIRouter, HTTPException

from core.logger import logger
from backendMock.backendMock_types import (
    TestPlanRequest,
    TestPlanResponse,
    ActionStep,
    ExecutionStep,
)
# The BackendMock and its dependencies are no longer used here
# from backendMock.dependencies import get_backend_mock_dependency
# from backendMock.core_mock import BackendMock # Import BackendMock for type hinting

router = APIRouter()

_request_count_test: int = 0 # Local request count for tests

def generate_test_plan(request: TestPlanRequest) -> TestPlanResponse:
    """
    Generate a mock execution plan based on a test name.
    """
    global _request_count_test
    _request_count_test += 1
    logger.info("BACKEND_MOCK", "Test plan request received", {
        "test_name": request.test_name,
        "request_number": _request_count_test
    })

    if request.test_name == "read_file":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Read tests/execution_workflow/test_files/toto.py to understand structure",
                actions=[
                    ActionStep(
                        tool_name="read_file",
                        arguments={"file_path": "tests/execution_workflow/test_files/toto.py"},
                        description="Read tests/execution_workflow/test_files/toto.py contents"
                    )
                ]
            )
        ]
    elif request.test_name == "write_file":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Write an hello world program in python",
                actions=[
                    ActionStep(
                        tool_name="write_file",
                        arguments={"file_path": "tests/execution_workflow/generated/hello_world.py", "content": "print('hello _world')"},
                        description="Write hello_world.py contents"
                    )
                ]
            )
        ]
    elif request.test_name == "ls":
        steps = [
            ExecutionStep(
                step_number=1,
                description="List files in the current directory",
                actions=[
                    ActionStep(
                        tool_name="list_files",
                        arguments={"directory": "."},
                        description="Execute ls ."
                    )
                ]
            )
        ]
    elif request.test_name == "pwd":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Print the current working directory",
                actions=[
                    ActionStep(
                        tool_name="bash",
                        arguments={"command": "pwd"},
                        description="Execute pwd"
                    )
                ]
            )
        ]
    elif request.test_name == "read_modify_write":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Read the sample data file",
                actions=[
                    ActionStep(
                        tool_name="read_file",
                        arguments={"file_path": "tests/execution_workflow/test_files/sample_data.txt"},
                        description="Read sample_data.txt contents"
                    )
                ]
            ),
            ExecutionStep(
                step_number=2,
                description="Write modified content to new file",
                actions=[
                    ActionStep(
                        tool_name="write_file",
                        arguments={
                            "file_path": "tests/execution_workflow/generated/modified_data.txt",
                            "content": "Modified: Sample text file for testing read operations.\nModified: This file contains multiple lines.\nModified: Line 3 of the file.\n"
                        },
                        description="Write modified content"
                    )
                ],
                depends_on=1
            )
        ]
    elif request.test_name == "sequential_operations":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Create first test file",
                actions=[
                    ActionStep(
                        tool_name="write_file",
                        arguments={
                            "file_path": "tests/execution_workflow/generated/file1.txt",
                            "content": "Content of file 1"
                        },
                        description="Write file1.txt"
                    )
                ]
            ),
            ExecutionStep(
                step_number=2,
                description="Create second test file",
                actions=[
                    ActionStep(
                        tool_name="write_file",
                        arguments={
                            "file_path": "tests/execution_workflow/generated/file2.txt",
                            "content": "Content of file 2"
                        },
                        description="Write file2.txt"
                    )
                ],
                depends_on=1
            ),
            ExecutionStep(
                step_number=3,
                description="List generated files",
                actions=[
                    ActionStep(
                        tool_name="list_files",
                        arguments={"directory": "tests/execution_workflow/generated"},
                        description="List files in generated directory"
                    )
                ],
                depends_on=2
            )
        ]
    elif request.test_name == "multi_action_step":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Create multiple files in parallel",
                actions=[
                    ActionStep(
                        tool_name="write_file",
                        arguments={
                            "file_path": "tests/execution_workflow/generated/parallel1.txt",
                            "content": "Parallel file 1"
                        },
                        description="Write parallel1.txt"
                    ),
                    ActionStep(
                        tool_name="write_file",
                        arguments={
                            "file_path": "tests/execution_workflow/generated/parallel2.txt",
                            "content": "Parallel file 2"
                        },
                        description="Write parallel2.txt"
                    ),
                    ActionStep(
                        tool_name="write_file",
                        arguments={
                            "file_path": "tests/execution_workflow/generated/parallel3.txt",
                            "content": "Parallel file 3"
                        },
                        description="Write parallel3.txt"
                    )
                ]
            )
        ]
    elif request.test_name == "edit_file":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Edit existing file content",
                actions=[
                    ActionStep(
                        tool_name="edit_file",
                        arguments={
                            "file_path": "tests/execution_workflow/test_files/edit_target.txt",
                            "old_text": "To be replaced",
                            "new_text": "REPLACED TEXT"
                        },
                        description="Replace text in edit_target.txt"
                    )
                ]
            )
        ]
    elif request.test_name == "file_info":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Get file information",
                actions=[
                    ActionStep(
                        tool_name="file_info",
                        arguments={"file_path": "tests/execution_workflow/test_files/toto.py"},
                        description="Get info for toto.py"
                    )
                ]
            )
        ]
    elif request.test_name == "grep":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Search for pattern in file",
                actions=[
                    ActionStep(
                        tool_name="grep",
                        arguments={
                            "pattern": "ERROR",
                            "path": "tests/execution_workflow/test_files/grep_target.txt"
                        },
                        description="Search for ERROR in grep_target.txt"
                    )
                ]
            )
        ]
    elif request.test_name == "find_file":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Find files by name pattern",
                actions=[
                    ActionStep(
                        tool_name="find_file",
                        arguments={
                            "name_pattern": "*.txt",
                            "directory": "tests/execution_workflow/test_files"
                        },
                        description="Find all .txt files"
                    )
                ]
            )
        ]
    elif request.test_name == "get_file_structure":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Get directory structure",
                actions=[
                    ActionStep(
                        tool_name="get_file_structure",
                        arguments={
                            "directory": "tests/execution_workflow/test_files",
                            "max_depth": 2
                        },
                        description="Get structure of test_files directory"
                    )
                ]
            )
        ]
    elif request.test_name == "code_search":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Search for code pattern",
                actions=[
                    ActionStep(
                        tool_name="code_search",
                        arguments={
                            "pattern": "def calculate",
                            "directory": "tests/execution_workflow/test_files",
                            "file_pattern": "*.py"
                        },
                        description="Search for function definitions"
                    )
                ]
            )
        ]
    elif request.test_name == "git_status":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Check git repository status",
                actions=[
                    ActionStep(
                        tool_name="git_status",
                        arguments={},
                        description="Get git status"
                    )
                ]
            )
        ]
    elif request.test_name == "git_log":
        steps = [
            ExecutionStep(
                step_number=1,
                description="Get git commit history",
                actions=[
                    ActionStep(
                        tool_name="git_log",
                        arguments={"max_count": 5},
                        description="Get last 5 commits"
                    )
                ]
            )
        ]
    else:
        steps = []

    return TestPlanResponse(steps=steps)


@router.post("/tests", response_model=TestPlanResponse, tags=["Tests"])
def run_test(request: TestPlanRequest): # Removed backend_mock: BackendMock = Depends(get_backend_mock_dependency)
    """
    Generate a mock execution plan for testing.
    """
    try:
        return generate_test_plan(request)
    except Exception as error:
        logger.error("BACKEND_MOCK", "Test plan error", {"error": str(error)})
        raise HTTPException(status_code=500, detail=str(error))