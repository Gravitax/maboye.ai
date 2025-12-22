# Core System

## Synthesis

The `core` module establishes the foundational architecture for the agent system, orchestrating the interaction between various components to enable autonomous agent behavior. It encapsulates core domain models, manages data persistence through abstract and in-memory repositories, and implements essential services for memory management, context building, and task execution. The `Orchestrator` acts as the central coordinator, responsible for initializing and connecting all other core components—including the LLM wrapper, Tool Scheduler, and specialized agent factories—thus providing a unified interface for managing complex agent workflows and maintaining conversational state.

## Component Description

*   **`orchestrator.py`**: The central coordinator responsible for setting up, initializing, and managing the lifecycle of all other core modules (LLM, Memory, Tools, Agents). It directs the overall agent workflow, from processing user input to task delegation and result aggregation.
*   **`tool_scheduler.py`**: Manages the execution of tools. It receives tool call requests, validates arguments against defined tool metadata, handles type coercion for LLM outputs, executes the tools via the `ToolRegistry`, and captures results or errors.
*   **`logger.py`**: Provides a standardized logging utility for the entire application, enabling structured and categorized output for debugging and monitoring.
*   **`domain/`**: This subdirectory contains the fundamental business entities and value objects, such as `AgentIdentity` (defining an agent's unique attributes), `AgentCapabilities`, and `ConversationContext`, which model the system's core concepts.
*   **`repositories/`**: Houses abstract interfaces (e.g., `AgentRepository`, `MemoryRepository`) and their in-memory implementations (e.g., `InMemoryAgentRepository`) for data persistence. They define the contract for storing and retrieving domain objects.
*   **`services/`**: Contains various service classes that encapsulate business logic and coordinate interactions between domain objects and repositories. Examples include `MemoryManager` (handling caching and memory isolation), `ContextManager` (building LLM prompts), `AgentFactory` (creating agent instances), and `TasksManager` (managing multi-step tasks).
