"""
Query Agent for reformatting and processing user queries

Handles query normalization, enhancement, and preparation
before sending to the LLM for processing.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from srcs.logger import logger
from agents.agent import Agent
from agents.config import AgentConfig
from agents.types import AgentInput, AgentOutput
from LLM import LLM


class AgentQuery(Agent):
    """
    Query processing agent

    """

    def __init__(
        self,
        llm: Optional[LLM] = None,
        config: Optional[AgentConfig] = None
    ):
        """
        Initialize query agent

        Args:
            llm: LLM instance (optional, not always needed for simple reformatting)
            config: Agent configuration (uses defaults if None)
        """
        if config is None:
            config = AgentConfig(
                name="QueryAgent",
                system_prompt="You are a query reformatting assistant.",
                enable_logging=True
            )

        super().__init__(llm, config)

        if self._config.enable_logging:
            logger.info("AGENT_QUERY", "Query agent initialized", {
                "name": self._config.name
            })

    def normalize_query(self, query: str) -> str:
        """
        Normalize query formatting

        Args:
            query: Raw query string

        Returns:
            Normalized query string
        """
        if not query:
            return ""

        # Strip leading/trailing whitespace
        normalized = query.strip()

        # Normalize internal whitespace
        normalized = " ".join(normalized.split())

        # Ensure query ends with appropriate punctuation
        if normalized and not normalized[-1] in ".!?":
            normalized += "."

        return normalized

    def sanitize_query(self, query: str) -> str:
        """
        Sanitize query for safe processing

        Args:
            query: Query string

        Returns:
            Sanitized query string
        """
        # Remove potentially dangerous characters
        # Keep alphanumeric, spaces, and common punctuation
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            " .,!?;:'-\"()[]{}/@#$%&*+=\n\t"
        )

        sanitized = "".join(c for c in query if c in allowed_chars)

        return sanitized

    def validate_query(self, query: str) -> bool:
        """
        Validate query meets basic requirements

        Args:
            query: Query string

        Returns:
            True if query is valid
        """
        if not query or not query.strip():
            logger.warning("AGENT_QUERY", "Empty query received")
            return False

        # Check if query is too short after stripping
        cleaned = query.strip()
        if len(cleaned) < 2:
            logger.warning("AGENT_QUERY", "Query too short", {
                "length": len(cleaned)
            })
            return False

        if len(query) > 10000:
            logger.warning("AGENT_QUERY", "Query too long", {
                "length": len(query)
            })
            return False

        return True

    def clean_query(self, query: str) -> str:
        """
        A clean query pipeline

        Args:
            query: Raw query string

        Returns:
            A sanitized and normalized query
        """
        if not self.validate_query(query):
            return ""

        # Sanitize
        cleaned = self.sanitize_query(query)

        # Normalize
        cleaned = self.normalize_query(cleaned)

        return cleaned

    def run(self, input: AgentInput) -> AgentOutput:
        """
        Run query processing

        Args:
            input: AgentInput

        Returns:
            AgentOutput
        """

        query = input.prompt
        query_cleaned = self.clean_query(query)

        # todo : identifier le type de query + definir une liste d'etape a effectuer issues de la query
        self.set_output(response=query_cleaned, metadata={
            "type": "",
            "steps": ""
        })
        return self.get_output()
