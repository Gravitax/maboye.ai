from typing import Dict, Any, Tuple, List
from core.logger import logger
from core.services.state_manager import StateManager
from agents.types import AgentOutput


class ExecutionManager:
    """
    Executes autonomous workflow with dynamic todolist.

    The service manages a loop where:
    1. Get next pending step from StateManager
    2. Route step to appropriate specialized agent
    3. Agent executes with N iterations
    4. Result is used to update todolist dynamically
    5. Loop continues with updated todolist until complete

    Each agent has its own memory and can iterate multiple times
    to accomplish its assigned step.
    """

    def __init__(
        self,
        llm,
        tool_scheduler,
        tool_registry,
        memory_manager,
        context_manager,
        agent_factory=None,
        agent_repository=None
    ):
        """
        Initialize execution manager.

        Args:
            llm: LLM wrapper instance
            tool_scheduler: Tool scheduler instance
            tool_registry: Tool registry instance
            memory_manager: Memory coordinator instance
            context_manager: Context manager for building prompts
            agent_factory: (Optional) Factory for creating specialized agents
            agent_repository: (Optional) Repository with registered agents
        """
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._memory_manager = memory_manager
        self._context_manager = context_manager

        # AgentFactory for routing to specialized agents
        self._agent_factory = agent_factory
        self._agent_repository = agent_repository
    
    def _execute_direct(self, user_input: str, context: str = "") -> AgentOutput:
        """
        Execute user input directly without todolist (fallback mode).

        Args:
            user_input: User input to process

        Returns:
            AgentOutput from direct execution
        """

        registered_agent = self._agent_repository.find_by_name("DefaultAgent")
        agent = self._agent_factory.create_agent(registered_agent)
        # todo
        user_prompt=user_input
        system_prompt = "Answer base on history and user_query"

        result = agent.run(
            user_prompt=user_prompt,
            system_prompt=system_prompt
        )
        result.metadata={"called_agents":[{"agent_name": agent._identity.agent_name}]}
        return result

    def execute(
        self,
        user_input: str,
        context: str = "",
        max_iterations: int = 50
    ) -> Tuple[AgentOutput, List]:
        """
        Execute autonomous workflow with dynamic todolist.

        The workflow continues until either:
        - All steps are completed (success)
        - A step fails (error)
        - Max iterations reached (timeout)

        Args:
            user_input: User query to process
            context: Conversation context (recent history)
            max_iterations: Max workflow iterations to prevent infinite loops

        Returns:
            Tuple of AgentOutput with final result and list of called agents
        """
        registered_agent = self._agent_repository.find_by_name("TodoListAgent")
        agent = self._agent_factory.create_agent(registered_agent)

        # Create state manager
        state_manager = StateManager(context_manager=self._context_manager, agent=agent)

        # Initialize todolist
        success = state_manager.init_todolist(user_input, context)

        logger.info("EXECUTION_MANAGER", state_manager.display_todolist())

        if not success:
            return self._execute_direct(user_input, context)

        iteration = 0
        called_agents = []
        while not state_manager.is_complete() and iteration < max_iterations:
            iteration += 1

            next_step = state_manager.get_next_step()

            if next_step is None:
                break

            step_id = next_step.get("step_id", "unknown")

            result, called_agent = self._execute_step(step=next_step)
            called_agents.append(called_agent)

            if not result.success:
                return AgentOutput(
                    response=f"Execution failed at step {step_id}: {result.error}",
                    success=False,
                    error=f"step_{step_id}_failed",
                    agent_id="autonomous_workflow",
                    metadata={"called_agents":called_agents}
                )

            state_manager.update_from_result(step_id, result)
            logger.info("STEP_COMPLETE", f"{step_id}")

        if iteration >= max_iterations:
            return AgentOutput(
                response=f"Max iterations ({max_iterations}) reached without completion",
                success=False,
                error="max_iterations_reached",
                agent_id="autonomous_workflow",
                metadata={"called_agents": called_agents}
            )

        if not state_manager.is_complete():
            return AgentOutput(
                response="Workflow ended without completion",
                success=False,
                error="incomplete_workflow",
                agent_id="autonomous_workflow",
                metadata={"called_agents": called_agents}
            )

        return AgentOutput(
            response="Workflow ended with success",
            success=True,
            agent_id="autonomous_workflow",
            metadata={"called_agents": called_agents}
        )

    # ========== Agent Routing ==========
    # def _route_to_agent(self, description: str):
    #     """
    #     Route step to appropriate specialized agent based on description.
    #
    #     Examples:
    #         "commit changes" → GitAgent
    #         "list files in /tmp" → BashAgent
    #         "create python script" → PythonAgent
    #         "respond to user" → DefaultAgent
    #
    #     Args:
    #         description: Step description to analyze
    #
    #     Returns:
    #         RegisteredAgent instance for the task
    #     """
    #     description_lower = description.lower()
    #
    #     # Simple keyword-based routing (can be improved with embeddings/LLM)
    #     git_keywords = ['git', 'commit', 'branch', 'merge', 'push', 'pull', 'clone']
    #     bash_keywords = ['bash', 'shell', 'command', 'execute', 'run', 'ls', 'cd', 'mkdir']
    #     python_keywords = ['python', 'script', 'pip', 'virtualenv', '.py']
    #
    #     # Check keywords
    #     if any(keyword in description_lower for keyword in git_keywords):
    #         return self._agent_repository.find_by_name("GitAgent")
    #     elif any(keyword in description_lower for keyword in bash_keywords):
    #         return self._agent_repository.find_by_name("BashAgent")
    #     elif any(keyword in description_lower for keyword in python_keywords):
    #         return self._agent_repository.find_by_name("PythonAgent")
    #     else:
    #         # Default: use DefaultAgent for general tasks
    #         return self._agent_repository.find_by_name("DefaultAgent")
    # ========================================================================

    def _execute_step(
        self,
        step: Dict[str, Any]
    ) -> AgentOutput:
        """
        Execute single step with specialized agent.

        The agent:
        - Receives step description and context
        - Has access to findings from previous steps
        - Can decompose task into sub-commands
        - Executes with N iterations to complete the task
        - Can return todolist updates in its response

        Args:
            step: Step dictionary with step_id, description, etc.
            state_manager: StateManager for accessing findings
            called_agents: List to track called agents

        Returns:
            AgentOutput from agent execution
        """
        step_id = step.get("step_id", "unknown")
        description = step.get("description", "")
        logger.info("STEP_START", f"{step_id}: {description}")

        registered_agent = self._agent_repository.find_by_name("ExecAgent")
        agent = self._agent_factory.create_agent(registered_agent)

        system_prompt = self._context_manager.get_agent_system_prompt()
        system_prompt += "\n\n" + self._context_manager.get_available_tools_prompt(agent)

        result = agent.run(
            user_prompt=description,
            system_prompt=system_prompt
        )
        return result, {"agent_name": agent._identity.agent_name}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.

        Returns:
            Dictionary with service stats
        """
        return {
            "service_type": "execution_manager",
            "components": {
                "llm": str(type(self._llm).__name__),
                "tool_scheduler": str(type(self._tool_scheduler).__name__),
                "tool_registry": str(type(self._tool_registry).__name__),
                "memory": str(type(self._memory_manager).__name__)
            }
        }

    def __str__(self) -> str:
        """String representation for logging."""
        return "ExecutionManager(ready)"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"ExecutionManager("
            f"llm={type(self._llm).__name__}, "
            f"tool_scheduler={type(self._tool_scheduler).__name__})"
        )
