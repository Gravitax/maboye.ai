# Repositories Module

This module defines the data access layer of the application.
It provides interfaces for storing and retrieving domain entities, abstracting the underlying data storage mechanisms.

## File Structure

- `agent_repository.py`: Defines the interface for storing, retrieving, and managing `Agent` entities.

- `in_memory_agent_repository.py`: Provides an in-memory implementation of the `AgentRepository` interface, suitable for testing or temporary storage.

- `in_memory_memory_repository.py`: Provides an in-memory implementation for storing and retrieving agent memory data.

- `memory_repository.py`: Defines the interface for managing persistent memory data associated with agents or conversations.
