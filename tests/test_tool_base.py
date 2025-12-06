"""
Test suite for tool base class and registry

Run: python tests/test_tool_base.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.tool_base import (
    Tool, ToolMetadata, ToolParameter, ToolRegistry,
    ToolError, ToolExecutionError, ToolValidationError,
    get_registry, register_tool
)


# Example tool implementations for testing
class EchoTool(Tool):
    """Simple echo tool for testing"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="echo",
            description="Echo input text",
            parameters=[
                ToolParameter(
                    name="text",
                    type=str,
                    description="Text to echo",
                    required=True
                )
            ],
            category="test"
        )

    def execute(self, text: str) -> str:
        return text


class AddTool(Tool):
    """Addition tool for testing"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="add",
            description="Add two numbers",
            parameters=[
                ToolParameter(
                    name="a",
                    type=int,
                    description="First number",
                    required=True
                ),
                ToolParameter(
                    name="b",
                    type=int,
                    description="Second number",
                    required=True
                )
            ],
            category="math"
        )

    def execute(self, a: int, b: int) -> int:
        return a + b


class GreetTool(Tool):
    """Greeting tool with optional parameter"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="greet",
            description="Greet someone",
            parameters=[
                ToolParameter(
                    name="name",
                    type=str,
                    description="Name to greet",
                    required=False,
                    default="World"
                )
            ],
            category="test"
        )

    def execute(self, name: str = "World") -> str:
        return f"Hello, {name}!"


class DangerousTool(Tool):
    """Tool marked as dangerous"""

    def _define_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="dangerous",
            description="Dangerous operation",
            parameters=[],
            category="system",
            dangerous=True
        )

    def execute(self) -> str:
        return "Danger!"


def test_tool_creation():
    """Test tool creation and metadata"""
    print("Testing tool creation...")

    tool = EchoTool()
    assert tool.name == "echo", "Tool should have correct name"
    assert tool.description == "Echo input text", "Tool should have description"
    assert tool.metadata.category == "test", "Tool should have category"

    print("  ✓ Tool creation working")


def test_tool_execution():
    """Test tool execution"""
    print("Testing tool execution...")

    # Echo tool
    echo = EchoTool()
    result = echo.run(text="Hello")
    assert result == "Hello", "Should echo input"

    # Add tool
    add = AddTool()
    result = add.run(a=5, b=3)
    assert result == 8, "Should add numbers"

    print("  ✓ Tool execution working")


def test_parameter_validation():
    """Test parameter validation"""
    print("Testing parameter validation...")

    tool = EchoTool()

    # Missing required parameter
    try:
        tool.run()
        assert False, "Should raise ToolValidationError"
    except ToolValidationError:
        pass

    # Invalid parameter type (should auto-convert)
    result = tool.run(text=123)
    assert result == "123", "Should convert int to string"

    print("  ✓ Parameter validation working")


def test_optional_parameters():
    """Test optional parameters with defaults"""
    print("Testing optional parameters...")

    tool = GreetTool()

    # Without optional parameter
    result = tool.run()
    assert result == "Hello, World!", "Should use default"

    # With optional parameter
    result = tool.run(name="Alice")
    assert result == "Hello, Alice!", "Should use provided value"

    print("  ✓ Optional parameters working")


def test_registry_operations():
    """Test tool registry"""
    print("Testing registry operations...")

    registry = ToolRegistry()

    # Register tools
    echo = EchoTool()
    add = AddTool()
    greet = GreetTool()

    registry.register(echo)
    registry.register(add)
    registry.register(greet)

    # Check registration
    assert registry.has_tool("echo"), "Should have echo tool"
    assert registry.has_tool("add"), "Should have add tool"
    assert not registry.has_tool("nonexistent"), "Should not have nonexistent tool"

    # Get tool
    retrieved = registry.get_tool("echo")
    assert retrieved is not None, "Should retrieve tool"
    assert retrieved.name == "echo", "Should retrieve correct tool"

    # List tools
    tools = registry.list_tools()
    assert len(tools) == 3, "Should list all tools"
    assert "echo" in tools, "Should include echo"

    # List by category
    test_tools = registry.list_tools(category="test")
    assert len(test_tools) == 2, "Should have 2 test tools"

    math_tools = registry.list_tools(category="math")
    assert len(math_tools) == 1, "Should have 1 math tool"

    print("  ✓ Registry operations working")


def test_registry_execution():
    """Test executing tools through registry"""
    print("Testing registry execution...")

    registry = ToolRegistry()
    registry.register(AddTool())

    # Execute through registry
    result = registry.execute("add", a=10, b=5)
    assert result == 15, "Should execute through registry"

    # Non-existent tool
    try:
        registry.execute("nonexistent")
        assert False, "Should raise ToolError"
    except ToolError:
        pass

    print("  ✓ Registry execution working")


def test_tool_info():
    """Test tool information retrieval"""
    print("Testing tool info...")

    registry = ToolRegistry()
    registry.register(EchoTool())

    info = registry.get_tool_info("echo")
    assert info is not None, "Should get tool info"
    assert info["name"] == "echo", "Should have name"
    assert info["category"] == "test", "Should have category"
    assert len(info["parameters"]) == 1, "Should have parameters"
    assert info["parameters"][0]["name"] == "text", "Should have parameter name"

    print("  ✓ Tool info working")


def test_dangerous_tools():
    """Test dangerous tool filtering"""
    print("Testing dangerous tools...")

    registry = ToolRegistry()
    registry.register(EchoTool())
    registry.register(DangerousTool())

    # Include dangerous
    all_tools = registry.list_tools(include_dangerous=True)
    assert len(all_tools) == 2, "Should include dangerous tools"

    # Exclude dangerous
    safe_tools = registry.list_tools(include_dangerous=False)
    assert len(safe_tools) == 1, "Should exclude dangerous tools"
    assert "dangerous" not in safe_tools, "Should not include dangerous tool"

    print("  ✓ Dangerous tool filtering working")


def test_unregister():
    """Test tool unregistration"""
    print("Testing tool unregistration...")

    registry = ToolRegistry()
    registry.register(EchoTool())

    assert registry.has_tool("echo"), "Should have tool"

    registry.unregister("echo")
    assert not registry.has_tool("echo"), "Should not have tool after unregister"

    print("  ✓ Tool unregistration working")


def test_global_registry():
    """Test global registry functions"""
    print("Testing global registry...")

    # Clear global registry first
    global_reg = get_registry()
    for tool_name in global_reg.list_tools():
        global_reg.unregister(tool_name)

    # Register with global function
    register_tool(EchoTool())

    # Access through global registry
    reg = get_registry()
    assert reg.has_tool("echo"), "Should be in global registry"

    print("  ✓ Global registry working")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Testing Tool Base and Registry")
    print("=" * 60)

    test_tool_creation()
    test_tool_execution()
    test_parameter_validation()
    test_optional_parameters()
    test_registry_operations()
    test_registry_execution()
    test_tool_info()
    test_dangerous_tools()
    test_unregister()
    test_global_registry()

    print("=" * 60)
    print("All tool base and registry tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
