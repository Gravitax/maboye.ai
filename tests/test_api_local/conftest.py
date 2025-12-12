from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest

from utils.config import load_configuration
from utils.api_client import ApiClient, generate_token
from utils.logger import logger, reconfigure_logger


def pytest_configure(config):
    """
    Called before test run starts.
    Forces logger reinitialization to create a new log file.
    """
    reconfigure_logger()


@pytest.fixture(scope="session")
def config():
    """
    Loads the configuration from environment variables.
    """
    cfg = load_configuration()
    setup_ssl_verification(cfg)
    return cfg

@pytest.fixture(scope="session")
def api_client(config):
    """
    Creates an API client with token authentication (with fallback to API key).
    """
    token = generate_token(
        config["base_url"],
        config["verify_ssl"],
        config["api_email"],
        config["api_password"],
    )
    if not token:
        logger.warning("TOKEN_GENERATION", "Failed to generate token, falling back to API key.")
        token = config.get("api_key")

    return ApiClient(
        base_url=config["base_url"],
        token=token,
        timeout=config["request_timeout"],
        verify_ssl=config["verify_ssl"],
    )



@pytest.fixture(scope="session")
def test_message():
    """Default test message for chat completion tests."""
    return "Hello, this is a test message."

def setup_ssl_verification(config):
    """
    Disables SSL warnings if SSL verification is disabled.
    """
    if not config['verify_ssl']:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        logger.warning("SSL", "SSL verification disabled")
