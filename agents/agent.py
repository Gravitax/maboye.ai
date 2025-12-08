"""
Base Agent class for LLM-powered agents

Provides core functionality for agent workflow: input processing,
LLM querying, and output generation.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from srcs.logger import logger
from LLM import LLM
from agents.config import AgentConfig
from agents.types import AgentInput, AgentOutput, Message


class AgentError(Exception):
    """Base exception for agent errors"""
    pass


class AgentInputError(AgentError):
    """Input validation errors"""
    pass


class AgentOutputError(AgentError):
    """Output processing errors"""
    pass


class Agent:
    """
    Base agent class for LLM-powered workflows

    Implements standard agent pattern: receive input, process with LLM,
    return output. Designed to be extended for specific use cases.
    """

    def __init__(
        self,
        llm: LLM,
        config: Optional[AgentConfig] = None
    ):
        """
        Initialize agent

        Args:
            llm: LLM instance for API calls
            config: Agent configuration (uses defaults if None)
        """
        self._llm = llm
        self._config = config or AgentConfig()
        self._input: Optional[AgentInput] = None
        self._output: Optional[AgentOutput] = None
        self._execution_count = 0

    def set_input(self, input_data: Union[str, Dict[str, Any], AgentInput]):
        """
        Set agent input

        Args:
            input_data: Input as string, dict, or AgentInput

        Raises:
            AgentInputError: Invalid input
        """
        if isinstance(input_data, str):
            agent_input = AgentInput(prompt=input_data)
        elif isinstance(input_data, dict):
            agent_input = AgentInput(**input_data)
        elif isinstance(input_data, AgentInput):
            agent_input = input_data
        else:
            raise AgentInputError(f"Invalid input type: {type(input_data)}")

        self._validate_input(agent_input)
        self._input = agent_input

        if self._config.enable_logging:
            logger.info("AGENT", "Input set", {
                "name": self._config.name,
                "prompt_length": len(agent_input.prompt)
            })

    def get_input(self) -> Optional[AgentInput]:
        """
        Get current input

        Returns:
            Current input or None
        """
        return self._input

    def _validate_input(self, input_data: AgentInput):
        """
        Validate input data

        Args:
            input_data: Input to validate

        Raises:
            AgentInputError: Validation failed
        """
        if not input_data.prompt:
            raise AgentInputError("Prompt cannot be empty")

        if len(input_data.prompt) > self._config.max_input_length:
            raise AgentInputError(
                f"Prompt exceeds max length: {len(input_data.prompt)} > {self._config.max_input_length}"
            )

    def query_llm(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Query LLM with current input

        Args:
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional LLM parameters

        Returns:
            LLM response text

        Raises:
            AgentError: No input set or LLM query failed
        """
        if not self._input:
            raise AgentError("No input set for LLM query")

        self._execution_count += 1

        messages = self._build_messages()

        if self._config.enable_logging:
            logger.info("AGENT", "Querying LLM", {
                "name": self._config.name,
                "execution": self._execution_count,
                "messages_count": len(messages)
            })

        try:
            response = self._llm.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            response_text = response.choices[0].message.content

            return response_text

        except Exception as e:
            logger.error("AGENT", "LLM query failed", {
                "name": self._config.name,
                "error": str(e)
            })
            raise AgentError(f"LLM query failed: {e}")

    def _build_messages(self) -> List[Message]:
        """
        Build message list for LLM

        Returns:
            List of messages including system prompt and user input
        """
        messages = []

        if self._config.system_prompt:
            messages.append(Message(
                role="system",
                content=self._config.system_prompt
            ))

        if self._input.context:
            context_text = self._format_context(self._input.context)
            messages.append(Message(
                role="system",
                content=f"Context:\n{context_text}"
            ))

        messages.append(Message(
            role="user",
            content=self._input.prompt
        ))

        return messages

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context dictionary as text

        Args:
            context: Context data

        Returns:
            Formatted context string
        """
        lines = []
        for key, value in context.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def set_output(self, response: str, success: bool = True, error: Optional[str] = None):
        """
        Set agent output

        Args:
            response: Response text
            success: Whether operation succeeded
            error: Error message if failed
        """
        metadata = {
            "execution_count": self._execution_count,
            "timestamp": datetime.now().isoformat()
        }

        if self._input and self._input.metadata:
            metadata.update(self._input.metadata)

        self._output = AgentOutput(
            response=response,
            metadata=metadata,
            success=success,
            error=error
        )

        self._validate_output(self._output)

        if self._config.enable_logging:
            logger.info("AGENT", "Output set", {
                "name": self._config.name,
                "success": success,
                "response_length": len(response)
            })

    def get_output(self) -> Optional[AgentOutput]:
        """
        Get current output

        Returns:
            Current output or None
        """
        return self._output

    def _validate_output(self, output: AgentOutput):
        """
        Validate output data

        Args:
            output: Output to validate

        Raises:
            AgentOutputError: Validation failed
        """
        if not output.response:
            raise AgentOutputError("Response cannot be empty")

        if len(output.response) > self._config.max_output_length:
            raise AgentOutputError(
                f"Response exceeds max length: {len(output.response)} > {self._config.max_output_length}"
            )
