# Agent System

Base classes for building LLM-powered agents with clean architecture and best practices.

---

## Overview

The agent system provides a foundation for creating AI agents that interact with LLM backends. It follows the single-responsibility principle with simple, focused functions and professional code structure.

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

**Features:**
- Input/output validation
- Execution history tracking
- Configurable logging
- Error handling
- State management

### LLM (Wrapper Class)

Abstraction layer for LLM API interactions.

**Methods:**
- `chat_completion()` - Chat-based completions
- `completion()` - Text completions
- `list_models()` - Available models
- `get_last_response()` - Last API response
- `reset_session()` - Reset connection

**Features:**
- Automatic retries with backoff
- Connection pooling
- Request/response logging
- Error handling
- Session management

### Configuration

**AgentConfig:**
- `name` - Agent identifier
- `max_history` - History retention limit
- `enable_logging` - Logging toggle
- `validate_inputs` - Input validation
- `system_prompt` - Default system prompt
- `max_input_length` - Input size limit

**LLMConfig:**
- `base_url` - API endpoint
- `model` - Model identifier
- `temperature` - Sampling temperature
- `max_tokens` - Token limit
- `timeout` - Request timeout
- `max_retries` - Retry attempts

---

## Usage

### Basic Usage

```python
from agents import Agent, LLM, LLMConfig, AgentConfig

# Configure LLM
llm_config = LLMConfig(
    base_url="http://127.0.0.1:8000",
    model="gpt-4",
    temperature=0.7
)

# Create LLM instance
llm = LLM(llm_config)

# Configure agent
agent_config = AgentConfig(
    name="MyAgent",
    system_prompt="You are a helpful assistant."
)

# Create agent
agent = Agent(llm, agent_config)

# Execute workflow
output = agent.run("What is 2+2?")
print(output.response)
```

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

### Direct LLM Usage

```python
from agents import LLM, LLMConfig, Message

llm_config = LLMConfig(base_url="http://127.0.0.1:8000")
llm = LLM(llm_config)

messages = [
    Message(role="system", content="You are helpful."),
    Message(role="user", content="Hello!")
]

response = llm.chat_completion(messages)
print(response.choices[0].message.content)
```

---

## File Structure

```
agents/
├── __init__.py          # Package exports
├── agent.py             # Base Agent class
├── llm.py               # LLM wrapper
├── config.py            # Configuration classes
├── types.py             # Type definitions
├── example_agent.py     # Example implementations
└── README.md            # This file
```

---

## Best Practices

### Code Organization

- **Single Responsibility:** Each method does one thing
- **Simple Conditionals:** Clear if/else logic
- **Simple Loops:** Single-purpose iterations
- **Professional Comments:** Clear, concise English
- **No Emojis:** Professional codebase

### Error Handling

```python
try:
    output = agent.run(input_data)
except AgentInputError as e:
    # Handle input validation error
    pass
except AgentError as e:
    # Handle general agent error
    pass
except LLMError as e:
    # Handle LLM communication error
    pass
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

## Extension Points

### Custom Input Processing

Override `_validate_input()` for custom validation:

```python
def _validate_input(self, input_data):
    super()._validate_input(input_data)
    # Add custom validation
    if "required_field" not in input_data.context:
        raise AgentInputError("Missing required field")
```

### Custom Message Building

Override `_build_messages()` for custom prompts:

```python
def _build_messages(self):
    messages = super()._build_messages()
    # Add custom messages
    messages.append(Message(
        role="system",
        content="Additional instructions"
    ))
    return messages
```

### Custom Output Processing

Override `_validate_output()` for custom validation:

```python
def _validate_output(self, output):
    super()._validate_output(output)
    # Add custom validation
    if len(output.response) < 10:
        raise AgentOutputError("Response too short")
```

---

## Dependencies

```
pydantic>=2.0.0
requests>=2.31.0
urllib3>=2.0.0
```

Install with:
```bash
pip install pydantic requests urllib3
```

---

## Examples

See `example_agent.py` for complete examples:
- `CodeReviewAgent` - Code review specialist
- `SummaryAgent` - Text summarization specialist

Run examples:
```bash
python agents/example_agent.py
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

---

## Future Enhancements

Potential additions for production use:
- Async support for concurrent requests
- Response caching
- Token usage tracking and limits
- Custom retry strategies
- Streaming response support
- Multi-agent orchestration
- Persistent state storage
