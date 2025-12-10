# LLM API Endpoints Documentation

**Base URL:** `https://192.168.239.20`

## 1. Global API Service (`/api/v1`)
**Prefix:** `/api/v1`
**Description:** General access point for transversal functionalities. Routes requests to all available models (e.g., `Mistral-Small`, `Devstral-Small-2507`).

### GET `/api/v1/models`
* **Description:** Lists all models accessible via the global API.
* **Response:** JSON object containing a list of model objects.
    ```json
    {
      "object": "list",
      "data": [
        {
          "id": "Mistral-Small",
          "object": "model",
          "owned_by": "vllm"
        },
        {
          "id": "Devstral-Small-2507",
          "object": "model",
          "owned_by": "vllm"
        }
      ]
    }
    ```

### POST `/api/v1/chat/completions`
* **Description:** Generates conversational completions.
* **Request Parameters (JSON):**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "messages": "This is a test sentence.",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
  ```
* **Response:**
    ```json
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "model": "Mistral-Small",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Response content..."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 5,
        "completion_tokens": 37,
        "total_tokens": 42
      }
    }
    ```

### POST `/api/v1/completions`
* **Description:** Text completions.
* **Request Parameters (JSON):**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "messages": "This is a test sentence.",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
  ```

* **Response:**
    ```json
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "model": "Mistral-Small",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Response content..."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 5,
        "completion_tokens": 37,
        "total_tokens": 42
      }
    }
    ```

### POST `/api/v1/embeddings`
* **Description:** Vector embedding generation.
* **Reauest:**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "input": "This is a test sentence.",
      "encoding_format": "float"
    }
  }
  ```
* **Response:**
    ```json
    {
      "error": {
        "message": "The model does not support Embeddings API",
        "type": "BadRequestError",
        "code": 400
      }
    }
    ```

---

## 2. Chat Service (`/chat/v1`)
**Prefix:** `/chat/v1`
**Description:** Service dedicated to general conversation models (e.g., `Mistral-Small`).

### GET `/chat/v1/models`
* **Description:** Lists all models accessible via the global API.
* **Response:** JSON object containing a list of model objects.
    ```json
    {
      "object": "list",
      "data": [
        {
          "id": "Mistral-Small",
          "object": "model",
          "owned_by": "vllm"
        },
        {
          "id": "Devstral-Small-2507",
          "object": "model",
          "owned_by": "vllm"
        }
      ]
    }
    ```

### POST `/chat/v1/chat/completions`
* **Description:** Generates conversational completions.
* **Request Parameters (JSON):**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "messages": "This is a test sentence.",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
  ```
* **Response:**
    ```json
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "model": "Mistral-Small",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Response content..."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 5,
        "completion_tokens": 37,
        "total_tokens": 42
      }
    }
    ```

### POST `/chat/v1/completions`
* **Description:** Text completions.
* **Request Parameters (JSON):**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "messages": "This is a test sentence.",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
  ```

* **Response:**
    ```json
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "model": "Mistral-Small",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Response content..."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 5,
        "completion_tokens": 37,
        "total_tokens": 42
      }
    }
    ```

### POST `/chat/v1/embeddings`
* **Description:** Vector embedding generation.
* **Reauest:**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "input": "This is a test sentence.",
      "encoding_format": "float"
    }
  }
  ```
* **Response:**
    ```json
    {
      "error": {
        "message": "The model does not support Embeddings API",
        "type": "BadRequestError",
        "code": 400
      }
    }
    ```

---

## 3. Code Service (`/code/v1`)
**Prefix:** `/code/v1`
**Description:** Service dedicated to code generation and analysis models (e.g., `Devstral-Small-2507`).

### GET `/code/v1/models`
* **Description:** Lists all models accessible via the global API.
* **Response:** JSON object containing a list of model objects.
    ```json
    {
      "object": "list",
      "data": [
        {
          "id": "Mistral-Small",
          "object": "model",
          "owned_by": "vllm"
        },
        {
          "id": "Devstral-Small-2507",
          "object": "model",
          "owned_by": "vllm"
        }
      ]
    }
    ```

### POST `/code/v1/chat/completions`
* **Description:** Generates conversational completions.
* **Request Parameters (JSON):**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "messages": "This is a test sentence.",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
  ```
* **Response:**
    ```json
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "model": "Mistral-Small",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Response content..."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 5,
        "completion_tokens": 37,
        "total_tokens": 42
      }
    }
    ```

### POST `/code/v1/completions`
* **Description:** Text completions.
* **Request Parameters (JSON):**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "messages": "This is a test sentence.",
      "temperature": 0.7,
      "max_tokens": 1000
    }
  }
  ```

* **Response:**
    ```json
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "model": "Mistral-Small",
      "choices": [
        {
          "index": 0,
          "message": {
            "role": "assistant",
            "content": "Response content..."
          },
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 5,
        "completion_tokens": 37,
        "total_tokens": 42
      }
    }
    ```

### POST `/code/v1/embeddings`
* **Description:** Vector embedding generation.
* **Reauest:**
  ```json
  {
    "payload": {
      "model": "Mistral-Small",
      "input": "This is a test sentence.",
      "encoding_format": "float"
    }
  }
  ```
* **Response:**
    ```json
    {
      "error": {
        "message": "The model does not support Embeddings API",
        "type": "BadRequestError",
        "code": 400
      }
    }
    ```

---

## 4. Ollama Service (`/ollama`)
**Prefix:** `/ollama`
**Description:** Service compliant with the Ollama API specification. Note: Paths do not use `/v1`.

### GET `/ollama/api/tags`
* **Description:** Lists all available Ollama models.
* **Response:**
    ```json
    {
      "models": [] 
    }
    ```

### POST `/ollama/api/generate`
* **Description:** Generates a completion for a given prompt.
* **Request Parameters (JSON):**
    * `model` (string, required).
    * `prompt` (string, required).
    * `stream` (boolean, optional): Default `true`. Set to `false` for a single response object.
* **Response (if stream=false):**
    ```json
    {
      "model": "llama3.1",
      "created_at": "2023-08-04T19:22:45.499127Z",
      "response": "The sky is blue because...",
      "done": true
    }
    ```

### POST `/ollama/api/embed`
* **Description:** Generates embedding vectors.
* **Request Parameters (JSON):**
    * `model` (string, required).
    * `input` (string or array, required).
* **Response:**
    ```json
    {
      "embeddings": [
        [0.123, 0.456, ...]
      ]
    }
    ```
