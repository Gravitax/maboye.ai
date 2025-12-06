# Agent System

Base classes for building LLM-powered agents with clean architecture and best practices.

---

## Overview

The agent system provides a foundation for creating AI agents that interact with LLM backends.

## Architecture

```
Input → Agent → LLM → Response → Output
         ↓              ↑
      Context       Processing
```

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

### Custom Agent

```python
from agents import Agent, AgentInput, AgentOutput

class CustomAgent(Agent):
    """Custom agent with specialized behavior"""

    def __init__(self, llm, config=None):
        if config is None:
            config = AgentConfig(
                name="CustomAgent",
                system_prompt="Your custom prompt here"
            )
        super().__init__(llm, config)

    def custom_method(self, data):
        """Implement custom functionality"""
        input_data = AgentInput(
            prompt=f"Process: {data}",
            context={"source": "custom_method"}
        )
        return self.run(input_data)
```

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

## Performance Considerations

### Token Efficiency
- Limit history size with `max_history`
- Control input length with `max_input_length`
- Use appropriate `max_tokens` in LLM config

### Connection Management
- Reuse LLM instances when possible
- Use context manager for automatic cleanup
- Reset sessions for long-running processes

### Memory Management
- Clear history periodically
- Reset agent state between tasks
- Monitor execution statistics
