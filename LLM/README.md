# LLM Wrapper

Abstraction layer for LLM API interactions with error handling, retries, and logging.

---

## Overview

The LLM wrapper provides a clean interface for interacting with OpenAI-compatible APIs. It handles connection management, retries, error handling, and request/response logging.

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
