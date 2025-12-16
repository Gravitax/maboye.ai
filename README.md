# maboye.AI

This project is a Python-based framework for creating and running autonomous agents through a command-line interface (CLI).
It features a modular architecture that separates core logic, agent definitions, tools, and the user interface.

## Project Architecture

The project is organized into several key modules, each with a distinct responsibility:

- `main.py`: The main entry point for the application. It initializes the system and starts the command-line interface.

- `start.sh`: A shell script to simplify the process of launching the application.

- `core/`: The central module of the application. It handles orchestration, defines the core domain models, manages data persistence through repositories, and contains the main business logic in its services.

- `agents/`: Contains the logic for the agents themselves. The `profiles/` subdirectory defines the specific capabilities and identities of different types of agents (e.g., code agent, bash agent) in a modular way.

- `tools/`: Provides the collection of tools that agents can use to interact with the environment. This includes functionalities for file operations, shell command execution, and more.

- `cli/`: Implements the command-line interface. It is responsible for parsing user input, managing commands, and displaying output to the terminal.

- `requirements.txt`: Lists all the Python dependencies required to run the project.

- `.env.example`: An example file showing the required environment variables for configuration.

## Usage

To run the application, use the `start.sh` script:

```bash
./start.sh
```

By default, the application starts without the backend mock server. To start the application and the backend server simultaneously, use the `--backend` flag:

```bash
./start.sh --backend
```

> supervised_simple
> supervised_analyze
> supervised_error
