from typing import Dict, Any, Tuple, List, Union
from core.logger import logger
from agents.types import AgentOutput
from tools.tool_ids import ToolId
from core.prompt_builder import PromptBuilder, PromptRole, PromptId


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

        self._builder = PromptBuilder()
    
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
        result.metadata={"called_agents":[{"agent_name": agent.get_identity().agent_name}]} # Fixed: Access via getter or public prop if available, assumed get_identity() from context
        return result

    def execute(self, user_prompt: str, tasks: dict) -> AgentOutput:
        """
        Execute autonomous workflow with cleaned structure.

        Args:
            user_prompt: User input prompt
            tasks: Dictionary containing "analyse" and "tasks" list

        Returns:
            AgentOutput
        """
        tasks_analyse = tasks.get("analyse", "")
        tasks_list = tasks.get("tasks", [])

        if not tasks_list:
            return self._execute_direct(user_prompt)

        called_agents_meta = []
        execution_context = ""

        for index, task_data in enumerate(tasks_list):
            step_num = index + 1

            # 1. Prepare Task Data
            objective, outcome = self._extract_task_data(task_data)

            # 2. Build Professional Prompt
            current_prompt = self._build_task_prompt(tasks_analyse, objective, outcome)
            logger.system("TASKS MANAGER", "task execute", current_prompt)

            # 3. Execute Step
            # Note: We pass the accumulated context (history) here as user_prompt or separate context arg
            result, active_agent = self._execute_task(current_prompt, execution_context)
            called_agents_meta.append({"agent_name": active_agent.get_identity().agent_name})

            # 4. Update History Context (only store objective, not full prompt)
            execution_context = self._update_context(
                execution_context,
                step_num,
                objective,
                result
            )

            logger.system("TASKS MANAGER", "task result", result)

            # 5. Check Short-circuit
            if result.cmd == ToolId.TASKS_COMPLETED.value:
                break

            # 6. Handle Errors
            reponse_too_big = len(result.response) > 1000
            if not result.success or reponse_too_big:
                 tmp = "\nresponse is too voluminous" if reponse_too_big else ""
                 return AgentOutput(
                    response=f"Execution failed at step {step_num}: {result.error}\n\n{execution_context}" + tmp,
                    success=False,
                    error=f"task_{step_num}_failed" + tmp,
                    agent_id="autonomous_workflow",
                    metadata={"called_agents": called_agents_meta}
                )

        return AgentOutput(
            response=f"Workflow completed successfully.\n{execution_context}",
            success=True,
            agent_id="autonomous_workflow",
            metadata={"called_agents": called_agents_meta}
        )

    def _extract_task_data(self, task_data: Union[Dict, str]) -> Tuple[str, str]:
        """Normalize task input into objective and outcome."""
        if isinstance(task_data, dict):
            return (
                task_data.get("step", "Unknown step"),
                task_data.get("expected_outcome", "Execute successfully")
            )
        return str(task_data), "Complete the task successfully."

    def _build_task_prompt(self, global_analysis: str, objective: str, outcome: str) -> str:
        """Generate a concise, professional English prompt using PromptBuilder."""

        self._builder.clear_prompt(PromptRole.USER)
        self._builder.add_block(PromptRole.USER, f"# GLOBAL CONTEXT\n{global_analysis}")
        self._builder.add_block(PromptRole.USER, f"# CURRENT ASSIGNMENT\n## OBJECTIVE\n{objective}")
        self._builder.add_block(PromptRole.USER, f"## DEFINITION OF DONE\n{outcome}")

        return self._builder.get_prompt(PromptRole.USER)

    def _update_context(self, current_context: str, step_num: int, objective: str, result: AgentOutput) -> str:
        """
        Append the recent execution details to the rolling history.

        Uses a compact format to minimize token usage:
        - STEP number followed by result output only
        - No verbose labels or formatting
        """
        # Initialize header if empty
        if not current_context:
            current_context = "\n## EXECUTION HISTORY:"

        # Append new block with compact format: just step number and output
        new_block = f"\n### STEP {step_num} {result.response}"

        return current_context + new_block

    def _execute_task(self, task: str, tasks_context: str) -> Tuple[AgentOutput, Any]:
        """
        Execute single task with specialized agent.

        Args:
            task: Task description to execute
            tasks_context: The accumulated history context

        Returns:
            Tuple of (AgentOutput, Agent)
        """
        registered_agent = self._agent_repository.find_by_name("ExecAgent")
        agent = self._agent_factory.create_agent(registered_agent)

        logger.system("TASKS MANAGER", "Initializing specialized agent execution")

        self._builder.clear_prompt(PromptRole.SYSTEM)

        # Build system prompt
        exec_prompt = PromptBuilder.get_prompt_by_id(PromptId.EXEC_AGENT)
        system_context = self._context_manager.get_system_context(agent)

        self._builder.add_block(PromptRole.SYSTEM, exec_prompt)
        self._builder.add_block(PromptRole.SYSTEM, system_context)

        system_prompt = self._builder.get_prompt(PromptRole.SYSTEM)

        # Note: Depending on your Agent.run implementation,
        # you might want to pass 'task' as the main instruction and 'tasks_context' as context/memory.
        result = agent.run(task=task, system_prompt=system_prompt, user_prompt=tasks_context)

        return result, agent
