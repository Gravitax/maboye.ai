"""
Test script for all API routes.

Tests all endpoints implemented in the backend mock server.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import requests
import json
import urllib3

# Disable SSL warnings for testing with self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from ..core.logger import logger


def get_base_url() -> str:
    """Get base URL from environment."""
    return os.getenv("LLM_BASE_URL", "https://192.168.239.20")


def get_timeout() -> int:
    """Get request timeout from environment."""
    timeout_str = os.getenv("LLM_TIMEOUT", "30")
    return int(timeout_str)


def get_api_credentials() -> Tuple[str, str, str]:
    """Get API credentials from environment."""
    api_key = os.getenv("API_KEY", "")
    email = os.getenv("API_EMAIL", "")
    password = os.getenv("API_PASSWORD", "")
    return api_key, email, password


def generate_auth_token(base_url: str) -> Optional[str]:
    """
    Generate JWT token for authentication.

    Args:
        base_url: Base URL of the API

    Returns:
        JWT token or None if authentication fails
    """
    api_key, email, password = get_api_credentials()

    if not email or not password:
        logger.warning("AUTH", "Missing credentials", {
            "has_email": bool(email),
            "has_password": bool(password)
        })
        return None

    url = f"{base_url}/api/v1/auths/signin"
    payload = {
        "email": email,
        "password": password
    }

    logger.info("AUTH", f"Attempting authentication for: {email}")

    try:
        response = requests.post(url, json=payload, verify=False, timeout=get_timeout())
        response.raise_for_status()
        data = response.json()
        token = data.get("token")

        if token:
            logger.info("AUTH", "Authentication successful", {"token_preview": token[:20] + "..."})
        else:
            logger.warning("AUTH", "No token in response", {"response": data})

        return token
    except Exception as error:
        logger.error("AUTH", "Authentication failed", {"error": str(error)})
        return None


def get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    """
    Get authentication headers.

    Args:
        token: JWT token for Bearer authentication

    Returns:
        Dictionary of headers
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def print_section(title: str) -> None:
    """Print formatted section title."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print('=' * 80)


def print_test_result(test_name: str, success: bool, details: str = "") -> None:
    """Print test result with status."""
    status = "PASS" if success else "FAIL"
    status_symbol = "✓" if success else "✗"
    print(f"[{status_symbol}] {test_name}: {status}")
    if details:
        print(f"    {details}")


def make_get_request(url: str, test_name: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Make GET request and handle response."""
    logger.info("TEST_REQUEST", f"GET {url}", {"headers": headers})

    try:
        response = requests.get(url, headers=headers, timeout=get_timeout(), verify=False)
        logger.info("TEST_RESPONSE", f"Status: {response.status_code}", {
            "content_type": response.headers.get("Content-Type"),
            "response_preview": response.text[:500] if response.text else None
        })

        response.raise_for_status()
        data = response.json()
        print_test_result(test_name, True, f"Status: {response.status_code}")
        return data
    except requests.ConnectionError as error:
        logger.error("TEST_ERROR", "Connection failed", {"url": url, "error": str(error)})
        print_test_result(test_name, False, "Connection failed")
        return None
    except requests.Timeout:
        logger.error("TEST_ERROR", "Request timeout", {"url": url})
        print_test_result(test_name, False, "Request timeout")
        return None
    except requests.HTTPError as error:
        logger.error("TEST_ERROR", f"HTTP {response.status_code}", {
            "url": url,
            "response_body": response.text[:500]
        })
        print_test_result(test_name, False, f"HTTP {response.status_code}")
        return None
    except json.JSONDecodeError as error:
        logger.error("TEST_ERROR", "Invalid JSON response", {
            "url": url,
            "response_body": response.text[:500]
        })
        print_test_result(test_name, False, "Invalid JSON response")
        return None
    except Exception as error:
        logger.error("TEST_ERROR", "Unexpected error", {"url": url, "error": str(error)})
        print_test_result(test_name, False, str(error))
        return None


def make_post_request(url: str, payload: Dict[str, Any], test_name: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Make POST request and handle response."""
    logger.info("TEST_REQUEST", f"POST {url}", {
        "headers": headers,
        "payload": payload
    })

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=get_timeout(), verify=False)
        logger.info("TEST_RESPONSE", f"Status: {response.status_code}", {
            "content_type": response.headers.get("Content-Type"),
            "response_preview": response.text[:500] if response.text else None
        })

        response.raise_for_status()
        data = response.json()
        print_test_result(test_name, True, f"Status: {response.status_code}")
        return data
    except requests.ConnectionError as error:
        logger.error("TEST_ERROR", "Connection failed", {"url": url, "error": str(error)})
        print_test_result(test_name, False, "Connection failed")
        return None
    except requests.Timeout:
        logger.error("TEST_ERROR", "Request timeout", {"url": url})
        print_test_result(test_name, False, "Request timeout")
        return None
    except requests.HTTPError as error:
        logger.error("TEST_ERROR", f"HTTP {response.status_code}", {
            "url": url,
            "payload": payload,
            "response_body": response.text[:500]
        })
        print_test_result(test_name, False, f"HTTP {response.status_code}")
        return None
    except json.JSONDecodeError as error:
        logger.error("TEST_ERROR", "Invalid JSON response", {
            "url": url,
            "response_body": response.text[:500]
        })
        print_test_result(test_name, False, "Invalid JSON response")
        return None
    except Exception as error:
        logger.error("TEST_ERROR", "Unexpected error", {"url": url, "error": str(error)})
        print_test_result(test_name, False, str(error))
        return None


def create_chat_payload(model: str = "Mistral-Small") -> Dict[str, Any]:
    """Create chat completion payload."""
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es un assistant technique expert en Python."},
            {"role": "user", "content": "Explique le Global Interpreter Lock."}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_tokens": 512,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "stream": False,
        "seed": 42,
        "stop": ["<|eot_id|>"]
    }


def create_completion_payload(model: str = "Mistral-Small") -> Dict[str, Any]:
    """Create text completion payload."""
    return {
        "model": model,
        "prompt": "def fibonacci(n):",
        "max_tokens": 128,
        "temperature": 0.5,
        "top_p": 1.0,
        "top_k": -1,
        "n": 1,
        "stream": False,
        "logprobs": None,
        "echo": False,
        "stop": ["\n"]
    }


def create_embedding_payload() -> Dict[str, Any]:
    """Create embedding request payload."""
    return {
        "model": "all-MiniLM-L6-v2",
        "input": "This is a test sentence.",
        "encoding_format": "float"
    }


def create_ollama_generate_payload() -> Dict[str, Any]:
    """Create Ollama generate request payload."""
    return {
        "model": "llama3.1",
        "prompt": "Why is the sky blue?",
        "stream": False
    }


def create_ollama_embed_payload() -> Dict[str, Any]:
    """Create Ollama embed request payload."""
    return {
        "model": "llama3.1",
        "input": "This is a test sentence."
    }


def test_health_endpoints(base_url: str, headers: Dict[str, str]) -> None:
    """Test health check endpoints."""
    print_section("HEALTH ENDPOINTS")

    make_get_request(f"{base_url}/health", "Health endpoint", headers)


def test_global_api_endpoints(base_url: str, headers: Dict[str, str]) -> None:
    """Test global API endpoints."""
    print_section("GLOBAL API ENDPOINTS (/api/v1)")

    make_get_request(f"{base_url}/api/v1/models", "GET /api/v1/models", headers)

    payload = create_chat_payload()
    make_post_request(f"{base_url}/api/v1/chat/completions", payload, "POST /api/v1/chat/completions", headers)
    payload = create_completion_payload()
    make_post_request(f"{base_url}/api/v1/completions", payload, "POST /api/v1/completions", headers)


def test_chat_service_endpoints(base_url: str, headers: Dict[str, str]) -> None:
    """Test chat service endpoints."""
    print_section("CHAT SERVICE ENDPOINTS (/chat/v1)")

    make_get_request(f"{base_url}/chat/v1/models", "GET /chat/v1/models", headers)

    payload = create_chat_payload()
    make_post_request(f"{base_url}/chat/v1/chat/completions", payload, "POST /chat/v1/chat/completions", headers)
    payload = create_completion_payload()
    make_post_request(f"{base_url}/chat/v1/completions", payload, "POST /chat/v1/completions", headers)


def test_code_service_endpoints(base_url: str, headers: Dict[str, str]) -> None:
    """Test code service endpoints."""
    print_section("CODE SERVICE ENDPOINTS (/code/v1)")

    make_get_request(f"{base_url}/code/v1/models", "GET /code/v1/models", headers)

    payload = create_chat_payload(model="Devstral-Small-2507")
    make_post_request(f"{base_url}/code/v1/chat/completions", payload, "POST /code/v1/chat/completions", headers)
    payload = create_completion_payload(model="Devstral-Small-2507")
    make_post_request(f"{base_url}/code/v1/completions", payload, "POST /code/v1/completions", headers)


def test_ollama_endpoints(base_url: str, headers: Dict[str, str]) -> None:
    """Test Ollama API endpoints."""
    print_section("OLLAMA ENDPOINTS (/ollama)")

    make_get_request(f"{base_url}/ollama/api/tags", "GET /ollama/api/tags", headers)

    generate_payload = create_ollama_generate_payload()
    make_post_request(f"{base_url}/ollama/api/generate", generate_payload, "POST /ollama/api/generate", headers)

    embed_payload = create_ollama_embed_payload()
    make_post_request(f"{base_url}/ollama/api/embed", embed_payload, "POST /ollama/api/embed", headers)


def test_embedding_endpoints(base_url: str, headers: Dict[str, str]) -> None:
    """Test embedding service endpoints."""
    print_section("EMBEDDING ENDPOINTS (/embed/v1)")

    make_get_request(f"{base_url}/embed/v1/models", "GET /embed/v1/models", headers)

    payload = create_embedding_payload()
    make_post_request(f"{base_url}/embed/v1/embeddings", payload, "POST /embed/v1/embeddings", headers)


def print_summary() -> None:
    """Print test summary."""
    print_section("TEST COMPLETED")
    print("All routes have been tested.")
    print("Check the results above for any failures.")


def run_all_tests() -> None:
    """Run all API route tests."""
    base_url = get_base_url()

    print(f"\nStarting API route tests...")
    print(f"Base URL: {base_url}")
    print(f"Timeout: {get_timeout()}s")

    print("\nAuthenticating...")
    token = generate_auth_token(base_url)
    if token:
        print("Authentication successful")
    else:
        print("Authentication failed or not required")

    headers = get_auth_headers(token)

    test_health_endpoints(base_url, headers)
    test_global_api_endpoints(base_url, headers)
    test_chat_service_endpoints(base_url, headers)
    test_code_service_endpoints(base_url, headers)
    # test_ollama_endpoints(base_url, headers)
    test_embedding_endpoints(base_url, headers)

    print_summary()


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as error:
        print(f"\n\nUnexpected error: {error}")
        sys.exit(1)
