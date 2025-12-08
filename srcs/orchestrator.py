"""
Orchestrator for managing agent workflows

Coordinates multiple agents to process user queries through a complete pipeline:
1. Query reformatting
2. Context building
3. LLM processing
4. Code execution
5. Memory storage
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from srcs.logger import logger
from srcs.memory import MemoryManager, MemoryType
from agents.agent_query import AgentQuery
from agents.agent_context import AgentContext
from agents.agent_code import AgentCode
from agents.config import AgentConfig
from agents.types import AgentInput, AgentOutput, Message
from LLM import LLM


class OrchestratorOutput:
    """Output from orchestrator execution"""

    def __init__(
        self,
        success: bool,
        response: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize orchestrator output

        Args:
            success: Whether execution was successful
            response: Response string
            error: Error message if failed
            metadata: Additional metadata
        """
        self.success = success
        self.response = response
        self.error = error
        self.metadata = metadata or {}


class Orchestrator:
    """
    Agent orchestrator

    Manages the complete workflow for processing user queries:
    - Reformats queries using AgentQueries
    - Builds context using AgentContext with memory
    - Processes through LLM
    - Executes code operations using AgentCode
    - Stores everything in memory
    """

    def __init__(
        self,
        llm: LLM,
        memory_manager: Optional[MemoryManager] = None,
        enable_logging: bool = True
    ):
        """
        Initialize orchestrator

        Args:
            llm: LLM instance for agent processing
            memory_manager: Memory manager (creates new if None)
            enable_logging: Enable detailed logging
        """
        self._llm = llm
        self._memory_manager = memory_manager or MemoryManager()
        self._enable_logging = enable_logging
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Initialize agents
        self._agent_query = AgentQuery(
            llm=None,
            config=AgentConfig(
                name="QueryAgent",
                enable_logging=enable_logging
            )
        )

        self._agent_context = AgentContext(
            llm=self._llm,
            config=AgentConfig(
                name="ContextAgent",
                enable_logging=enable_logging
            ),
            memory_manager=self._memory_manager
        )

        self._agent_code = AgentCode(
            llm=self._llm,
            config=AgentConfig(
                name="CodeAgent",
                enable_logging=enable_logging
            )
        )

        if self._enable_logging:
            logger.info("ORCHESTRATOR", "Orchestrator initialized", {
                "session_id": self._session_id
            })

    def process_query(
        self,
        query_user: str
    ) -> OrchestratorOutput:
        """
        Process user query through complete pipeline

        Args:
            query_user: Raw user query

        Returns:
            OrchestratorOutput with results
        """
        try:
            if self._enable_logging:
                logger.separator("Query Processing Started")
                logger.info("ORCHESTRATOR", "Processing query", {
                    "session_id": self._session_id,
                    "query": query_user,
                    "query_length": len(query_user)
                })

            # Step 1: Reformat query
            if self._enable_logging:
                logger.info("ORCHESTRATOR", "Step 1: Reformat query")
            # todo: definir le contexte afin d'obtenir un type de query et une liste de steps pour effectuer cette query
            output = self._agent_query.run(AgentInput(prompt=query_user))
            query_reformatted = output.response
            query_type = output.metadata["type"]
            query_steps = output.metadata["steps"]

            if self._enable_logging:
                logger.info("ORCHESTRATOR", {
                    "query_reformatted": query_reformatted,
                    "type": query_type,
                    "steps": query_steps
                })

            # Check if query is valid after reformatting
            if not query_reformatted or not query_reformatted.strip():
                return OrchestratorOutput(
                    success=False,
                    error="Query is empty or invalid. Please provide a valid message."
                )

            # todo: celon le query type on appel tel ou tel agent
            # todo definir une enum type (question general, faire du code, traiter des commandes shell, analyser un document, etc...)
            # todo: stocker la memoire sous le format: { memoryType, enumType, id, rawString, embedString }

            # Step 2: Build context
            if self._enable_logging:
                logger.info("ORCHESTRATOR", "Step 2: Build context")
            # todo: definir le contexte afin recuperer la memoire en rapport avec la query, son type et ses steps
            # peu-etre associer des mots clefs au type pour faire une comparaison vectorielle avec les chunks de memoire
            output = self._agent_context.run(AgentInput(prompt=query_reformatted))
            context = output.response

            # Step 3: Query LLM
            if self._enable_logging:
                logger.info("ORCHESTRATOR", "Step 3: Querying LLM")

            # todo: 
            # Build messages for LLM
            messages = [
                Message(role="system", content="You are a helpful AI assistant."),
                Message(role="user", content=query_reformatted)
            ]
            response = self._llm.chat_completion(messages)
            llm_response = response.choices[0].message.content

            # Step 4: Store in memory
            if self._enable_logging:
                logger.info("ORCHESTRATOR", "Step 4: Storing in memory")
            self._store_in_memory(
                query_user,
                query_reformatted,
                context
            )

            # Create output
            output = OrchestratorOutput(
                success=True,
                response=llm_response,
                metadata={
                    "query_reformatted": query_reformatted,
                    "session_id": self._session_id
                }
            )

            if self._enable_logging:
                logger.info("ORCHESTRATOR", "Query processed successfully")
                logger.separator("Query Processing Complete")

            return output

        except Exception as e:
            if self._enable_logging:
                logger.error("ORCHESTRATOR", "Query processing failed", {
                    "error": str(e),
                    "session_id": self._session_id
                })

            return OrchestratorOutput(
                success=False,
                error=str(e)
            )

    def _store_in_memory(
        self,
        original_query: str,
        query_reformatted: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Store all data in memory

        Args:
            original_query: Original user query
            query_reformatted: Reformatted query
            context: Context used
            llm_response: LLM response
        """

        # Store query
        self._memory_manager.set(
            MemoryType.QUERIES,
            original_query,
            metadata={
                "session_id": self._session_id,
                "reformatted": query_reformatted
            }
        )

        # Store context
        self._memory_manager.set(
            MemoryType.CONTEXTS,
            context,
            metadata={"session_id": self._session_id}
        )

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics

        Returns:
            Memory statistics
        """
        return self._memory_manager.get_stats()

    def clear_memory(self) -> None:
        """Clear all memory"""
        self._memory_manager.clear_all()

        if self._enable_logging:
            logger.info("ORCHESTRATOR", "Memory cleared")

    def get_session_id(self) -> str:
        """
        Get current session ID

        Returns:
            Session ID
        """
        return self._session_id

    def get_query_history(self, count: int = 10) -> List[str]:
        """
        Get query history

        Args:
            count: Number of queries to retrieve

        Returns:
            List of queries
        """
        query_memory = self._memory_manager.get(MemoryType.QUERIES)
        entries = query_memory.get_last(count)
        return [entry["data"] for entry in entries]

    def reset(self) -> None:
        """Reset orchestrator state"""
        self.clear_memory()
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self._enable_logging:
            logger.info("ORCHESTRATOR", "Orchestrator reset", {
                "new_session_id": self._session_id
            })
