"""
Base Agent class for LLM-powered agents

Provides core functionality for agent workflow: input processing,
LLM querying, and output generation.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.logger import logger
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
        self._history: List[Dict[str, Any]] = []
        self._execution_count = 0

        if self._config.enable_logging:
            logger.info("AGENT", "Agent initialized", {
                "name": self._config.name,
                "max_history": self._config.max_history
            })

    def set_llm(self, llm: LLM):
        """
        Set LLM instance

        Args:
            llm: New LLM instance
        """
        if not isinstance(llm, LLM):
            raise TypeError("llm must be instance of LLM")

        self._llm = llm

        if self._config.enable_logging:
            logger.info("AGENT", "LLM instance updated", {"name": self._config.name})

    def get_llm(self) -> LLM:
        """
        Get current LLM instance

        Returns:
            Current LLM instance
        """
        return self._llm

    def set_input(self, input_data: str | Dict[str, Any] | AgentInput):
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

        if self._config.validate_inputs:
            self._validate_input(agent_input)

        self._input = agent_input

        if self._config.enable_logging and self._config.log_inputs:
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

    def modify_input(
        self,
        prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Modify current input

        Args:
            prompt: New prompt (keeps existing if None)
            context: New context (keeps existing if None)
            metadata: New metadata (keeps existing if None)

        Raises:
            AgentError: No input set
        """
        if not self._input:
            raise AgentError("No input set to modify")

        if prompt is not None:
            self._input.prompt = prompt

        if context is not None:
            self._input.context = context

        if metadata is not None:
            self._input.metadata = metadata

        if self._config.validate_inputs:
            self._validate_input(self._input)

        if self._config.enable_logging:
            logger.debug("AGENT", "Input modified", {"name": self._config.name})

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

            self._add_to_history({
                "timestamp": datetime.now().isoformat(),
                "execution": self._execution_count,
                "input": self._input.prompt,
                "response": response_text,
                "tokens": response.usage.total_tokens
            })

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

    def get_last_llm_response(self) -> Optional[str]:
        """
        Get last response from LLM

        Returns:
            Last response text or None
        """
        if not self._history:
            return None

        return self._history[-1].get("response")

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

        if self._config.validate_outputs:
            self._validate_output(self._output)

        if self._config.enable_logging and self._config.log_outputs:
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

    def run(
        self,
        input_data: str | Dict[str, Any] | AgentInput,
        **llm_kwargs
    ) -> AgentOutput:
        """
        Execute complete agent workflow

        Args:
            input_data: Agent input
            **llm_kwargs: Additional LLM parameters

        Returns:
            Agent output

        Raises:
            AgentError: Execution failed
        """
        try:
            self.set_input(input_data)
            response = self.query_llm(**llm_kwargs)
            self.set_output(response, success=True)
            return self._output

        except Exception as e:
            error_msg = str(e)
            self.set_output(
                response="",
                success=False,
                error=error_msg
            )

            if self._config.enable_logging:
                logger.error("AGENT", "Execution failed", {
                    "name": self._config.name,
                    "error": error_msg
                })

            raise AgentError(f"Agent execution failed: {e}")

    def _add_to_history(self, entry: Dict[str, Any]):
        """
        Add entry to execution history

        Args:
            entry: History entry
        """
        self._history.append(entry)

        if len(self._history) > self._config.max_history:
            self._history.pop(0)

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get execution history

        Returns:
            List of history entries
        """
        return self._history.copy()

    def clear_history(self):
        """Clear execution history"""
        self._history.clear()

        if self._config.enable_logging:
            logger.debug("AGENT", "History cleared", {"name": self._config.name})

    def reset(self):
        """Reset agent state"""
        self._input = None
        self._output = None
        self._history.clear()
        self._execution_count = 0

        if self._config.enable_logging:
            logger.info("AGENT", "Agent reset", {"name": self._config.name})

    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics

        Returns:
            Statistics dictionary
        """
        return {
            "name": self._config.name,
            "executions": self._execution_count,
            "history_size": len(self._history),
            "has_input": self._input is not None,
            "has_output": self._output is not None,
            "llm_requests": self._llm.get_request_count()
        }
