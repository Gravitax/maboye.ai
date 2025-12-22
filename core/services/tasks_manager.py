from typing import Dict, Any, Tuple, List
from core.logger import logger
from agents.types import AgentOutput
from tools.tool_ids import ToolId


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
        tasks_analyse = tasks.get("analyse", "")
        tasks_list = tasks.get("tasks", [])

        if not tasks_list or len(tasks_list) == 0:
            return self._execute_direct(user_prompt)

        called_agents = []
        tasks_context = ""

        for i, task_data in enumerate(tasks_list):
            # Handle both string and dict tasks schema
            if isinstance(task_data, dict):
                step = task_data.get("step", "Unknown step")
                outcome = task_data.get("expected_outcome", "Unknown outcome")
                task_description = (
                    f"# CURRENT TASK OBJECTIVE:\n{step}\n"
                    f"## Expected Outcome:\n{outcome}\n"
                    f"## USER QUERY:\n{tasks_analyse}"
                )
            else:
                task_description = (
                    f"# CURRENT TASK OBJECTIVE:\n{task_data}\n"
                    f"## USER QUERY:\n{tasks_analyse}"
                )

            logger.system("TASKS MANAGER", "task execute", task_description)

            result, called_agent = self._execute_task(task_description, tasks_context)
            called_agents.append({"agent_name": called_agent.get_identity().agent_name})

            if result.cmd == ToolId.TASKS_COMPLETED.value:
                break

            # Retrieve full conversation history for this task execution
            if len(tasks_context) > 0: tasks_context = '\n' + tasks_context
            else: tasks_context += "\n## TASKS REALIZED HISTORY:"
            tasks_context += f"\n### TASK {i+1}: {task_description}\n"
            tasks_context += self._context_manager.format_context_as_string(agent_id=called_agent.get_identity().agent_id, max_turns=2)

            logger.system("TASKS MANAGER", "task result", result)

            if not result.success:
                return AgentOutput(
                    response=f"Execution failed at step {i+1}: {result.error}\n\nContext:\n{tasks_context}",
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

    def _execute_task(self, task: str, tasks_context: str) -> Tuple[AgentOutput, Any]:
        """
        Execute single task with specialized agent.

        Args:
            task: Task description to execute

        Returns:
            Tuple of (AgentOutput, Agent)
        """
        registered_agent = self._agent_repository.find_by_name("ExecAgent")
        agent = self._agent_factory.create_agent(registered_agent)

        logger.system("TASKS MANAGER", "aaa")

        system_prompt = self._context_manager.get_execution_system_prompt()
        system_prompt += self._context_manager.build_system_prompt(agent)
        logger.system("TASKS MANAGER", "bbb")
        result = agent.run(task=task, system_prompt=system_prompt, user_prompt=tasks_context)
        return result, agent
