# LLM Wrapper Module

This module provides an abstraction layer for interacting with Large Language Models (LLMs).
It encapsulates the specifics of different LLM providers, offering a unified interface for the rest of the application.

## File Structure

- `config.py`: Contains configuration settings and parameters related to LLM access and behavior.

- `types.py`: Defines custom data types, enums, and Pydantic models used specifically for LLM interactions and responses.

- `llm_wrapper.py`: Implements the core logic for communicating with and processing responses from Large Language Models.
