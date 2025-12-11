from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

from utils.logger import logger


def generate_token(base_url: str, verify_ssl: bool, email: str | None, password: str | None) -> str | None:
    """
    Generates a JWT token for authentication.
    """
    if not email or not password:
        logger.warning("TOKEN_GENERATION", f"Missing credentials: email={email is not None}, password={password is not None}")
        return None
    url = f"{base_url}/api/v1/auths/signin"
    payload = {
        "email": email,
        "password": password,
    }
    try:
        logger.info("TOKEN_GENERATION", f"Attempting to generate token for: {email}")
        response = requests.post(url, json=payload, verify=verify_ssl)
        response.raise_for_status()
        token = response.json().get("token")
        logger.info("TOKEN_GENERATION", "Token generated successfully")
        return token
    except requests.exceptions.RequestException as e:
        logger.error("TOKEN_GENERATION", f"Failed to generate token: {e}")
        return None


class ApiClient:
    """A client for interacting with the LLM API."""

    def __init__(self, base_url: str, token: str, timeout: int, verify_ssl: bool):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        self.timeout = timeout
        self.verify_ssl = verify_ssl

    def get(self, endpoint: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Sends a GET request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the request to.

        Returns:
            A tuple containing a boolean indicating success, the response data, and an error message.
        """
        url = f"{self.base_url}{endpoint}"
        logger.info("REQUEST_SEPARATOR", "----------------------------------------")
        logger.info("REQUEST", f"Sending GET request to {url}")
        return self._send_request("GET", url)

    def post(self, endpoint: str, payload: Dict[str, Any]) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Sends a POST request to the specified endpoint.

        Args:
            endpoint: The API endpoint to send the request to.
            payload: The payload to send with the request.

        Returns:
            A tuple containing a boolean indicating success, the response data, and an error message.
        """
        url = f"{self.base_url}{endpoint}"
        logger.info("REQUEST_SEPARATOR", "----------------------------------------")
        logger.info("REQUEST", f"Sending POST request to {url}", {"payload": payload})
        return self._send_request("POST", url, payload)

    def _send_request(
        self,
        method: str,
        url: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Sends a request to the specified endpoint.

        Args:
            method: The HTTP method to use (GET or POST).
            url: The URL to send the request to.
            payload: The payload to send with the request.

        Returns:
            A tuple containing a boolean indicating success, the response data, and an error message.
        """
        try:
            if method == "GET":
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )
            else:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl,
                )
            response.raise_for_status()
            response_data = response.json()
            logger.info(
                "RESPONSE",
                "Request successful",
                {"status_code": response.status_code, "response": response_data},
            )
            return True, response_data, None
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after {self.timeout} seconds"
            logger.error("TIMEOUT", error_msg, {"endpoint": url})
            return False, None, error_msg
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("CONNECTION", error_msg, {"endpoint": url})
            return False, None, error_msg
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error: {e.response.status_code}"
            response_text = e.response.text
            logger.error(
                "HTTP_ERROR",
                error_msg,
                {
                    "endpoint": url,
                    "status_code": e.response.status_code,
                    "response_text": response_text,
                },
            )
            return False, None, error_msg
        except json.JSONDecodeError:
            error_msg = "Invalid JSON response"
            logger.error(
                "JSON_ERROR",
                error_msg,
                {"endpoint": url, "response_text": response.text if "response" in locals() else None},
            )
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error("UNKNOWN_ERROR", error_msg, {"endpoint": url})
            return False, None, error_msg
