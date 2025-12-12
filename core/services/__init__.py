"""
Service Layer

Business logic services for agent system.

Services:
    - AgentMemoryCoordinator: Coordinates memory access across agents
    - AgentPromptConstructor: Builds agent-specific prompts
    - AgentExecutionService: Executes agents with metrics and traceability

Types:
    - ExecutionOptions: Options for agent execution
    - AgentExecutionResult: Result of agent execution
    - CacheStrategy, LRUCache: Caching strategies

Exceptions:
    - AgentNotFoundError: Agent not found in repository
    - AgentInactiveError: Agent is inactive
    - AgentExecutionError: Agent execution failed

Note: To avoid circular imports, import these explicitly when needed:
    from core.services.agent_memory_coordinator import AgentMemoryCoordinator
    from core.services.agent_prompt_constructor import AgentPromptConstructor
    from core.services.agent_execution_service import AgentExecutionService
"""

# Cache strategies
from core.services.cache_strategy import CacheStrategy, LRUCache

# Services
from core.services.agent_memory_coordinator import AgentMemoryCoordinator
from core.services.agent_prompt_constructor import AgentPromptConstructor
from core.services.agent_execution_service import AgentExecutionService

# Types
from core.services.service_types import (
    ExecutionOptions,
    AgentExecutionResult,
    AgentNotFoundError,
    AgentInactiveError,
    AgentExecutionError
)

__all__ = [
    # Cache
    'CacheStrategy',
    'LRUCache',
    # Services
    'AgentMemoryCoordinator',
    'AgentPromptConstructor',
    'AgentExecutionService',
    # Types
    'ExecutionOptions',
    'AgentExecutionResult',
    # Exceptions
    'AgentNotFoundError',
    'AgentInactiveError',
    'AgentExecutionError',
]
