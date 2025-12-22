# Tool System

## Synthesis

The `tools` module provides a standardized, extensible interface for agents to interact with the external environment. It relies on the `Tool` abstract base class, which enforces a strict contract for parameter validation, metadata definition, and execution logic. A central `ToolRegistry` manages the discovery and instantiation of tools, allowing agents to dynamically access capabilities like file manipulation, high-performance code search (ripgrep), shell command execution, and version control operations. Security is enforced via metadata flags (e.g., `dangerous=True`) and input validation layers.

## Component Description

*   **`tool_base.py`**: Defines the core architecture, including the `Tool` abstract base class, `ToolMetadata` data structure, and the `ToolRegistry` for managing tool lifecycle and lookup.
*   **`implementations.py`**: Adapts raw functional logic into concrete `Tool` subclasses (e.g., `ReadFileTool`, `GitStatusTool`), mapping agent inputs to backend operations.
*   **`tool_ids.py`**: Contains constants and enumerations for stable tool identification across the system.
*   **`file_ops.py` / `search.py` / `shell.py` / `git_ops.py`**: Standalone modules implementing the actual low-level operations. These are decoupled from the agent interface to allow direct usage where appropriate.
*   **`implementations/`**: A subdirectory containing specific tool categories and their logic.
