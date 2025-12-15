import pytest
from core.orchestrator import Orchestrator
from core.llm_wrapper import LLMWrapperConfig
from agents.types import AgentOutput
import os

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
    user_input = "read_file" # This will be used by the MockAgent as test_name
    expected_file_content = "print(\"toto is here\")"
    
    # Read the content of tests/toto.py directly for comparison
    toto_py_path = os.path.join(os.path.dirname(__file__), "toto.py")
    with open(toto_py_path, "r") as f:
        actual_file_content_from_disk = f.read()

    output = orchestrator.process_user_input(user_input)
    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    assert len(memory_content) > 0, "Memory should not be empty after read_file test"
    
    # Assert tool call
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "read_file" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "read_file tool not found in context"
    assert expected_file_content in tool_turn.get("data", {}).get("content", ""), "toto.py content not found in memory"
    assert actual_file_content_from_disk == tool_turn.get("data", {}).get("content", ""), "Content from disk does not match memory"

def test_write_file_workflow(orchestrator: Orchestrator):
    """
    Test the 'write_file' execution workflow.
    """
    user_input = "write_file"
    expected_content = "print('hello _world')"
    expected_file_path = "./hello_world.py"

    output = orchestrator.process_user_input(user_input)
    assert output.success, f"write_file test failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turn = next((t for t in memory_content if t.get("data", {}).get("role") == "tool"), None)
    assert tool_turn is not None, "Tool execution not found in memory"
    assert "write_file" in tool_turn.get("data", {}).get("context", {}).get("tool_name", ""), "write_file tool not found in context"
    assert f"Successfully wrote to {expected_file_path}" in tool_turn.get("data", {}).get("content", ""), "Expected write confirmation not found"

    # Optional: Verify file content if possible (requires a way to read the file after writing)
    # For now, we trust the mock backend response indicates success.

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
    # The actual content of ls output can vary, so just check for non-empty content
    assert len(tool_turn.get("data", {}).get("content", "")) > 0, "ls output is empty"

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
    # Check if the content is the current working directory
    assert "/opt/eca/tools/maboye.ai" in tool_turn.get("data", {}).get("content", ""), "pwd output does not contain expected path"
