"""
Configuration for LLM wrapper.

Provides configuration management for LLM instances with the following precedence:
1. Constructor arguments
2. config.json file
3. Environment variables
4. Default values
"""

import os
import json
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class LLMWrapperConfig:
    """
    Configuration for LLM wrapper.
    
    Loads settings from config.json (if present), environment variables, or defaults.
    """
    
    # Connection settings
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    # API Routes
    api_service: Optional[str] = None
    embed_service: Optional[str] = None
    fim_service: Optional[str] = None
    models_service: Optional[str] = None
    balance_service: Optional[str] = None
    
    # Model settings
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    stream: Optional[bool] = None
    
    # Auth (Legacy/Custom)
    email: Optional[str] = None
    password: Optional[str] = None
    auth_enabled: bool = False
    auth_service: Optional[str] = None
    
    # Internal
    use_payload_wrapper: bool = False
    config_path: str = os.path.join(os.path.dirname(__file__), "config.json")

    def __post_init__(self):
        """Load configuration from JSON/Env/Defaults after initialization."""
        
        # 1. Load config.json if it exists
        file_config = {}
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load {self.config_path}: {e}")

        # 2. Helper to resolve values
        def resolve(field_name: str, env_var: str, default: Any, cast_type: type = str):
            # If value was passed in constructor (is not None), keep it
            current_value = getattr(self, field_name)
            if current_value is not None:
                return current_value

            # Check config.json
            if field_name in file_config:
                val = file_config[field_name]
                if val is not None:
                    return val

            # Check Environment Variable
            env_val = os.getenv(env_var)
            if env_val:  # Treat empty string as None/False to allow fallback
                if cast_type == bool:
                    return env_val.lower() in ("true", "1", "yes", "on")
                try:
                    return cast_type(env_val)
                except (ValueError, TypeError):
                    pass 

            # Return Default
            return default

        # 3. Resolve all fields
        self.base_url = resolve("base_url", "LLM_BASE_URL", "https://api.deepseek.com")
        self.api_key = resolve("api_key", "API_KEY", "")
        
        self.api_service = resolve("api_service", "API_SERVICE", "chat/completions")
        self.fim_service = resolve("fim_service", "FIM_SERVICE", "beta/completions")
        self.embed_service = resolve("embed_service", "EMBED_SERVICE", "")
        self.models_service = resolve("models_service", "MODELS_SERVICE", "models")
        self.balance_service = resolve("balance_service", "BALANCE_SERVICE", "user/balance")
        
        self.model = resolve("model", "LLM_MODEL", "deepseek-chat")
        self.temperature = resolve("temperature", "LLM_TEMPERATURE", 0.0, float)
        self.max_tokens = resolve("max_tokens", "LLM_MAX_TOKENS", 4000, int)
        self.timeout = resolve("timeout", "LLM_TIMEOUT", 60, int)
        self.stream = resolve("stream", "LLM_STREAM", False, bool)
        
        self.email = resolve("email", "API_EMAIL", "")
        self.password = resolve("password", "API_PASSWORD", "")
        
        self.auth_enabled = resolve("auth_enabled", "AUTH_ENABLED", False, bool)
        self.auth_service = resolve("auth_service", "AUTH_SERVICE", "api/v1/auths/signin")
        
        if "use_payload_wrapper" in file_config:
            self.use_payload_wrapper = file_config["use_payload_wrapper"]

        # 4. Validation
        if self.temperature is not None and not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
            
        if self.timeout is not None and self.timeout <= 0:
            raise ValueError("Timeout must be positive")
