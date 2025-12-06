"""
Test suite for Agent tool usage

Run: python tests/test_agent_tools.py

Tests that the Agent can successfully use tools from the registry.
"""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents.agent_code import AgentCode
from agents.config import AgentConfig
from LLM import LLM
from LLM.config import LLMConfig
from tools.tool_base import ToolRegistry, get_registry
from tools.implementations import register_all_tools


# Register tools once at module level
register_all_tools()


def test_agent_initialization_with_tools():
    """Test code agent initialization with tool registry"""
    print("Testing code agent initialization with tools...")

    # Create code agent
    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # Check tools are available
    tools = agent.list_available_tools(include_dangerous=True)
    assert len(tools) > 0, "Should have tools available"
    assert "read_file" in tools, "Should have read_file tool"
    assert "write_file" in tools, "Should have write_file tool"

    print("  ✓ Agent initialization with tools working")


def test_agent_list_tools():
    """Test agent tool listing"""
    print("Testing agent tool listing...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # List all tools
    all_tools = agent.list_available_tools()
    assert len(all_tools) > 0, "Should have tools"

    # List by category
    file_tools = agent.list_available_tools(category="file_operations")
    assert "read_file" in file_tools, "Should have file operation tools"

    search_tools = agent.list_available_tools(category="search")
    assert "glob_files" in search_tools, "Should have search tools"

    # Exclude dangerous tools
    safe_tools = agent.list_available_tools(include_dangerous=False)
    assert "write_file" not in safe_tools, "Should exclude dangerous tools"
    assert "read_file" in safe_tools, "Should include safe tools"

    print("  ✓ Agent tool listing working")


def test_agent_get_tool_info():
    """Test getting tool information"""
    print("Testing agent get tool info...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # Get tool info
    info = agent.get_tool_info("read_file")
    assert info is not None, "Should get tool info"
    assert info["name"] == "read_file", "Should have correct name"
    assert info["category"] == "file_operations", "Should have category"
    assert len(info["parameters"]) > 0, "Should have parameters"

    print("  ✓ Agent get tool info working")


def test_agent_use_file_tools():
    """Test agent using file operation tools"""
    print("Testing agent file operation tools...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        content = "Test content from agent"

        # Write file using tool
        result = agent.use_tool(
            "write_file",
            file_path=str(test_file),
            content=content
        )
        assert result is True, "Should write file"
        assert test_file.exists(), "File should exist"

        # Read file using tool
        read_content = agent.use_tool(
            "read_file",
            file_path=str(test_file)
        )
        assert read_content == content, "Should read correct content"

        # Edit file using tool
        agent.use_tool(
            "edit_file",
            file_path=str(test_file),
            old_string="Test",
            new_string="Modified"
        )

        # Verify edit
        edited_content = agent.use_tool(
            "read_file",
            file_path=str(test_file)
        )
        assert "Modified" in edited_content, "Should have edited content"

    print("  ✓ Agent file operation tools working")


def test_agent_use_search_tools():
    """Test agent using search tools"""
    print("Testing agent search tools...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        for i in range(3):
            file_path = Path(tmpdir) / f"file{i}.py"
            agent.use_tool(
                "write_file",
                file_path=str(file_path),
                content=f"def test{i}():\n    pass\n"
            )

        # Glob files
        py_files = agent.use_tool(
            "glob_files",
            pattern="*.py",
            path=tmpdir
        )
        assert len(py_files) == 3, "Should find Python files"

        # Grep content
        grep_results = agent.use_tool(
            "grep_content",
            pattern="def",
            path=tmpdir,
            file_pattern="*.py"
        )
        assert grep_results["matches_found"] > 0, "Should find matches"

    print("  ✓ Agent search tools working")


def test_agent_use_shell_tool():
    """Test agent using shell tool"""
    print("Testing agent shell tool...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # Execute simple command
    result = agent.use_tool(
        "execute_command",
        command="echo 'Hello from agent'"
    )

    assert result.success, "Command should succeed"
    assert "Hello from agent" in result.stdout, "Should have output"

    print("  ✓ Agent shell tool working")


def test_agent_tool_execution_tracking():
    """Test tracking of tool executions"""
    print("Testing tool execution tracking...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # Execute some tools
    agent.use_tool("execute_command", command="echo 'test'")

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        agent.use_tool(
            "write_file",
            file_path=str(test_file),
            content="test"
        )

    # Check execution tracking
    executions = agent.get_tool_executions()
    assert len(executions) == 2, "Should track executions"
    assert executions[0]["tool"] == "execute_command", "Should track first tool"
    assert executions[1]["tool"] == "write_file", "Should track second tool"
    assert all(e["success"] for e in executions), "All should succeed"

    print("  ✓ Tool execution tracking working")


def test_agent_stats_with_tools():
    """Test agent statistics include tool info"""
    print("Testing agent stats with tools...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # Execute some tools
    agent.use_tool("execute_command", command="echo 'test'")

    # Get stats
    stats = agent.get_stats()
    assert "tool_executions" in stats, "Should have tool execution count"
    assert stats["tool_executions"] == 1, "Should track tool executions"
    assert "available_tools" in stats, "Should have available tools count"
    assert stats["available_tools"] > 0, "Should have tools available"

    print("  ✓ Agent stats with tools working")


def test_agent_reset_clears_tool_executions():
    """Test reset clears tool executions"""
    print("Testing agent reset clears tool executions...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # Execute tool
    agent.use_tool("execute_command", command="echo 'test'")
    assert len(agent.get_tool_executions()) == 1, "Should have execution"

    # Reset
    agent.reset()
    assert len(agent.get_tool_executions()) == 0, "Should clear executions"

    print("  ✓ Agent reset clears tool executions working")


def test_run_existing_tests_via_agent():
    """Test agent can run existing test suites"""
    print("Testing agent running existing tests...")

    llm = LLM(LLMConfig())
    agent = AgentCode(llm)

    # Run file operations test
    result = agent.use_tool(
        "execute_command",
        command="python3 tests/test_file_ops.py",
        timeout=30
    )
    assert result.success, "File ops tests should pass"
    assert "All file operation tests passed" in result.stdout, "Should complete all tests"

    # Run search operations test
    result = agent.use_tool(
        "execute_command",
        command="python3 tests/test_search.py",
        timeout=30
    )
    assert result.success, "Search tests should pass"
    assert "All search operation tests passed" in result.stdout, "Should complete all tests"

    # Run shell operations test
    result = agent.use_tool(
        "execute_command",
        command="python3 tests/test_shell.py",
        timeout=30
    )
    assert result.success, "Shell tests should pass"
    assert "All shell operation tests passed" in result.stdout, "Should complete all tests"

    print("  ✓ Agent running existing tests working")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing AgentCode Tool Usage")
    print("=" * 60)

    test_agent_initialization_with_tools()
    test_agent_list_tools()
    test_agent_get_tool_info()
    test_agent_use_file_tools()
    test_agent_use_search_tools()
    test_agent_use_shell_tool()
    test_agent_tool_execution_tracking()
    test_agent_stats_with_tools()
    test_agent_reset_clears_tool_executions()
    test_run_existing_tests_via_agent()

    print("=" * 60)
    print("All AgentCode tool usage tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
