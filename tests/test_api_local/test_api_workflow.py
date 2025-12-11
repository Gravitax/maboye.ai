from __future__ import annotations

import pytest
from utils.api_client import ApiClient
from utils.logger import logger
from utils.payloads import build_chat_completion_payload, build_legacy_completion_payload, build_embedding_payload

# Mark the entire module as slow
pytestmark = pytest.mark.slow

@pytest.fixture(scope="module", params=["api", "chat", "code", "ollama", "embed"])
def service(request):
    """
    Provides the service name and path for each service to be tested.
    """
    return request.param

@pytest.fixture(scope="module")
def available_models(api_client: ApiClient, config: dict, service: str):
    logger.separator(f"SERVICE: {service.upper()}", width=80)
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
        logger.info("ROUTE", f"{'-' * 80}")
        logger.info("ROUTE", f"Fetching models from: {path}")
        logger.info("ROUTE", f"{'-' * 80}")
        success, response, _ = api_client.get(path)
        if success and response.get("models"):
            models = [m["name"] for m in response["models"]]
    else:
        path = f"{service_path}/v1/models"
        logger.info("ROUTE", f"{'-' * 80}")
        logger.info("ROUTE", f"Fetching models from: {path}")
        logger.info("ROUTE", f"{'-' * 80}")
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

    logger.info("ROUTE", f"{'-' * 80}")
    logger.info("ROUTE", f"Testing route: {service_path}/v1/chat/completions")
    logger.info("ROUTE", f"{'-' * 80}")

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

    logger.info("ROUTE", f"{'-' * 80}")
    logger.info("ROUTE", f"Testing route: {service_path}/v1/completions")
    logger.info("ROUTE", f"{'-' * 80}")

    path = f"{service_path}/v1/completions"

    for model_id in available_models:
        logger.info("test_completions", f"Sending completion request to model '{model_id}' in service '{service}' with prompt 'message test'.")
        payload = build_legacy_completion_payload(
            "message test", model_id, config["temperature"], config["max_tokens"]
        )
        success, response, error = api_client.post(path, payload)

        assert success, f"[/completions] Failed for model '{model_id}' in service '{service}'. Error: {error}"
        assert response and response.get("choices"), f"[/completions] No 'choices' in response for model '{model_id}'."
        assert response.get("choices")[0].get("text"), f"[/completions] Empty response text for model '{model_id}'."

def test_embeddings(api_client: ApiClient, config: dict, service: str, available_models: list[str]):
    """
    Tests the /embeddings endpoint for a given service and its available models.
    """
    if service == "embed":
        pytest.skip("Skipping generic embeddings test for 'embed' service; covered by specific test.")

    service_path = config["service_prefixes"][service]

    if service == "ollama":
        path = f"{service_path}/api/embed"
    else:
        path = f"{service_path}/v1/embeddings"

    logger.info("ROUTE", f"{'-' * 80}")
    logger.info("ROUTE", f"Testing route: {path}")
    logger.info("ROUTE", f"{'-' * 80}")

    for model_id in available_models:
        logger.info("test_embeddings", f"Sending embedding request for model '{model_id}' in service '{service}' with input 'This is a test sentence.'.")
        payload = build_embedding_payload(model_id, "This is a test sentence.")
        success, response, error = api_client.post(path, payload)
        
        # We don't assert success here because many models are expected to fail
        if not success:
            logger.warning("EMBED_TEST", f"Embedding request failed for model '{model_id}' as expected. Error: {error}")
        elif response and "data" in response and isinstance(response["data"], list) and response["data"]:
            logger.info("EMBED_TEST", f"Successfully received embedding for model '{model_id}'.")
            assert isinstance(response["data"][0].get("embedding"), list), f"Embedding for '{model_id}' is not a list."
        elif service == "ollama" and response and "embeddings" in response:
            logger.info("EMBED_TEST", f"Successfully received embedding for model '{model_id}' (Ollama).")
            assert isinstance(response["embeddings"], list), f"Ollama embedding for '{model_id}' is not a list."
        else:
            logger.warning("EMBED_TEST", f"Embedding request for model '{model_id}' succeeded but response is empty or invalid.", {"response": response})

def test_ollama_generate(api_client: ApiClient, config: dict, service: str, available_models: list[str]):
    """
    Tests the /api/generate endpoint specifically for the ollama service.
    """
    if service != "ollama":
        pytest.skip("This test is only for the ollama service.")

    service_path = config["service_prefixes"]["ollama"]
    path = f"{service_path}/api/generate"

    logger.info("ROUTE", f"{'-' * 80}")
    logger.info("ROUTE", f"Testing route: {path}")
    logger.info("ROUTE", f"{'-' * 80}")

    for model_id in available_models:
        logger.info("test_ollama_generate", f"Sending generate request to model '{model_id}' in service 'ollama' with prompt 'message test'.")
        payload = {"model": model_id, "prompt": "message test"}
        success, response, error = api_client.post(path, payload)
        assert success, f"[/api/generate] Failed for model '{model_id}'. Error: {error}"
        assert response and response.get("response"), f"[/api/generate] No 'response' in response for model '{model_id}'."
        assert response.get("response"), f"[/api/generate] Empty response for model '{model_id}'."

def test_embed_embeddings(api_client: ApiClient, config: dict, service: str, available_models: list[str]):
    """
    Tests the /embed/v1/embeddings endpoint specifically for the embed service.
    """
    if service != "embed":
        pytest.skip("This test is only for the embed service.")

    service_path = config["service_prefixes"]["embed"]
    path = f"{service_path}/v1/embeddings"

    logger.info("ROUTE", f"{'-' * 80}")
    logger.info("ROUTE", f"Testing route: {path}")
    logger.info("ROUTE", f"{'-' * 80}")

    for model_id in available_models:
        logger.info("test_embed_embeddings", f"Sending embedding request to model '{model_id}' in service 'embed' with input 'message test'.")
        payload = build_embedding_payload(model_id, "message test")
        success, response, error = api_client.post(path, payload)
        assert success, f"[/embeddings] Failed for model '{model_id}' in service 'embed'. Error: {error}"
        assert response and response.get("data"), f"[/embeddings] No 'data' in response for model '{model_id}'."
        assert isinstance(response["data"], list) and response["data"], f"[/embeddings] Empty 'data' array for model '{model_id}'."
        assert response["data"][0].get("embedding"), f"[/embeddings] No 'embedding' in response data for model '{model_id}'."
        assert isinstance(response["data"][0]["embedding"], list), f"[/embeddings] Embedding is not a list for model '{model_id}'."
