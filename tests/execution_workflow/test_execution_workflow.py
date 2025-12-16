import pytest
from core.orchestrator import Orchestrator
from core.llm_wrapper import LLMWrapperConfig
from agents.types import AgentOutput
import os
import json

# Fixture for Orchestrator to ensure a clean state for each test
@pytest.fixture
def orchestrator():
    llm_config = LLMWrapperConfig(
        base_url="http://localhost:8000",
        api_service="",
        embed_service=""
    )
    orch = Orchestrator(llm_config=llm_config)
    # Clear memory after each test
    orch.reset_conversation()
    return orch

def test_read_file_workflow(orchestrator: Orchestrator):
    """
    Test the 'read_file' execution workflow.
    """
    user_input = "read_file"
    expected_file_content = "print(\"toto is here\")"

    # Read the content of test_files/toto.py directly for comparison
    toto_py_path = os.path.join(os.path.dirname(__file__), "test_files", "toto.py")
    with open(toto_py_path, "r") as f:
        actual_file_content_from_disk = f.read()

    output = orchestrator.process_user_input(user_input)
    assert output.success, f"read_file test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    assert len(memory_content) > 0, "Memory should not be empty after read_file test"

    # Assert tool call
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, f"Tool execution not found in memory. Memory content: {memory_content}"
    assert "read_file" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "read_file tool not found in context"
    assert expected_file_content in tool_turn.get("data", {}).get("content", ""), "toto.py content not found in memory"
    assert actual_file_content_from_disk == tool_turn.get("data", {}).get("content", ""), "Content from disk does not match memory"

def test_write_file_workflow(orchestrator: Orchestrator):
    """
    Test the 'write_file' execution workflow.
    """
    user_input = "write_file"
    expected_content = "print('hello _world')"
    expected_file_path = "tests/execution_workflow/generated/hello_world.py"

    output = orchestrator.process_user_input(user_input)
    assert output.success, f"write_file test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "write_file" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "write_file tool not found in context"
    assert f"Successfully wrote to {expected_file_path}" in tool_turn.get("data", {}).get("content", ""), "Expected write confirmation not found"

    # Verify the file was actually created and has correct content
    assert os.path.exists(expected_file_path), f"File {expected_file_path} was not created"
    with open(expected_file_path, "r") as f:
        actual_content = f.read()
    assert actual_content == expected_content, f"File content mismatch. Expected: {expected_content}, Got: {actual_content}"

def test_ls_workflow(orchestrator: Orchestrator):
    """
    Test the 'ls' execution workflow.
    """
    user_input = "ls"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"ls test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "list_files" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "list_files tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert len(content) > 0, "ls output is empty"

    try:
        ls_data = json.loads(content)
        assert isinstance(ls_data, list), "ls output should be a list"
        assert len(ls_data) > 0, "ls output list is empty"
    except json.JSONDecodeError:
        pass

def test_pwd_workflow(orchestrator: Orchestrator):
    """
    Test the 'pwd' execution workflow.
    """
    user_input = "pwd"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"pwd test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "bash" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "bash tool not found in context"
    content = tool_turn.get("data", {}).get("content", "")
    assert "maboye.ai" in content, f"pwd output does not contain expected path. Got: {content}"


def test_read_modify_write_workflow(orchestrator: Orchestrator):
    """
    Test multi-step workflow: read, modify, and write.
    """
    user_input = "read_modify_write"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"read_modify_write test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) == 2, f"Expected 2 tool executions, got {len(tool_turns)}"

    read_turn = tool_turns[0]
    assert "read_file" in read_turn.get("data", {}).get("context", {}).get("tool_name", ""), "First tool should be read_file"
    assert "Sample text file" in read_turn.get("data", {}).get("content", ""), "Read content not found"

    write_turn = tool_turns[1]
    assert "write_file" in write_turn.get("data", {}).get("context", {}).get("tool_name", ""), "Second tool should be write_file"

    output_file_path = "tests/execution_workflow/generated/modified_data.txt"
    assert os.path.exists(output_file_path), f"Modified file {output_file_path} was not created"
    with open(output_file_path, "r") as f:
        content = f.read()
    assert "Modified:" in content, "Modified prefix not found in output file"


def test_sequential_operations_workflow(orchestrator: Orchestrator):
    """
    Test sequential multi-step operations with dependencies.
    """
    user_input = "sequential_operations"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"sequential_operations test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) == 3, f"Expected 3 tool executions, got {len(tool_turns)}"

    assert "write_file" in tool_turns[0].get("data", {}).get("context", {}).get("tool_name", ""), "First tool should be write_file"
    assert "write_file" in tool_turns[1].get("data", {}).get("context", {}).get("tool_name", ""), "Second tool should be write_file"
    assert "list_files" in tool_turns[2].get("data", {}).get("context", {}).get("tool_name", ""), "Third tool should be list_files"

    file1_path = "tests/execution_workflow/generated/file1.txt"
    file2_path = "tests/execution_workflow/generated/file2.txt"
    assert os.path.exists(file1_path), f"File {file1_path} was not created"
    assert os.path.exists(file2_path), f"File {file2_path} was not created"

    ls_content_str = tool_turns[2].get("data", {}).get("content", "")
    try:
        ls_content = json.loads(ls_content_str)
        file_names = [item.get("name", "") for item in ls_content if isinstance(item, dict)]
        assert "file1.txt" in file_names or "file2.txt" in file_names, f"Created files not found in ls output. Found: {file_names}"
    except json.JSONDecodeError:
        assert "file1.txt" in ls_content_str or "file2.txt" in ls_content_str, f"Created files not found in ls output: {ls_content_str}"


def test_multi_action_step_workflow(orchestrator: Orchestrator):
    """
    Test single step with multiple parallel actions.
    """
    user_input = "multi_action_step"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"multi_action_step test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) == 3, f"Expected 3 tool executions, got {len(tool_turns)}"

    for tool_turn in tool_turns:
        assert "write_file" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "All tools should be write_file"

    parallel_files = [
        "tests/execution_workflow/generated/parallel1.txt",
        "tests/execution_workflow/generated/parallel2.txt",
        "tests/execution_workflow/generated/parallel3.txt"
    ]

    for file_path in parallel_files:
        assert os.path.exists(file_path), f"File {file_path} was not created"

    with open(parallel_files[0], "r") as f:
        assert "Parallel file 1" == f.read(), "Content mismatch in parallel1.txt"
    with open(parallel_files[1], "r") as f:
        assert "Parallel file 2" == f.read(), "Content mismatch in parallel2.txt"
    with open(parallel_files[2], "r") as f:
        assert "Parallel file 3" == f.read(), "Content mismatch in parallel3.txt"


def test_edit_file_workflow(orchestrator: Orchestrator):
    """
    Test edit_file tool execution.
    """
    edit_file_path = "tests/execution_workflow/test_files/edit_target.txt"
    original_content = "Line 1: Original content\nLine 2: To be replaced\nLine 3: Final line\n"

    with open(edit_file_path, "w") as f:
        f.write(original_content)

    user_input = "edit_file"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"edit_file test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "edit_file" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "edit_file tool not found in context"

    edited_file_path = "tests/execution_workflow/test_files/edit_target.txt"
    with open(edited_file_path, "r") as f:
        content = f.read()
    assert "REPLACED TEXT" in content, "Text was not replaced correctly"
    assert "To be replaced" not in content, "Old text still present"


def test_file_info_workflow(orchestrator: Orchestrator):
    """
    Test file_info tool execution.
    """
    user_input = "file_info"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"file_info test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "file_info" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "file_info tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert len(content) > 0, "file_info output is empty"
    assert "size" in content.lower() or "toto.py" in content, "Expected file info not found"


def test_grep_workflow(orchestrator: Orchestrator):
    """
    Test grep tool execution.
    """
    user_input = "grep"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"grep test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "grep" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "grep tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert "ERROR" in content, "Pattern ERROR not found in grep results"


def test_find_file_workflow(orchestrator: Orchestrator):
    """
    Test find_file tool execution.
    """
    user_input = "find_file"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"find_file test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "find_file" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "find_file tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert ".txt" in content, "No .txt files found in find_file results"


def test_get_file_structure_workflow(orchestrator: Orchestrator):
    """
    Test get_file_structure tool execution.
    """
    user_input = "get_file_structure"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"get_file_structure test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "get_file_structure" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "get_file_structure tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert len(content) > 0, "file structure output is empty"


def test_code_search_workflow(orchestrator: Orchestrator):
    """
    Test code_search tool execution.
    """
    user_input = "code_search"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"code_search test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "code_search" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "code_search tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert "def calculate" in content, "Function definition not found in code_search results"


def test_git_status_workflow(orchestrator: Orchestrator):
    """
    Test git_status tool execution.
    """
    user_input = "git_status"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"git_status test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "git_status" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "git_status tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert len(content) > 0, "git_status output is empty"


def test_git_log_workflow(orchestrator: Orchestrator):
    """
    Test git_log tool execution.
    """
    user_input = "git_log"
    output = orchestrator.process_user_input(user_input)
    assert output.success, f"git_log test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "git_log" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "git_log tool not found in context"

    content = tool_turn.get("data", {}).get("content", "")
    assert len(content) > 0, "git_log output is empty"
