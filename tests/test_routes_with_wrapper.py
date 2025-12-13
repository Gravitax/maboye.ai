
"""
Test script for for all API routes using LLMWrapper.

Tests all endpoints implemented in the backend mock server using the LLMWrapper.
"""

import os
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv
import urllib3

# Disable SSL warnings for testing with self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from core.logger import logger
from core.llm_wrapper.llm_wrapper import LLMWrapper, LLMWrapperConfig
from core.llm_wrapper.llm_types import LLMMessage


def get_base_url() -> str:
    """Get base URL from environment."""
    return os.getenv("LLM_BASE_URL", "https://192.168.239.20")

def get_timeout() -> int:
    """Get request timeout from environment."""
    timeout_str = os.getenv("LLM_TIMEOUT", "30")
    return int(timeout_str)

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

def test_list_models(llm_wrapper: LLMWrapper, test_name: str) -> List[str]:
    """Test the list_models endpoint and return the list of models."""
    logger.info("TEST_REQUEST", f"GET /models", {})
    try:
        models_response = llm_wrapper.list_models()
        model_ids = [model.id for model in models_response.data]
        logger.info("TEST_RESPONSE", f"Found {len(model_ids)} models", {"models": model_ids})
        print_test_result(test_name, True, f"Found {len(model_ids)} models")
        return model_ids
    except Exception as e:
        logger.error("TEST_ERROR", "Failed to list models", {"error": str(e)})
        print_test_result(test_name, False, str(e))
        return []

def test_chat_completions(llm_wrapper: LLMWrapper, test_name: str, messages: List[LLMMessage]) -> None:
    """Test the chat completions endpoint using LLMWrapper."""
    logger.info("TEST_REQUEST", f"POST /chat/completions", {})
    try:
        chat_response = llm_wrapper.chat(messages, verbose=True)
        logger.info("TEST_RESPONSE", f"Response from {chat_response.model}", {})
        print_test_result(test_name, True, f"Response from {chat_response.model}")
    except Exception as e:
        logger.error("TEST_ERROR", "Failed to get chat completion", {"error": str(e)})
        print_test_result(test_name, False, str(e))

def create_chat_messages() -> List[LLMMessage]:
    """Create a list of LLMMessage for chat completions."""
    return [
        LLMMessage(role="system", content="Tu es un assistant technique expert en Python."),
        LLMMessage(role="user", content="Explique le Global Interpreter Lock.")
    ]

def test_chat_service_endpoints(base_url: str) -> None:
    """Test chat service endpoints."""
    print_section("CHAT SERVICE ENDPOINTS (/chat/v1)")
    config = LLMWrapperConfig(base_url=base_url, api_service="chat/v1")
    llm_wrapper = LLMWrapper(config=config)
    models = test_list_models(llm_wrapper, "GET /chat/v1/models")
    if not models:
        return
    llm_wrapper.config.model = models[0]
    messages = create_chat_messages()
    test_chat_completions(llm_wrapper, "POST /chat/v1/chat/completions", messages)

def test_global_api_endpoints(base_url: str) -> None:
    """Test global API endpoints."""
    print_section("GLOBAL API ENDPOINTS (/api/v1)")
    config = LLMWrapperConfig(base_url=base_url, api_service="api/v1")
    llm_wrapper = LLMWrapper(config=config)
    models = test_list_models(llm_wrapper, "GET /api/v1/models")
    if not models:
        return
    llm_wrapper.config.model = models[0]
    messages = create_chat_messages()
    test_chat_completions(llm_wrapper, "POST /api/v1/chat/completions", messages)

def test_embedding_service_endpoints(base_url: str) -> None:
    """Test embedding service endpoints."""
    print_section("EMBEDDING SERVICE ENDPOINTS (/embed/v1)")
    config = LLMWrapperConfig(base_url=base_url)
    llm_wrapper = LLMWrapper(config=config)
    models = test_list_embedding_models(llm_wrapper, "GET /embed/v1/models")
    if not models:
        return
    llm_wrapper.config.model = models[0]
    input_texts = create_embedding_input()

    test_embedding(llm_wrapper, "POST /embed/v1/embeddings", input_texts)

def test_list_embedding_models(llm_wrapper: LLMWrapper, test_name: str) -> List[str]:
    """Test the list_embedding_models endpoint using LLMWrapper and return model IDs."""
    logger.info("TEST_REQUEST", f"GET /models", {})
    try:
        models_response = llm_wrapper.list_embedding_models()
        model_ids = [model.id for model in models_response.data]
        logger.info("TEST_RESPONSE", f"Found {len(model_ids)} models", {"models": model_ids})
        print_test_result(test_name, True, f"Found {len(model_ids)} models")
        return model_ids
    except Exception as e:
        logger.error("TEST_ERROR", "Failed to list models", {"error": str(e)})
        print_test_result(test_name, False, str(e))
        return []

def test_embedding(llm_wrapper: LLMWrapper, test_name: str, input_texts: List[str]) -> None:
    """Test the embedding endpoint using LLMWrapper."""
    logger.info("TEST_REQUEST", f"POST /embeddings", {})
    try:
        embedding_response = llm_wrapper.embedding(input_texts)
        logger.info("TEST_RESPONSE", f"Got {len(embedding_response.data)} embeddings", {})
        print_test_result(test_name, True, f"Got {len(embedding_response.data)} embeddings")
    except Exception as e:
        logger.error("TEST_ERROR", "Failed to get embeddings", {"error": str(e)})
        print_test_result(test_name, False, str(e))

def create_embedding_input() -> List[str]:
    """Create a list of strings for embedding."""
    return ["This is a test sentence.", "This is another test sentence."]

def print_summary() -> None:
    """Print test summary."""
    print_section("TEST COMPLETED")
    print("All routes have been tested using LLMWrapper.")
    print("Check the results above for any failures.")

def run_all_tests() -> None:
    """Run all API route tests."""
    base_url = get_base_url()

    print(f"\nStarting API route tests with LLMWrapper...")
    print(f"Base URL: {base_url}")
    print(f"Timeout: {get_timeout()}s")

    test_global_api_endpoints(base_url)
    test_chat_service_endpoints(base_url)
    test_embedding_service_endpoints(base_url)

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
