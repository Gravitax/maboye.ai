# Agents Module

This directory contains the core components for defining and managing agents.
It separates the agent's logic from its specific configuration profiles.

## File Structure

- `agent.py`: Defines the primary `Agent` class.
This class orchestrates the agent's lifecycle, including initialization, processing user input, and coordinating with the LLM and available tools.

- `types.py`: Contains custom data types and Pydantic models specific to the agents, ensuring data consistency and validation.

- `profiles/`: A subdirectory holding JSON files that define the configurations for different agent types (e.g., `code_agent`, `bash_agent`).
