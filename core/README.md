# Core Module

This module represents the central part of the application, encompassing the foundational components for orchestration, logging, and managing interactions between different parts of the system, including agents, tools, and LLMs.

## File Structure

- `logger.py`: Configures and provides a standardized logging mechanism for the entire application, ensuring consistent output for debugging and monitoring.

- `orchestrator.py`: Contains the main application orchestrator, responsible for managing the overall flow, coordinating tasks, and directing interactions between agents, tools, and the LLM.

- `tool_scheduler.py`: Manages the scheduling and execution of tools, ensuring that tool calls are processed efficiently and in the correct order.

- `domain/`: A subdirectory defining the core business entities, data models, and foundational concepts of the application.

- `llm_wrapper/`: A subdirectory containing components for interacting with Large Language Models, abstracting the specifics of LLM providers.

- `repositories/`: A subdirectory providing interfaces and implementations for data persistence and retrieval for various application entities.

- `services/`: A subdirectory housing the application's business logic, coordinating domain entities and repositories to fulfill specific tasks.
