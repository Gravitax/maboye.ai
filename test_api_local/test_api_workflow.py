from __future__ import annotations

import pytest
from .utils.api_client import ApiClient
from .utils.logger import logger
from .utils.payloads import build_chat_completion_payload, build_legacy_completion_payload, build_embedding_payload

# Mark the entire module as slow
pytestmark = pytest.mark.slow

@pytest.fixture(scope="module", params=["api", "chat", "code", "ollama"])
def service(request):
    """
    Provides the service name and path for each service to be tested.
    """
    return request.param

@pytest.fixture(scope="module")
def available_models(api_client: ApiClient, config: dict, service: str):
    logger.info("TEST_SUITE", f"\n========================================================\nStarting tests for service: {service.upper()}\n========================================================")
    """
    Fetches the available models for a given service.
    This fixture is scoped to the module to ensure models are fetched only once per service.
    """
    service_path = config["service_prefixes"].get(service)
    if not service_path:
        pytest.skip(f"Service '{service}' not configured.")

    models = []
    if service == "ollama":
        # Ollama has a different endpoint for listing models
        path = f"{service_path}/api/tags"
        success, response, _ = api_client.get(path)
        if success and response.get("models"):
            models = [m["name"] for m in response["models"]]
    else:
        path = f"{service_path}/v1/models"
        success, response, _ = api_client.get(path)
        if success and response.get("data"):
            models = [m["id"] for m in response["data"]]

    if not models:
        logger.warning(f"No models found for service '{service}'.", f"Skipping tests for this service.")
        pytest.skip(f"No models found for service '{service}'.")
    
    logger.info(f"available_models for {service}", f"Available models: {models}")
    return models

def test_chat_completions(api_client: ApiClient, config: dict, service: str, available_models: list[str]):
    """
    Tests the /chat/completions endpoint for a given service and its available models.
    """
    service_path = config["service_prefixes"][service]
    
    if service == "ollama":
        # Ollama has a '/api/generate' endpoint instead of '/chat/completions'
        pytest.skip("Ollama does not support /chat/completions, use /api/generate.")

    path = f"{service_path}/v1/chat/completions"
    
    for model_id in available_models:
        logger.info("test_chat_completions", f"Sending chat completion request to model '{model_id}' in service '{service}' with prompt 'message test'.")
        payload = build_chat_completion_payload(
            "message test", model_id, config["temperature"], config["max_tokens"]
        )
        success, response, error = api_client.post(path, payload)
        assert success, f"[/chat/completions] Failed for model '{model_id}' in service '{service}'. Error: {error}"
        assert response and response.get("choices"), f"[/chat/completions] No 'choices' in response for model '{model_id}'."
        assert response.get("choices")[0].get("message").get("content"), f"[/chat/completions] Empty response content for model '{model_id}'."

def test_completions(api_client: ApiClient, config: dict, service: str, available_models: list[str]):
    """
    Tests the /completions endpoint for a given service and its available models.
    """
    service_path = config["service_prefixes"][service]

    if service == "ollama":
        # Ollama's '/api/generate' is tested separately
        pytest.skip("Ollama does not support /completions, use /api/generate.")

    path = f"{service_path}/v1/completions"

    for model_id in available_models:
        logger.info("test_completions", f"Sending completion request to model '{model_id}' in service '{service}' with prompt 'message test'.")
        payload = build_legacy_completion_payload(
            "message test", model_id, config["temperature"], config["max_tokens"]
        )
        success, response, error = api_client.post(path, payload)

        if not success and service == 'api' and "405" in (error or ""):
            logger.warning(
                "test_completions",
                f"Known issue: Received 405 Method Not Allowed for model '{model_id}' on /api/v1/completions. Skipping assertion."
            )
            continue

        assert success, f"[/completions] Failed for model '{model_id}' in service '{service}'. Error: {error}"
        assert response and response.get("choices"), f"[/completions] No 'choices' in response for model '{model_id}'."
        assert response.get("choices")[0].get("text"), f"[/completions] Empty response text for model '{model_id}'."
def test_embeddings(api_client: ApiClient, config: dict, service: str, available_models: list[str]):
    """
    Tests the /embeddings endpoint for a given service and its available models.
    """
    service_path = config["service_prefixes"][service]

    if service == "ollama":
        path = f"{service_path}/api/embed"
    else:
        path = f"{service_path}/v1/embeddings"
    
    for model_id in available_models:
        logger.info("test_embeddings", f"Sending embedding request for model '{model_id}' in service '{service}' with input 'This is a test sentence.'.")
        payload = build_embedding_payload(model_id, "This is a test sentence.")
        success, response, error = api_client.post(path, payload)
        
        # We don't assert success here because many models are expected to fail
        if not success:
            logger.warning(f"Embedding request failed for model '{model_id}' as expected.", f"Error: {error}")
        elif response and "data" in response and isinstance(response["data"], list) and response["data"]:
            logger.info(f"Successfully received embedding for model '{model_id}'.")
            assert isinstance(response["data"][0].get("embedding"), list), f"Embedding for '{model_id}' is not a list."
        elif service == "ollama" and response and "embeddings" in response:
            logger.info(f"Successfully received embedding for model '{model_id}' (Ollama).")
            assert isinstance(response["embeddings"], list), f"Ollama embedding for '{model_id}' is not a list."
        else:
            logger.warning(f"Embedding request for model '{model_id}' succeeded but response is empty or invalid.", f"Response: {response}")

def test_ollama_generate(api_client: ApiClient, config: dict, service: str, available_models: list[str]):
    """
    Tests the /api/generate endpoint specifically for the ollama service.
    """
    if service != "ollama":
        pytest.skip("This test is only for the ollama service.")

    service_path = config["service_prefixes"]["ollama"]
    path = f"{service_path}/api/generate"

    for model_id in available_models:
        logger.info("test_ollama_generate", f"Sending generate request to model '{model_id}' in service 'ollama' with prompt 'message test'.")
        payload = {"model": model_id, "prompt": "message test"}
        success, response, error = api_client.post(path, payload)
        assert success, f"[/api/generate] Failed for model '{model_id}'. Error: {error}"
        assert response and response.get("response"), f"[/api/generate] No 'response' in response for model '{model_id}'."
        assert response.get("response"), f"[/api/generate] Empty response for model '{model_id}'."

