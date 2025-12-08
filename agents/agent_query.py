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

    def process_input(
        self,
        query: str
    ) -> str:
        """
        Full query reformatting pipeline

        Args:
            query: Raw query string

        Returns:
            todo
        """
        if not self.validate_query(query):
            logger.error("AGENT_QUERY", "Invalid query", {
                "query": query[:50]
            })
            return ""

        # Sanitize
        processed = self.sanitize_query(query)

        # Normalize
        processed = self.normalize_query(processed)

        # todo : identifier le type de query + return un json avec un format de data

        return processed

    def run(self, query: str) -> Any:
        """
        Run query processing

        Args:
            query: Raw query string

        Returns:
            todo
        """

        query_metadata = self.process_input(query)

        return query_metadata
