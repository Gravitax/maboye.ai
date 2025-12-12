# Services Module

This module contains the application's core business logic. Services orchestrate operations, coordinate interactions between domain entities and repositories, and encapsulate complex use cases.

## File Structure

- `agent_execution_service.py`: Manages the lifecycle and execution of agent tasks, including delegating to tools and processing results.

- `agent_factory.py`: Responsible for creating and initializing agent instances based on their profiles and configurations.

- `agent_memory_coordinator.py`: Coordinates the storage, retrieval, and management of memory for agents.

- `agent_prompt_constructor.py`: Constructs and formats prompts for Large Language Models, incorporating context, instructions, and available tools.

- `cache_strategy.py`: Defines strategies and implementations for caching data to improve performance.

- `service_types.py`: Contains common type definitions and enums used across the service layer.