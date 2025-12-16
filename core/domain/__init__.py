"""
Domain Layer

Value Objects and Entities for the agent system domain model.

Value Objects (Immutable):
    - AgentIdentity: Unique identity of an agent
    - AgentCapabilities: What an agent can do
    - ConversationContext: Snapshot of conversation state
    - ExecutionPlan: Complete execution plan from LLM

Entities (Mutable):
    - RegisteredAgent: Agent registered in the system with lifecycle

Note: To avoid circular imports, import these explicitly when needed:
    from core.domain.agent_identity import AgentIdentity
    from core.domain.agent_capabilities import AgentCapabilities
    from core.domain.conversation_context import ConversationContext
    from core.domain.registered_agent import RegisteredAgent
    from core.domain.execution_plan import ExecutionPlan, ExecutionStep, ActionStep
"""

# Value Objects
from core.domain.agent_identity import AgentIdentity
from core.domain.agent_capabilities import AgentCapabilities
from core.domain.conversation_context import ConversationContext
from core.domain.execution_plan import ExecutionPlan, ExecutionStep, ActionStep

# Entities
from core.domain.registered_agent import RegisteredAgent

__all__ = [
    # Value Objects
    'AgentIdentity',
    'AgentCapabilities',
    'ConversationContext',
    'ExecutionPlan',
    'ExecutionStep',
    'ActionStep',
    # Entities
    'RegisteredAgent',
]
