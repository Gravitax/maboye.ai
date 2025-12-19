"""
Orchestrator for managing agent workflows.

This module centralizes the setup and coordination of all core components:
LLM wrapper, Memory Manager, Tool Scheduler, Prompt Builder, and the Agent itself.
It provides a clean interface for the main application loop to interact with the agent system.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from core.logger import logger
from core.llm_wrapper import LLMWrapper, LLMWrapperConfig
from core.tool_scheduler import ToolScheduler
from tools.tool_base import get_registry
from tools.implementations import register_all_tools
from agents.types import AgentOutput
from core.repositories import InMemoryMemoryRepository, InMemoryAgentRepository
from core.services import MemoryManager, LRUCache, AgentFactory
from core.services.tasks_manager import TasksManager
from core.services.memory_formatter import MemoryFormatter
from core.services.context_manager import ContextManager

class Orchestrator:
    """
    Central coordinator for the multi-agent system.
    """

    def __init__(self, llm_config: Optional[LLMWrapperConfig] = None):
        """
        Initialize the orchestrator with all components.

        Args:
            llm_config: Configuration for the LLM wrapper
        """
        self._llm_config = llm_config or LLMWrapperConfig()
        self._setup_components()

    def _setup_components(self) -> None:
        """Setup all orchestrator components in correct order."""

        # Initialize repositories
        self._memory_repository = InMemoryMemoryRepository()
        self._agent_repository = InMemoryAgentRepository()

        # Initialize memory coordinator with LRU cache
        cache_strategy = LRUCache(max_size=100)
        self._memory_manager = MemoryManager(
            memory_repository=self._memory_repository,
            cache_strategy=cache_strategy
        )
        # Initialize memory formatter
        self._memory_formatter = MemoryFormatter(self._memory_repository)

        # Register tools
        register_all_tools()
        self._tool_registry = get_registry()
        # Initialize tool scheduler
        self._tool_scheduler = ToolScheduler(registry=self._tool_registry)

        # Initialize LLM wrapper
        self._llm = LLMWrapper(self._llm_config)
        # Initialize context manager
        self._context_manager = ContextManager(self._memory_repository)

        # Initialize agent factory for creating specialized agents
        self._agent_factory = AgentFactory(
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            tool_registry=self._tool_registry,
            memory=self._memory_manager
        )
        # Initialize tasks manager
        self._tasks_manager = TasksManager(
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            tool_registry=self._tool_registry,
            memory_manager=self._memory_manager,
            context_manager=self._context_manager,
            agent_factory=self._agent_factory,
            agent_repository=self._agent_repository
        )

        # Tasks agent will be created lazily when first needed
        self._tasks_agent = None

    def get_agent_repository(self) -> InMemoryAgentRepository:
        """Get the agent repository."""
        return self._agent_repository

    def get_memory_manager(self) -> MemoryManager:
        """Get the memory coordinator."""
        return self._memory_manager

    def get_tool_info(self) -> list:
        """
        Get information about all registered tools.

        Returns:
            List of tool info dictionaries
        """
        return self._tool_registry.get_all_tools_info()

    def _save_orchestrator_output(self, result: AgentOutput, conversation_id: str = None) -> None:
        """
        Save orchestrator output to memory.

        Args:
            result: AgentOutput with orchestrator response
            conversation_id: ID of the conversation
        """
        metadata = result.metadata
        if conversation_id:
            metadata["conversation_id"] = conversation_id

        self._memory_manager.save_conversation_turn(
            agent_id="orchestrator",
            role="assistant",
            content=result.response,
            metadata=metadata
        )

    def _ensure_tasks_agent_initialized(self):
        """Ensure tasks agent is initialized (lazy initialization)."""
        if self._tasks_agent is None:
            registered_agent = self._agent_repository.find_by_name("TasksAgent")
            if registered_agent:
                self._tasks_agent = self._agent_factory.create_agent(registered_agent)
            else:
                raise ValueError("TasksAgent not found in repository. Ensure agents are registered before use.")

    def _get_tasks_list(self, user_prompt: str, system_prompt: str):
        import json

        self._ensure_tasks_agent_initialized()

        result = self._tasks_agent.run(
            task=user_prompt,
            system_prompt=system_prompt
        )
        tasks = {}
        if result.success == True:
            response = result.response.strip()
            if response:
                try:
                    tasks = json.loads(response)
                except json.JSONDecodeError as e:
                    tasks = {}
        return tasks

    def process_user_input(self, user_input: str) -> AgentOutput:
        """
        Process user input through autonomous workflow.

        Args:
            user_input: User input to process

        Returns:
            AgentOutput
        """
        # Generate unique conversation ID
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        # Save user input in orchestrator memory
        self._memory_manager.save_conversation_turn(
            agent_id="orchestrator",
            role="user",
            content=user_input,
            metadata={"conversation_id": conversation_id}
        )

        try:
            executing = True
            self._ensure_tasks_agent_initialized()

            # user_prompt = self._context_manager.format_context_as_string(
            #     agent_id="orchestrator",
            #     max_turns=6
            # )
            user_prompt = user_input            
            system_prompt = self._context_manager.get_taskslist_system_prompt()
            system_prompt += self._context_manager.get_available_tools_prompt(self._tasks_agent)

            while executing:
                try:
                    logger.info("ORCHESTRATOR", "---------- create tasks list start")
                    tasks = self._get_tasks_list(user_prompt, system_prompt)
                    logger.info("ORCHESTRATOR", "---------- create tasks list end")
                    logger.info("ORCHESTRATOR", "---------- tasks manager start")
                    result = self._tasks_manager.execute(user_prompt, tasks)
                    if result.success == False:
                        # todo: build prompt on resultat log to loop again with error context
                        user_prompt = ""
                        system_prompt = ""
                        executing = False
                        logger.info("ORCHESTRATOR", "tasks manager failed")
                    else:
                        executing = False
                    logger.info("ORCHESTRATOR", "---------- tasks manager end", { "success": result.success })
                    self._save_orchestrator_output(result, conversation_id)
                    return result
                except KeyboardInterrupt:
                    logger.warning("ORCHESTRATOR", "Orchestrator loop interrupted by user (Ctrl+C).")
                    executing = False # Stop the loop
                    self._memory_manager.save_conversation_turn(
                        agent_id="orchestrator",
                        role="assistant",
                        content="Orchestrator loop interrupted by user.",
                        metadata={"conversation_id": conversation_id, "status": "interrupted"}
                    )
                    return AgentOutput(
                        response="Orchestrator loop interrupted by user.",
                        success=False,
                        error="user_interrupted",
                        cmd="interrupted"
                    )

        except Exception as e:
            result = AgentOutput(
                response=f"Error executing: {e}",
                success=False,
                error=str(e)
            )
            # Save error output
            self._save_orchestrator_output(result, conversation_id)
            return result

    def get_memory_manager_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics formatted for the /memory command.

        Returns:
            Dictionary with conversation and agent stats
        """
        return {
            "conversation": self._memory_formatter.get_conversation_stats(),
            "agents": self._memory_formatter.get_agent_stats()
        }

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Alias for get_memory_manager_stats() for backward compatibility.

        Returns:
            Dictionary with conversation and agent stats
        """
        return self.get_memory_manager_stats()

    def reset_conversation(self) -> None:
        """Clear all conversation memory for active agents."""
        active_agents = self._agent_repository.find_active()

        for agent in active_agents:
            agent_id = agent.get_agent_id()
            self._memory_manager.clear_agent_memory(agent_id)

        # Also clear memory for orchestrator and mock agent
        self._memory_manager.clear_agent_memory("orchestrator")
        self._memory_manager.clear_agent_memory("mock_agent")

    def get_memory_manager_content(self, mem_type: str, agent_id: Optional[str] = None) -> list:
        """
        Get memory content for a specific type.

        Args:
            mem_type: Type of memory to retrieve ('conversation' or 'agents')
            agent_id: Optional. Specific agent ID to retrieve details for

        Returns:
            List of formatted strings ready for display
        """
        if mem_type == "conversation":
            return self._memory_formatter.format_conversations()
        elif mem_type == "agents":
            if agent_id:
                # Get detail for specific agent
                detail = self._memory_formatter.get_agent_detail(agent_id)
                return [detail] if detail else []
            else:
                # Get list of all agents
                return self._memory_formatter.format_agents()
        else:
            return []

    def get_memory_content(self, mem_type: str, agent_id: Optional[str] = None) -> list:
        """
        Alias for get_memory_manager_content() for backward compatibility.

        Args:
            mem_type: Type of memory to retrieve ('conversation' or 'agents')
            agent_id: Optional. Specific agent ID to retrieve details for

        Returns:
            List of formatted strings ready for display
        """
        return self.get_memory_manager_content(mem_type, agent_id)
