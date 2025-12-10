from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


def parse_endpoints(endpoints_str: str) -> Dict[str, str]:
    """
    Parses endpoint configuration string into a dictionary.
    
    Args:
        endpoints_str: A string containing endpoint configurations.
        
    Returns:
        A dictionary of endpoint configurations.
    """
    endpoints = {}
    if not endpoints_str:
        return endpoints

    for endpoint_pair in endpoints_str.split(','):
        endpoint_pair = endpoint_pair.strip()
        if ':' in endpoint_pair:
            name, path = endpoint_pair.split(':', 1)
            endpoints[name.strip()] = path.strip()

    return endpoints


def load_configuration() -> Dict[str, Any]:
    """
    Loads configuration from environment variables.

    Returns:
        A dictionary containing the configuration.
    """
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)

    base_url = os.getenv('API_BASE_URL', 'https://192.168.239.20')

    verify_ssl_str = os.getenv('API_VERIFY_SSL', 'false').lower()
    verify_ssl = verify_ssl_str in ('true', '1', 'yes')

    service_prefixes_str = os.getenv('API_SERVICE_PREFIXES', 'chat:/chat,code:/code,ollama:/ollama')
    service_prefixes = parse_endpoints(service_prefixes_str)
    
    if 'api' not in service_prefixes:
        service_prefixes['api'] = '/api'
    
    if 'ollama' not in service_prefixes:
        service_prefixes['ollama'] = '/ollama'
    
    additional_routes = {}
    
    api_key = os.getenv('API_KEY', 'sk-de84accdaf814042a15cbf4aadd8dde7')
    # Support both API_EMAIL/API_PASSWORD and EMAIL/PWD for backwards compatibility
    api_email = os.getenv('API_EMAIL') or os.getenv('EMAIL')
    api_password = os.getenv('API_PASSWORD') or os.getenv('PWD')


    config = {
        'base_url': base_url,
        'service_prefixes': service_prefixes,
        'additional_routes': additional_routes,
        'request_timeout': int(os.getenv('API_REQUEST_TIMEOUT', '30')),
        'verify_ssl': verify_ssl,
        'model': os.getenv('LLM_MODEL', 'Mistral-Small'),
        'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
        'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '100')),
        'api_key': api_key,
        'api_email': api_email,
        'api_password': api_password,
        'embedding_route_path': 'embeddings',
        'embedding_model_candidates': [
            'all-MiniLM-L6-v2',
            'bge-small-en-v1.5',
            'nomic-embed-text',
            'thenlper/gte-large'
        ]
    }

    return config
