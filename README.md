# Maboye AI - Autonomous Agent System

## Overview

**Maboye AI** is a modular, CLI-driven framework designed to create and orchestrate autonomous AI agents. Built with a robust iterative reasoning engine, it enables agents to break down complex tasks, execute tools (file I/O, Git, shell), and maintain persistent context—all within a unified terminal interface.

The system is architected around a central **Orchestrator** that manages specialized agents (e.g., `CodeAgent`, `GitAgent`), delegating tasks based on capabilities and utilizing a specialized **TasksAgent** for high-level planning.

## Key Features

*   **Iterative Agent Workflow**: Agents follow a strict "Plan → Execute → Observe" cycle, allowing for error correction and dynamic replanning.
*   **Specialized Agent Roles**: Configurable agent profiles (defined in JSON) allow for distinct identities and toolsets (e.g., coding, system administration).
*   **Extensive Tooling**: Built-in support for safe file operations, Git version control, high-performance code search (via `ripgrep`), and controlled shell execution.
*   **Interactive CLI**: A rich terminal interface with command history, tab completion, and colored output for clear user interaction.
*   **Robust Memory Management**: Persistent conversation history and context isolation per agent, optimized with LRU caching.
*   **LLM Abstraction**: A cleaner `llm_wrapper` layer that decouples the system from specific model providers.

## Architecture Modules

The project is organized into five core modules, each with its own specific responsibility:

*   **`core/`**: The central nervous system. Contains the `Orchestrator`, domain entities (`AgentIdentity`, `RegisteredAgent`), and service layers for memory and task management.
*   **`agents/`**: The cognitive engine. Implements the `Agent` class and the `TaskExecution` loop that drives the iterative reasoning process.
*   **`tools/`**: The capabilities layer. Provides a standardized `Tool` interface and a registry for all external operations (File Ops, Git, Search, etc.).
*   **`cli/`**: The user interface. Manages the terminal event loop, command parsing (`/help`, `/tools`), and system command integration.
*   **`llm_wrapper/`**: The communication layer. Handles API requests, authentication, and response parsing for Large Language Models.

*(See the `README.md` file within each directory for detailed technical documentation.)*

## Getting Started

### Prerequisites

*   **Python 3.8+**
*   **Git**
*   **(Optional)** `ripgrep` for high-performance code search.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd maboye.ai
    ```

2.  **Setup Environment:**
    Copy the example environment file and configure your keys.
    ```bash
    cp .env.example .env
    # Edit .env with your API keys and configuration
    ```

3.  **Install Dependencies:**
    You can use the provided start script to handle virtual environment creation and installation automatically, or do it manually:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

**Running the CLI:**

The easiest way to start the application is via the `start.sh` script, which handles the virtual environment and optional backend services.

```bash
./start.sh
```

**Optional: Start with Mock Backend**
To run with a local backend service (e.g., for testing or offline mode):
```bash
./start.sh --backend
```

**Manual Execution:**
```bash
source venv/bin/activate
python main.py
```

### CLI Commands

Once inside the interactive terminal, you can use natural language to instruct the agents or use specific slash commands:

*   `/help`: Show available commands.
*   `/tools`: List all available tools and their descriptions.
*   `/clear`: Clear the terminal screen.
*   `/exit` or `/quit`: Close the application.
*   Standard shell commands (`ls`, `cd`, `pwd`) are also supported directly.

## Contributing

Please adhere to the project's coding standards:
*   Use `snake_case` for functions and variables.
*   Keep functions short and single-purpose.
*   Add comments only for "why", not "what".
