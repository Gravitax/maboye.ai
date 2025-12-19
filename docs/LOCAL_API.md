# LLM API Endpoints Documentation

**Base URL:** `https://192.168.239.20`

This document provides an overview of the available API endpoints, their functionalities, and expected request/response formats, based on `llm_wrapper/test_routes.py`.

---

## 1. Authentication

### POST `/api/v1/auths/signin`
* **Description:** Authenticates a user and returns a JWT token for accessing protected routes.
* **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "your_password"
    }
    ```
* **Response:**
    ```json
    {
        "token": "ey...",
        "user": {
            "id": "...",
            "email": "user@example.com"
        }
    }
    ```

---

## 2. Health Check

### GET `/health`
* **Description:** Checks the health status of the API.
* **Response:**
    ```json
    {
      "status": "ok"
    }
    ```

---

## 3. Global API Service (`/api/v1`)
**Prefix:** `/api/v1`
**Description:** A general-purpose endpoint that routes requests to any available model, including both chat and code models.

### GET `/api/v1/models`
* **Description:** Lists all models accessible through the global API.
* **Response:** A list of available model objects.
    ```json
    {
      "object": "list",
      "data": [
        { "id": "Mistral-Small", "object": "model", "owned_by": "vllm" },
        { "id": "Devstral-Small-2507", "object": "model", "owned_by": "vllm" }
      ]
    }
    ```

### POST `/api/v1/chat/completions`
* **Description:** Generates a conversational completion.
* **Request Body:**
    ```json
    {
        "model": "Mistral-Small",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": false
    }
    ```
* **Response:** A standard chat completion object.

### POST `/api/v1/completions`
* **Description:** Generates a standard text completion.
* **Request Body:**
    ```json
    {
        "model": "Mistral-Small",
        "prompt": "def fibonacci(n):",
        "max_tokens": 128,
        "temperature": 0.5,
        "stream": false
    }
    ```
* **Response:** A standard text completion object.

---

## 4. Chat Service (`/chat/v1`)
**Prefix:** `/chat/v1`
**Description:** A specialized service for conversational models (e.g., `Mistral-Small`).

### GET `/chat/v1/models`
* **Description:** Lists all models available within the chat service.
* **Response:** Similar to `/api/v1/models`, but may be filtered to chat-specific models.

### POST `/chat/v1/chat/completions`
* **Description:** Generates a conversational completion using a chat model.
* **Request Body:** Same as `/api/v1/chat/completions`.

### POST `/chat/v1/completions`
* **Description:** Generates a text completion using a chat model.
* **Request Body:** Same as `/api/v1/completions`.

---

## 5. Code Service (`/code/v1`)
**Prefix:** `/code/v1`
**Description:** A specialized service for code generation and analysis models (e.g., `Devstral-Small-2507`).

### GET `/code/v1/models`
* **Description:** Lists all models available within the code service.
* **Response:** Similar to `/api/v1/models`, but may be filtered to code-specific models.

### POST `/code/v1/chat/completions`
* **Description:** Generates a conversational completion using a code model.
* **Request Body:** Same as `/api/v1/chat/completions`, with the `model` parameter set to a code model like `Devstral-Small-2507`.

### POST `/code/v1/completions`
* **Description:** Generates a text completion using a code model.
* **Request Body:** Same as `/api/v1/completions`, with the `model` parameter set to a code model like `Devstral-Small-2507`.

---

## 6. Embedding Service (`/embed/v1`)
**Prefix:** `/embed/v1`
**Description:** A dedicated service for generating text embeddings.

### GET `/embed/v1/models`
* **Description:** Lists all available embedding models.
* **Response:**
    ```json
    {
      "object": "list",
      "data": [
        { "id": "all-MiniLM-L6-v2", "object": "model", "owned_by": "sentence-transformers" }
      ]
    }
    ```

### POST `/embed/v1/embeddings`
* **Description:** Creates vector embeddings for a given text input.
* **Request Body:**
    ```json
    {
        "model": "all-MiniLM-L6-v2",
        "input": "This is a test sentence.",
        "encoding_format": "float"
    }
    ```
* **Response:**
    ```json
    {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.01, -0.02, ...],
                "index": 0
            }
        ],
        "model": "all-MiniLM-L6-v2"
    }
    ```

---

## 7. Ollama-Compatible Service (`/ollama`)
**Prefix:** `/ollama`
**Description:** An experimental service providing compatibility with the Ollama API specification.

### GET `/ollama/api/tags`
* **Description:** Lists all local models available through the Ollama-compatible endpoint.
* **Response:**
    ```json
    {
      "models": [
        {
          "name": "llama3.1:latest",
          "model": "llama3.1:latest",
          "modified_at": "...",
          "size": 4100000000,
          "digest": "..."
        }
      ]
    }
    ```

### POST `/ollama/api/generate`
* **Description:** Generates a completion for a given prompt (non-streamed).
* **Request Body:**
    ```json
    {
        "model": "llama3.1",
        "prompt": "Why is the sky blue?",
        "stream": false
    }
    ```
* **Response:**
    ```json
    {
        "model": "llama3.1",
        "created_at": "...",
        "response": "The sky is blue because...",
        "done": true
    }
    ```

### POST `/ollama/api/embed`
* **Description:** Generates embeddings for a given input.
* **Request Body:**
    ```json
    {
        "model": "llama3.1",
        "input": "This is a test sentence."
    }
    ```
* **Response:**
    ```json
    {
        "embeddings": [
            [0.123, 0.456, ...]
        ]
    }
    ```