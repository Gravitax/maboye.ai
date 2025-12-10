from __future__ import annotations

from typing import Any, Dict


def build_legacy_completion_payload(content: str, model: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
    """
    Builds a test payload for the legacy /v1/completions endpoint using 'prompt'.
    
    Args:
        content: The content of the prompt.
        model: The model to use for the completion.
        temperature: The temperature to use for the completion.
        max_tokens: The maximum number of tokens to generate.
        
    Returns:
        A dictionary representing the payload.
    """
    return {
        "model": model,
        "prompt": content,
        "temperature": temperature,
        "max_tokens": max_tokens
    }


def build_chat_completion_payload(content: str, model: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
    """
    Builds a test message payload for the LLM endpoint using OpenAI Chat format (messages).
    
    Args:
        content: The content of the user message.
        model: The model to use for the completion.
        temperature: The temperature to use for the completion.
        max_tokens: The maximum number of tokens to generate.
        
    Returns:
        A dictionary representing the payload.
    """
    return {
        "model": model,
        "messages": [
            {"role": "user", "content": content}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }


def build_embedding_payload(model_id: str, input_text: str) -> Dict[str, Any]:
    """
    Builds the test payload for the embeddings endpoint.
    
    Args:
        model_id: The ID of the model to use for the embedding.
        input_text: The text to embed.
        
    Returns:
        A dictionary representing the payload.
    """
    return {
        "model": model_id, 
        "input": input_text,
        "encoding_format": "float"
    }
