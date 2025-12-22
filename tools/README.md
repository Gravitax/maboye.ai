# Tool System

## Synthesis

The `tools` module provides a standardized, extensible interface for agents to interact with the external environment. It relies on the `Tool` abstract base class, which enforces a strict contract for parameter validation, metadata definition, and execution logic. A central `ToolRegistry` manages the discovery and instantiation of tools, allowing agents to dynamically access capabilities like file manipulation, high-performance code search (ripgrep), shell command execution, and version control operations. Security is enforced via metadata flags (e.g., `dangerous=True`) and input validation layers.

## Component Description

*   **`tool_base.py`**: Defines the core architecture, including the `Tool` abstract base class, `ToolMetadata` data structure, and the `ToolRegistry` for managing tool lifecycle and lookup.
*   **`implementations.py`**: Adapts raw functional logic into concrete `Tool` subclasses (e.g., `ReadFileTool`, `GitStatusTool`), mapping agent inputs to backend operations.
*   **`tool_ids.py`**: Contains constants and enumerations for stable tool identification across the system.
*   **`file_ops.py` / `search.py` / `shell.py` / `git_ops.py`**: Standalone modules implementing the actual low-level operations. These are decoupled from the agent interface to allow direct usage where appropriate.
*   **`implementations/`**: A subdirectory containing specific tool categories and their logic.

## Control Tools

Control tools are special tools used to manage the agent's flow (e.g., signalling success, failure, or global completion). They are typically available to all agents by default.

### Adding a New Control Tool

To add a new control tool, follow these steps:

1.  **Define the Tool Class**:
    Create the tool class in `tools/implementations/control_tools.py`. It should inherit from `Tool` and implement `_define_metadata` and `execute`.

    ```python
    # tools/implementations/control_tools.py
    class MyControlTool(Tool):
        def _define_metadata(self) -> ToolMetadata:
            return ToolMetadata(
                name=ToolId.MY_CONTROL_TOOL.value,
                # ...
            )
        # ...
    ```

2.  **Add Tool ID**:
    Add a new constant to the `ToolId` enum in `tools/tool_ids.py`.

    ```python
    # tools/tool_ids.py
    class ToolId(str, Enum):
        # ...
        MY_CONTROL_TOOL = "my_control_tool"
    ```

3.  **Register the Tool**:
    Update `tools/implementations/__init__.py` to:
    *   Import the new class.
    *   Add an instance to the `control_tools` list in the `register_all_tools` function.
    *   Add the class name to `__all__`.

4.  **Inject by Default (Optional but Recommended for Control Tools)**:
    If the tool should be available to all agents automatically (like `task_success` or `task_error`), you must update `core/services/context_manager.py`.
    
    In the `get_available_tools_prompt` method:
    *   Add logic to append the tool ID to `tools_to_display` if it's not already present.
    *   Optionally, add a specific "NOTE" to guide the LLM on when to use this tool immediately.

    ```python
    # core/services/context_manager.py
    
    def get_available_tools_prompt(self, agent) -> str:
        # ...
        # Ensure my_control_tool is always displayed
        if ToolId.MY_CONTROL_TOOL.value not in tools_to_display:
            tools_to_display.append(ToolId.MY_CONTROL_TOOL.value)
        
        # ... inside the loop ...
        if tool_name == ToolId.MY_CONTROL_TOOL.value:
            lines.append("NOTE: Use this tool ...")
    ```