# Agent System

## Synthesis

The `agents` module implements a robust, iterative agent architecture designed for autonomous task execution. At its core, the system utilizes a feedback loop where the `Agent` orchestrates interactions between the Large Language Model (LLM), a tool execution engine, and a persistent memory store.

The workflow is centralized around the `Agent` class, which breaks down high-level user tasks into discrete steps. For each step, the `TaskExecution` coordinator prompts the LLM, strictly parses the response into structured commands, performs security validation, and executes the appropriate tool. This cycle repeats—analyzing results and adjusting plans—until the objective is met or constraints are reached.

## Component Description

*   **`agent.py`**: Contains the main `Agent` class. It manages the lifecycle of a task, handling the iterative execution loop, context management, and decision-making process based on tool outputs.
*   **`task_execution.py`**: Implements the `TaskExecution` class. This component is responsible for a single atomic execution step: generating the prompt, parsing the JSON tool command from the LLM response (with retry logic), checking for dangerous actions, and invoking the `ToolScheduler`.
*   **`types.py`**: Defines the data contracts and type definitions for the system. It uses Pydantic models and TypedDicts (e.g., `AgentInput`, `AgentOutput`, `ToolCall`) to ensure type safety and structured communication between components.
*   **`profiles/`**: A subdirectory containing JSON configuration files that define distinct agent identities (e.g., `default_agent.json`, `exec_agent.json`), allowing for customizable agent behaviors and capability sets.
