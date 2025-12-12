# CLI Module

This module is responsible for handling the command-line interface (CLI) interactions of the application.
It provides utilities for parsing commands, managing their execution, and interacting with the terminal.

## File Structure

- `cli_utils.py`: Contains various utility functions that support CLI operations, such as input parsing, output formatting, and interactive prompts.

- `command_manager.py`: Manages the registration, discovery, and execution flow of all available CLI commands. It acts as the central dispatcher for user commands.

- `terminal.py`: Handles low-level terminal interactions, including displaying output, reading user input, and managing terminal state.

- `commands/`: A subdirectory containing the implementation of individual CLI commands. Each file in this directory defines a specific command's logic.
