# LLM Dynamic Route Configuration Proposal

## Goal
To enable flexible configuration of multiple Large Language Model (LLM) providers (e.g., DeepSeek, OpenAI, Mistral, custom endpoints) by loading their specific settings from a JSON file. This allows for easy switching and dynamic assignment of LLMs without code modification.

## Strategy

### 1. Configuration File Location and Naming
- **File**: `llm_routes.json`
- **Location**: Project root or within a dedicated `config/` directory.

### 2. Proposed JSON Schema

The `llm_routes.json` file will contain a `default_route` identifier and a `routes` object. The `routes` object will map user-defined route names to their respective configuration settings.

```json
{
  "default_route": "deepseek_cloud",
  "routes": {
    "deepseek_cloud": {
      "type": "openai_compatible",
      "base_url": "https://api.deepseek.com/v1",
      "api_key_env": "DEEPSEEK_API_KEY",
      "model": "deepseek-chat",
      "parameters": {
        "temperature": 0.0,
        "max_tokens": 2000
      },
      "headers": {}
    },
    "mistral_local": {
      "type": "ollama",
      "base_url": "http://localhost:11434",
      "model": "mistral:latest",
      "parameters": {
        "temperature": 0.7
      }
    },
    "openai_gpt4": {
      "type": "openai",
      "api_key_env": "OPENAI_API_KEY",
      "model": "gpt-4-turbo",
      "parameters": {
        "temperature": 0.5,
        "max_tokens": 1500
      }
    },
    "custom_internal": {
      "type": "custom",
      "base_url": "https://internal-ai.corp/v1",
      "api_key_env": "INTERNAL_KEY",
      "headers": {
        "X-Custom-Auth": "Bearer {INTERNAL_KEY_VALUE}",
        "User-Agent": "MyCustomClient"
      },
      "parameters": {}
    }
  }
}
```

### 3. Route Configuration Object Schema (`routes.<route_name>`)

Each entry under `"routes"` is an object with the following fields:

-   **`type` (string, required)**:
    -   Defines the LLM provider's API type.
    -   **Possible values**:
        -   `"openai"`: For OpenAI's official API.
        -   `"openai_compatible"`: For providers that mimic OpenAI's API (e.g., DeepSeek, Groq, TogetherAI).
        -   `"ollama"`: For local Ollama instances.
        -   `"azure"`: For Azure OpenAI Service.
        -   `"custom"`: For highly customized endpoints requiring specific headers or authentication.
        -   *(Extendable with more types like "anthropic", "google" as needed)*.
-   **`base_url` (string, optional)**: The base URL for the API endpoint. Required for `ollama`, `openai_compatible`, `custom`. For `"openai"`, it defaults to OpenAI's API base URL.
-   **`api_key_env` (string, optional)**:
    -   The name of the environment variable (e.g., `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`) that holds the API key.
    -   **Security Best Practice**: API keys are NEVER stored directly in this JSON file.
-   **`model` (string, required)**: The specific model identifier (e.g., `"gpt-4-turbo"`, `"deepseek-chat"`, `"mistral:latest"`).
-   **`headers` (object, optional)**: A dictionary of custom HTTP headers to send with requests. Useful for `custom` types or specific authentication schemes. Environment variables can be interpolated using `{ENV_VAR_NAME}` syntax.
-   **`parameters` (object, optional)**: A dictionary of default LLM parameters (e.g., `temperature`, `max_tokens`, `top_p`, `frequency_penalty`) specific to this route. These can be overridden by agent configurations or direct call parameters.

### 4. Loading and Integration Mechanism

1.  **`LLMWrapperConfig` Enhancement**:
    -   The `LLMWrapperConfig` class (or a new `LLMRouteManager`) will be responsible for loading `llm_routes.json`.
    -   It will parse the JSON, validate the schema, and resolve `api_key_env` fields by fetching values from `os.environ`.
    -   It will create a dictionary of ready-to-use LLM client configurations.

2.  **`LLMWrapper` Client Instantiation**:
    -   The `LLMWrapper` will be updated to manage multiple underlying LLM client instances (e.g., `OpenAI()`, `OllamaClient()`).
    -   When `LLMWrapper.chat()` is called, it will identify which route to use (from agent config or a default) and use the corresponding client.

3.  **Agent Profile Integration**:
    -   The `agents/profiles/*.json` files (which currently have `llm_config` parameters) will be extended with a `"route": "<route_name>"` field.
    -   This allows binding specific agents (e.g., "CodeAgent", "TasksAgent") to a named LLM route defined in `llm_routes.json`.
    -   Agent-specific `llm_config` parameters (temperature, max_tokens) in the agent profile will override defaults specified in `llm_routes.json`.

## Benefits of this Approach

-   **Flexibility**: Easily switch LLM providers or models without changing code.
-   **Security**: API keys are managed via environment variables, not committed to source control.
-   **Granularity**: Different agents can be configured to use different LLMs, optimizing performance and cost for specific tasks.
-   **Scalability**: New LLM providers can be added by simply extending the JSON file and potentially a new `type` handler in `LLMWrapper`.
-   **Centralized Control**: All LLM routing configuration is in one place.
