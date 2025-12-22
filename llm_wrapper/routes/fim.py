from typing import Any, Dict
from llm_wrapper.types import FimResponse

def fim_completion(wrapper, prompt: str, suffix: str, max_tokens: int = 128) -> FimResponse:
    """
    Perform Fill-In-the-Middle (FIM) code completion.
    
    Compatible with DeepSeek API: /beta/completions
    Payload matches example: model, prompt, suffix, max_tokens.
    """
    # Construct URL based on config (defaults to beta/completions)
    url = f"{wrapper.config.base_url}/{wrapper.config.fim_service}"
    
    payload = {
        "model": wrapper.config.model,
        "prompt": prompt,
        "suffix": suffix,
        "max_tokens": max_tokens,
        "temperature": wrapper.config.temperature
    }
    
    # Send request using wrapper's centralized sender
    # Headers are built via request_builder (Authorization: Bearer <KEY>)
    response = wrapper.request_sender.send_request(
        wrapper.session,
        "POST",
        url,
        headers=wrapper.request_builder.build_headers(wrapper.token, wrapper.config.api_key),
        json=payload,
        timeout=wrapper.config.timeout
    )
    
    data = wrapper.response_handler.handle_response(response)
    return FimResponse(**data)
