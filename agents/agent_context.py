"""
Context Agent for building LLM context

Handles context assembly using memory and query information
to create structured context for LLM processing.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from srcs.logger import logger
from srcs.memory import MemoryManager, MemoryType
from agents.agent import Agent
from agents.config import AgentConfig
from agents.types import AgentInput, AgentOutput
from LLM import LLM


class AgentContext(Agent):
    """
    Context building agent

    """

    def __init__(
        self,
        llm: Optional[LLM] = None,
        config: Optional[AgentConfig] = None,
        memory_manager: Optional[MemoryManager] = None
    ):
        """
        Initialize context agent

        Args:
            llm: LLM instance (optional)
            config: Agent configuration (uses defaults if None)
            memory_manager: Memory manager instance (creates new if None)
        """
        if config is None:
            config = AgentConfig(
                name="ContextAgent",
                system_prompt="You are a context building assistant.",
                enable_logging=True
            )

        super().__init__(llm, config)

        self._memory_manager = memory_manager or MemoryManager()

        if self._config.enable_logging:
            logger.info("AGENT_CONTEXT", "Context agent initialized", {
                "name": self._config.name
            })

    # def get_query_history(self, count: int = 5) -> List[str]:
    #     query_memory = self._memory_manager.get(MemoryType.QUERIES)
    #     entries = query_memory.get_last(count)
    #     return [entry["data"] for entry in entries]

    def run(self, input: AgentInput) -> AgentOutput:
        """
        run context building

        Args:
            input: AgentInput

        Returns:
            AgentOutput
        """

        # self.set_input(query)
        # response = self.query_llm()

        context = input.prompt
    
        self.set_output(response=context)
        return self.get_output()
