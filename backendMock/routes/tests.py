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
                description="Read tests/toto.py to understand structure",
                actions=[
                    ActionStep(
                        tool_name="read_file",
                        arguments={"file_path": "tests/toto.py"},
                        description="Read tests/toto.py contents"
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
                        arguments={"file_path": "./hello_world.py", "content": "print('hello _world')"},
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
                        arguments={"dir_path": "."},
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