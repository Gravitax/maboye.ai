"""
Tests for iterative agent workflow.

These tests validate the complete iterative workflow where:
1. Agent receives query
2. LLM responds with tool_calls or final text
3. Agent executes tools and returns results
4. Loop continues until final text response or termination condition
"""
import pytest
from core.orchestrator import Orchestrator
from core.llm_wrapper import LLMWrapperConfig


@pytest.fixture
def orchestrator():
    """Create orchestrator with mock backend."""
    llm_config = LLMWrapperConfig(
        base_url="http://localhost:8000",
        api_service="",
        embed_service=""
    )
    orch = Orchestrator(llm_config=llm_config)
    orch.reset_conversation()
    return orch


def test_iterative_analyze_architecture(orchestrator: Orchestrator):
    """Test iterative workflow for architecture analysis."""
    output = orchestrator.process_user_input_iterative("analyze architecture")

    assert output.success, f"Analyze architecture failed: {output.error}"
    assert "Architecture Analysis" in output.response, "Expected analysis section not found"
    assert "Entry Point" in output.response or "main.py" in output.response, "Entry point not analyzed"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) >= 3, f"Expected at least 3 tool executions, got {len(tool_turns)}"

    tool_names = [
        t.get("metadata", {}).get("tool_name")
        for t in tool_turns
    ]

    assert "list_files" in tool_names, f"list_files tool not executed. Found: {tool_names}"
    assert "read_file" in tool_names, f"read_file tool not executed. Found: {tool_names}"


def test_iterative_read_summarize(orchestrator: Orchestrator):
    """Test iterative workflow for reading and summarizing."""
    output = orchestrator.process_user_input_iterative("read and summarize README.md")

    assert output.success, f"Read and summarize failed: {output.error}"
    assert "summary" in output.response.lower(), "Summary not found in response"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) == 1, f"Expected 1 tool execution, got {len(tool_turns)}"

    tool_name = tool_turns[0].get("metadata", {}).get("tool_name")
    assert tool_name == "read_file", f"Expected read_file, got {tool_name}"


def test_iterative_find_errors(orchestrator: Orchestrator):
    """Test iterative workflow for finding errors."""
    output = orchestrator.process_user_input_iterative("find errors in codebase")

    assert output.success, f"Find errors failed: {output.error}"
    assert "Error Analysis" in output.response or "ERROR" in output.response, "Error analysis not found"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) >= 2, f"Expected at least 2 tool executions, got {len(tool_turns)}"

    tool_names = [
        t.get("metadata", {}).get("tool_name")
        for t in tool_turns
    ]

    assert "grep" in tool_names, f"grep tool not executed. Found: {tool_names}"


def test_iterative_default_scenario(orchestrator: Orchestrator):
    """
    Test iterative workflow for default scenario.

    Expected flow:
    1. bash pwd
    2. Final text response
    """
    output = orchestrator.process_user_input_iterative("simple task")

    assert output.success, f"Default scenario failed: {output.error}"
    assert len(output.response) > 0, "Empty response received"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) >= 1, f"Expected at least 1 tool execution, got {len(tool_turns)}"


def test_iterative_max_iterations(orchestrator: Orchestrator):
    """
    Test that max iterations limit is enforced.

    This test would need a special scenario that doesn't terminate naturally,
    but for now we just verify the mechanism works with analyze_architecture.
    """
    output = orchestrator.process_user_input_iterative("analyze architecture", max_iterations=5)

    assert output.success or output.error == "max_iterations", "Expected success or max_iterations error"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    assert len(tool_turns) <= 5, f"Tool executions exceeded max iterations: {len(tool_turns)}"


def test_iterative_memory_persistence(orchestrator: Orchestrator):
    """
    Test that all interactions are properly saved to memory.
    """
    output = orchestrator.process_user_input_iterative("read and summarize README.md")

    assert output.success, f"Task failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)

    roles = [t.get("data", {}).get("role") for t in memory_content]

    assert "user" in roles, "User query not saved in memory"
    assert "tool" in roles, "Tool results not saved in memory"
    assert "assistant" in roles, "Final response not saved in memory"

    user_turns = [t for t in memory_content if t.get("data", {}).get("role") == "user"]
    assert len(user_turns) >= 1, "User query missing from memory"

    final_turn = memory_content[-1]
    assert final_turn.get("data", {}).get("role") == "assistant", "Last turn should be assistant response"


def test_iterative_tool_execution_results(orchestrator: Orchestrator):
    """Test that tool execution results are properly captured."""
    output = orchestrator.process_user_input_iterative("read and summarize README.md")

    assert output.success, f"Task failed: {output.error}"

    memory_content = orchestrator.get_memory_content("conversation", agent_id=output.agent_id)
    tool_turns = [t for t in memory_content if t.get("data", {}).get("role") == "tool"]

    for tool_turn in tool_turns:
        content = tool_turn.get("data", {}).get("content", "")
        assert len(content) > 0, "Tool result content is empty"

        metadata = tool_turn.get("metadata", {})
        assert "tool_name" in metadata, f"Tool name not in metadata. Available keys: {metadata.keys()}"
        assert "success" in metadata, f"Success flag not in metadata. Available keys: {metadata.keys()}"
