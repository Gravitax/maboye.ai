# API Routes

OpenAI-compatible Mock API endpoints.

Base URL: `http://127.0.0.1:8000`

---

## POST /v1/chat/completions

Create a chat completion.

**Request Body:**
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "top_p": 1.0,
  "max_tokens": 150,
  "n": 1,
  "stop": null,
  "presence_penalty": 0.0,
  "frequency_penalty": 0.0,
  "user": "user-123"
}
```

**Response:** `200 OK`
```json
{
  "id": "chatcmpl-mock-1",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Mock response to: Hello!..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  }
}
```

## GET /v1/models

List available models.

**Response:** `200 OK`
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4",
      "object": "model",
      "created": 1234567890,
      "owned_by": "openai-mock"
    },
    {
      "id": "gpt-3.5-turbo",
      "object": "model",
      "created": 1234567890,
      "owned_by": "openai-mock"
    },
    {
      "id": "text-davinci-003",
      "object": "model",
      "created": 1234567890,
      "owned_by": "openai-mock"
    }
  ]
}
```

---

## GET /

Health check.

**Response:** `200 OK`
```json
{
  "status": "ok",
  "message": "OpenAI Mock API is running",
  "version": "1.0.0",
  "endpoints": [
    "POST /v1/chat/completions",
    "POST /v1/completions",
    "GET  /v1/models"
  ]
}
```

---

## GET /health

Detailed health status.

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2025-12-06T21:30:00.000000",
  "requests_processed": 42
}
```

---

## Error Responses

**400 Bad Request** - Invalid parameters or streaming requested
```json
{
  "detail": "Streaming is not supported in this mock implementation"
}
```

**500 Internal Server Error** - Server error
```json
{
  "detail": "Error message"
}
```

---

**Documentation:**
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
