# Agent System

Base classes for building LLM-powered agents with clean architecture and best practices.

---

## Overview

The agent system provides a foundation for creating AI agents that interact with LLM backends.

## Components

### Agent (Base Class)

Core agent implementation with workflow management.

**Key Methods:**
- `set_input()` - Set agent input
- `get_input()` - Retrieve current input
- `modify_input()` - Modify existing input
- `query_llm()` - Send request to LLM
- `get_last_llm_response()` - Get last LLM response
- `set_output()` - Set agent output
- `get_output()` - Retrieve current output
- `run()` - Execute complete workflow

### Logging

```python
# Automatic logging when enabled
agent_config = AgentConfig(
    enable_logging=True,
    log_inputs=True,
    log_outputs=True
)

# View execution stats
stats = agent.get_stats()
print(stats)
```

### State Management

```python
# Access execution history
history = agent.get_history()

# Reset agent state
agent.reset()

# Clear history only
agent.clear_history()
```

---

## Testing

Start the mock backend first:
```bash
cd backend
python main.py
```

Then run agent code:
```bash
python agents/example_agent.py
```

---

## Error Reference

**AgentError:** Base agent exception
**AgentInputError:** Input validation failed
**AgentOutputError:** Output validation failed
**LLMError:** Base LLM exception
**LLMConnectionError:** Connection failed
**LLMAPIError:** API returned error

---
