# CLI System

## Synthesis

The `cli` module implements the application's interactive command-line interface, serving as the primary bridge between the user and the agent orchestration system. It features a robust event loop managed by the `Terminal` class, which handles user input, signal processing (interrupts/EOF), and output formatting. The system distinguishes between internal application commands (prefixed with `/`) and system shell commands. It leverages `readline` for enhanced usability features like command history, navigation, and context-aware tab completion.

## Component Description

*   **`terminal.py`**: The core driver of the CLI. It manages the run loop, processes raw input, displays the prompt, and handles terminal signal events.
*   **`command_manager.py`**: Responsible for parsing, registering, and routing internal commands (e.g., `/help`, `/tools`) to their respective handlers.
*   **`system_command_manager.py`**: Detects and executes standard system shell commands (e.g., `ls`, `cd`) directly from the CLI prompt.
*   **`completer.py`**: Implements custom tab-completion logic, offering suggestions for both internal commands and file system paths.
*   **`cli_utils.py`**: Provides utility functions for terminal output, including ANSI color codes and text formatting helpers.
*   **`commands/`**: A directory containing the implementation logic for specific CLI commands.
