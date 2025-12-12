"""
Repository Layer

Abstract interfaces and implementations for data persistence.

Interfaces:
    - AgentRepository: Agent persistence operations
    - MemoryRepository: Conversation memory operations

Implementations:
    - InMemoryAgentRepository: In-memory agent storage
    - InMemoryMemoryRepository: In-memory memory storage

Exceptions:
    - RepositoryError: Base exception for repository errors

Note: To avoid circular imports, import these explicitly when needed:
    from core.repositories.agent_repository import AgentRepository
    from core.repositories.memory_repository import MemoryRepository
    from core.repositories.in_memory_agent_repository import InMemoryAgentRepository
    from core.repositories.in_memory_memory_repository import InMemoryMemoryRepository
"""

# Interfaces
from core.repositories.agent_repository import AgentRepository
from core.repositories.memory_repository import MemoryRepository

# Implementations
from core.repositories.in_memory_agent_repository import (
    InMemoryAgentRepository,
    RepositoryError as AgentRepositoryError
)
from core.repositories.in_memory_memory_repository import (
    InMemoryMemoryRepository,
    RepositoryError as MemoryRepositoryError
)

__all__ = [
    # Interfaces
    'AgentRepository',
    'MemoryRepository',
    # Implementations
    'InMemoryAgentRepository',
    'InMemoryMemoryRepository',
    # Exceptions
    'AgentRepositoryError',
    'MemoryRepositoryError',
]
