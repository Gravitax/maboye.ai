from typing import Dict, Any, Tuple, List
from core.logger import logger
from agents.types import AgentOutput


class TasksManager:
    """
    Executes autonomous workflow with dynamic todolist.

    Each agent called has its own memory and can iterate multiple times
    to accomplish its assigned step.
    """

    def __init__(
        self,
        llm,
        tool_scheduler,
        tool_registry,
        memory_manager,
        context_manager,
        agent_factory,
        agent_repository
    ):
        """
        Initialize execution manager.
        """
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._memory_manager = memory_manager
        self._context_manager = context_manager
        # AgentFactory for routing to specialized agents
        self._agent_factory = agent_factory
        self._agent_repository = agent_repository
    
    def _execute_direct(self, user_prompt: str) -> AgentOutput:
        """
        Execute user prompt directly with a default agent (fallback mode).

        Args:
            user_prompt: User prompt to process

        Returns:
            AgentOutput
        """

        logger.info("TASKS MANAGER", "direct execution")
        registered_agent = self._agent_repository.find_by_name("DefaultAgent")
        agent = self._agent_factory.create_agent(registered_agent)

        result = agent.run(task=user_prompt)
        result.metadata={"called_agents":[{"agent_name": agent._identity.agent_name}]}
        return result

    def execute(self, user_prompt: str, tasks: dict) -> AgentOutput:
        """
        Execute autonomous workflow

        Args:
            user_prompt: User input prompt
            tasks: {
                "analyse": "brief analyse of the user_input",
                "tasks": ["task1", "task2", ...]
            }

        Returns:
            AgentOutput
        """
        tasks_list = tasks.get("tasks", [])

        if not tasks_list or len(tasks_list) == 0:
            return self._execute_direct(user_prompt)

        called_agents = []

        for i, task_description in enumerate(tasks_list):

            result, called_agent = self._execute_task(task_description)
            called_agents.append(called_agent)

            if not result.success:
                return AgentOutput(
                    response=f"Execution failed at step {i}: {result.error}",
                    success=False,
                    error=f"task_{i}_failed",
                    agent_id="autonomous_workflow",
                    metadata={"called_agents": called_agents}
                )

        return AgentOutput(
            response="Workflow ended with success",
            success=True,
            agent_id="autonomous_workflow",
            metadata={"called_agents": called_agents}
        )

    def _execute_task(self, task: str) -> AgentOutput:
        """
        Execute single task with specialized agent.

        Args:
            task: Task description to execute

        Returns:
            Tuple of (AgentOutput, agent_metadata)
        """
        registered_agent = self._agent_repository.find_by_name("ExecAgent")
        agent = self._agent_factory.create_agent(registered_agent)

        system_prompt = self._context_manager.get_execution_system_prompt()
        system_prompt += "\n\n" + self._context_manager.get_available_tools_prompt(agent)

        result = agent.run(task=task, system_prompt=system_prompt)
        return result, {"agent_name": agent._identity.agent_name}
