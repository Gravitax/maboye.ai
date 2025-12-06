# LLM Wrapper

Abstraction layer for LLM API interactions with error handling, retries, and logging.

---

## Overview

The LLM wrapper provides a clean interface for interacting with OpenAI-compatible APIs. It handles connection management, retries, error handling, and request/response logging.

## Features

- OpenAI-compatible API support
- Automatic retry with exponential backoff
- Connection pooling
- Request/response logging
- Error handling and classification
- Session management
- Context manager support

---

## Usage

### Basic Setup

```python
from LLM import LLM, LLMConfig

config = LLMConfig(
    base_url="http://127.0.0.1:8000",
    model="gpt-4",
    temperature=0.7,
    timeout=30,
    max_retries=3
)

llm = LLM(config)
```

### Chat Completion

```python
from agents.types import Message

messages = [
    Message(role="system", content="You are helpful."),
    Message(role="user", content="Hello!")
]

response = llm.chat_completion(messages)
print(response.choices[0].message.content)
```

### Text Completion

```python
response = llm.completion(
    prompt="Once upon a time",
    max_tokens=100
)
print(response.choices[0].text)
```

### List Models

```python
models = llm.list_models()
for model in models.data:
    print(model.id)
```

### Context Manager

```python
with LLM(config) as llm:
    response = llm.chat_completion(messages)
    print(response.choices[0].message.content)
# Automatically closes session
```

---

## Configuration

### LLMConfig Parameters

**base_url** (str)
- API endpoint base URL
- Default: `http://127.0.0.1:8000`

**api_key** (str, optional)
- API authentication key
- Default: None

**model** (str)
- Model identifier
- Default: `gpt-4`

**temperature** (float)
- Sampling temperature (0.0-2.0)
- Default: 0.7

**max_tokens** (int, optional)
- Maximum tokens to generate
- Default: None (model default)

**timeout** (int)
- Request timeout in seconds
- Default: 30

**max_retries** (int)
- Maximum retry attempts
- Default: 3

**retry_delay** (float)
- Base delay between retries in seconds
- Default: 1.0

---

## Error Handling

### Exception Hierarchy

```
LLMError (base)
├── LLMConnectionError (connection issues)
└── LLMAPIError (API errors)
```

### Example

```python
from LLM import LLM, LLMConnectionError, LLMAPIError

try:
    response = llm.chat_completion(messages)
except LLMConnectionError as e:
    # Handle connection failure
    print(f"Connection failed: {e}")
except LLMAPIError as e:
    # Handle API error
    print(f"API error: {e}")
```

---

## Methods

### chat_completion()

Create chat completion.

```python
response = llm.chat_completion(
    messages=[Message(...)],
    temperature=0.7,
    max_tokens=150
)
```

**Parameters:**
- `messages` (List[Message]) - Conversation messages
- `temperature` (float, optional) - Sampling temperature
- `max_tokens` (int, optional) - Max tokens to generate
- `**kwargs` - Additional API parameters

**Returns:** ChatCompletionResponse

### completion()

Create text completion.

```python
response = llm.completion(
    prompt="Text to complete",
    temperature=0.7,
    max_tokens=150
)
```

**Parameters:**
- `prompt` (str | List[str]) - Text prompt(s)
- `temperature` (float, optional) - Sampling temperature
- `max_tokens` (int, optional) - Max tokens to generate
- `**kwargs` - Additional API parameters

**Returns:** CompletionResponse

### list_models()

List available models.

```python
models = llm.list_models()
```

**Returns:** ModelsResponse

### get_last_response()

Get last API response.

```python
last = llm.get_last_response()
```

**Returns:** ChatCompletionResponse | CompletionResponse | None

### get_request_count()

Get total requests made.

```python
count = llm.get_request_count()
```

**Returns:** int

### reset_session()

Reset HTTP session and clear state.

```python
llm.reset_session()
```

### close()

Close session and cleanup.

```python
llm.close()
```

---

## Retry Behavior

### Strategy

- Retries on status codes: 429, 500, 502, 503, 504
- Exponential backoff with configurable base delay
- Configurable maximum retry attempts

### Example

```python
config = LLMConfig(
    max_retries=5,        # Try up to 5 times
    retry_delay=2.0       # Start with 2s delay
)
```

Retry delays: 2s, 4s, 8s, 16s, 32s

---

## Logging

The LLM wrapper integrates with the project logger:

**Logged Events:**
- Initialization
- Request details (model, message count, temperature)
- Response details (ID, tokens used)
- Errors (connection, timeout, API)
- Session resets and closures

**Log Levels:**
- INFO: Normal operations
- DEBUG: Detailed information
- ERROR: Failures and exceptions

---

## Thread Safety

The LLM wrapper uses requests.Session which is not thread-safe. For concurrent usage:

1. Create separate LLM instances per thread
2. Use connection pooling (built-in)
3. Consider async alternatives for high concurrency

---

## Performance Tips

### Connection Reuse

```python
# Good: Reuse instance
llm = LLM(config)
for prompt in prompts:
    response = llm.chat_completion([Message(...)])

# Bad: New instance each time
for prompt in prompts:
    llm = LLM(config)  # Creates new connection
    response = llm.chat_completion([Message(...)])
    llm.close()
```

### Session Reset

For long-running processes, periodically reset:

```python
request_count = 0
for item in large_dataset:
    response = llm.chat_completion([...])
    request_count += 1

    if request_count % 100 == 0:
        llm.reset_session()  # Fresh connection pool
```

---

## Dependencies

```
pydantic>=2.0.0
requests>=2.31.0
urllib3>=2.0.0
```

---

## Future Enhancements

- Async/await support
- Response streaming
- Token usage tracking and limits
- Response caching
- Custom retry strategies
- Batch request support
- Rate limiting
