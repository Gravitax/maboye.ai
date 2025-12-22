# LLM Wrapper

## Synthesis

The `llm_wrapper` module acts as an abstraction layer for Large Language Model API interactions, decoupling the application's core logic from specific provider implementations. It centralizes authentication, configuration, and network communication. The architecture utilizes a component-based design where `RequestBuilder`, `RequestSender`, and `ResponseHandler` manage the lifecycle of an API call. This ensures consistent error handling, type safety via defined data contracts, and simplified access to chat, embedding, and model listing endpoints.

## Component Description

*   **`llm_wrapper.py`**: The main entry point. It initializes the client components, manages session state, and exposes high-level methods like `chat()` and `embedding()`.
*   **`config.py`**: Manages configuration settings, including API keys, base URLs, and model defaults.
*   **`types.py`**: Defines strict type definitions for messages, requests, and responses to ensure data integrity.
*   **`client/`**: Contains the low-level logic for constructing HTTP requests (`request_builder.py`), sending them (`request_sender.py`), and processing raw responses (`response_handler.py`).
*   **`routes/`**: Implements specific logic for different API endpoints such as authentication, chat completions, and embeddings.

## Configuration

The wrapper can be configured via a `config.json` file placed in the project root or `llm_wrapper/` directory.

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `base_url` | string | `https://api.deepseek.com` | Base URL of the LLM provider. |
| `api_key` | string | `""` | Authentication key (optional if auth disabled). |
| `model` | string | `deepseek-chat` | Model identifier to use. |
| `api_service` | string | `chat/completions` | Path to chat completion endpoint (relative to base). |
| `embed_service` | string | `""` | Path to embedding endpoint (relative to base). |
| `fim_service` | string | `beta/completions` | Path to FIM endpoint (relative to base). |
| `auth_enabled` | bool | `false` | Enable legacy/custom authentication flow. |
| `stream` | bool | `false` | Enable streaming for chat responses. |

### Configuration Profiles

#### 1. DeepSeek API (Default)
Standard configuration for the official DeepSeek API.

```json
{
    "base_url": "https://api.deepseek.com",
    "api_key": "YOUR_API_KEY",
    "model": "deepseek-chat",
    "api_service": "chat/completions",
    "fim_service": "beta/completions",
    "balance_service": "user/balance",
    "auth_enabled": false,
    "temperature": 0.0,
    "max_tokens": 4000,
    "stream": false
}
```

#### 2. Local Backend Mock
Configuration for the project's internal mock server (`backendMock`).
*Note: Ensure the backend is running via `./start.sh --backend`.*

```json
{
    "base_url": "http://127.0.0.1:8000",
    "api_key": "any",
    "model": "mock-model",
    "api_service": "v1",
    "models_service": "v1/models",
    "embed_service": "embed/v1",
    "auth_enabled": false,
    "temperature": 0.7,
    "max_tokens": 1000
}
```

#### 3. Private Mistral / vLLM Instance
Configuration for the specific private instance at `192.168.239.20` using `Devstral`.

```json
{
    "base_url": "https://192.168.239.20",
    "api_key": "sk-de84accdaf814042a15cbf4aadd8dde7",
    "model": "Devstral-Small-2507",
    "api_service": "code/v1",
    "embed_service": "embed/v1",
    "auth_enabled": false,
    "temperature": 0.3,
    "max_tokens": 1000,
    "timeout": 30
}
```