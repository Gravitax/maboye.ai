from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add parent directory to path for logger import
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from core.logger import logger


def main():
    """
    Main entry point for the test script.
    Runs the complete test suite using pytest.
    """
    try:
        # Disable SSL warnings for self-signed certificates
        from test_api_local.utils.config import load_configuration
        config = load_configuration()
        if not config['verify_ssl']:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning("SSL", "SSL verification disabled")

        logger.separator("Starting API Test Suite")
        logger.info("TEST_SUITE", "Running complete test battery")

        # Get the test directory path
        test_dir = Path(__file__).parent

        # Run pytest with the test directory
        # -v: verbose output
        # -s: show print statements
        # --tb=short: shorter traceback format
        exit_code = pytest.main([
            str(test_dir),
            "-v",
            "-s",
            "--tb=short",
            "--color=yes"
        ])

        if exit_code == 0:
            logger.info("TEST_SUITE", "All tests passed successfully")
        else:
            logger.error("TEST_SUITE", f"Tests failed with exit code: {exit_code}")

        logger.separator("Test Suite Complete")
        return exit_code

    except KeyboardInterrupt:
        logger.warning("INTERRUPT", "Tests interrupted by user")
        return 130

    except Exception as e:
        logger.critical("FATAL", "Unexpected error in main", {"error": str(e)})
        return 1


if __name__ == "__main__":
    sys.exit(main())
