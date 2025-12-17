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

    OPTION B - Agent Routing (commented in code):
    -----------------------------------------------
    To enable specialized agent routing:
    1. Uncomment AgentFactory initialization in orchestrator._setup_components()
    2. Uncomment agent_factory/agent_repository params in __init__
    3. Uncomment _route_to_agent() method
    4. Uncomment routing logic in _execute_step()

    This will route tasks to specialized agents:
        - "git commit" → GitAgent (git_agent.json)
        - "list files" → BashAgent (bash_agent.json)
        - "hello" → DefaultAgent (default_agent.json)
        - etc.

    Benefits: Agent caching, specialized tools, better performance
    Current: Uses MockAgent for all tasks (simple, for testing)
    """

    def __init__(
        self,
        llm,
        tool_scheduler,
        tool_registry,
        memory_manager,
        context_manager,
        # agent_factory=None,  # Option B: pass AgentFactory for routing
        # agent_repository=None  # Option B: pass AgentRepository for loading profiles
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
        self.context_manager = context_manager

        # Option B: AgentFactory for routing to specialized agents
        # self._agent_factory = agent_factory
        # self._agent_repository = agent_repository

        logger.info("EXECUTION_MANAGER", "ExecutionManager initialized")
    
    def _execute_direct(self, user_input: str, context: str = "") -> AgentOutput:
        """
        Execute user input directly without todolist (fallback mode).

        Args:
            user_input: User input to process

        Returns:
            AgentOutput from direct execution
        """
        #todo remplacer mockagent par un agent default
        from tests.test_utils.mock_agent import MockAgent
        logger.info("EXECUTION_MANAGER", "Executing directly without todolist")

        mock_agent = MockAgent(
            self._llm,
            self._tool_scheduler,
            self._tool_registry,
            self._memory_manager
        )

        # todo
        user_prompt=user_input
        system_prompt = "Answer base on history and user_query"

        result = mock_agent.run(
            user_prompt=user_prompt,
            system_prompt=system_prompt
        )
        result.metadata={"called_agents":[{"agent_name": mock_agent._identity.agent_name}]}
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
        from tests.test_utils.mock_agent import MockAgent

        logger.info("EXECUTION_MANAGER", "Starting autonomous execution")

        # Create agent for todolist initialization
        agent = MockAgent(
            self._llm,
            self._tool_scheduler,
            self._tool_registry,
            self._memory_manager
        )

        # Create state manager
        state_manager = StateManager(context_manager=self.context_manager, agent=agent)

        # Initialize todolist
        success = state_manager.init_todolist(user_input, context)

        if not success:
            # Fallback to direct execution
            return self._execute_direct(user_input, context)

        logger.info("EXECUTION_MANAGER", "Todolist initialized", {
            "initial_state": state_manager.get_state_summary()
        })

        iteration = 0
        called_agents = []
        # max_iterations should be todolist steps number
        while not state_manager.is_complete() and iteration < max_iterations:
            iteration += 1

            # Get next pending step
            next_step = state_manager.get_next_step()

            if next_step is None:
                logger.warning("EXECUTION_MANAGER", "No pending steps but todolist not complete")
                break

            step_id = next_step.get("step_id", "unknown")

            logger.info("EXECUTION_MANAGER", f"Executing step: {step_id}", {
                "description": next_step.get("description", "")[:100]
            })

            # Execute step with specialized agent
            result, called_agent = self._execute_step(step=next_step)
            called_agents.append(called_agent)

            # Check if step failed
            if not result.success:
                logger.error("EXECUTION_MANAGER", f"Step {step_id} failed", {
                    "error": result.error
                })
                return AgentOutput(
                    response=f"Execution failed at step {step_id}: {result.error}",
                    success=False,
                    error=f"step_{step_id}_failed",
                    agent_id="autonomous_workflow",
                    metadata={"called_agents":called_agents}
                )

            # Update todolist based on result
            state_manager.update_from_result(step_id, result)

            logger.info("EXECUTION_MANAGER", f"Step {step_id} completed successfully")

        # Check why loop ended
        if iteration >= max_iterations:
            logger.error("EXECUTION_MANAGER", "Max iterations reached", {
                "max_iterations": max_iterations,
                "state": state_manager.get_state_summary()
            })
            return AgentOutput(
                response=f"Max iterations ({max_iterations}) reached without completion",
                success=False,
                error="max_iterations_reached",
                agent_id="autonomous_workflow",
                metadata={"called_agents": called_agents}
            )

        if not state_manager.is_complete():
            logger.warning("EXECUTION_MANAGER", "Workflow ended but not complete")
            return AgentOutput(
                response="Workflow ended without completion",
                success=False,
                error="incomplete_workflow",
                agent_id="autonomous_workflow",
                metadata={"called_agents": called_agents}
            )

        # Generate final report
        logger.info("EXECUTION_MANAGER", "Workflow completed successfully", {
            "total_iterations": iteration,
            "completed_steps": len(state_manager.get_completed_steps())
        })

        return self._generate_final_report(state_manager, called_agents)

    # ========== OPTION B: Agent Routing (commented for future use) ==========
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
        from tests.test_utils.mock_agent import MockAgent

        step_id = step.get("step_id", "unknown")
        description = step.get("description", "")

        logger.info("EXECUTION_MANAGER", f"Creating agent for step {step_id}")

        # ===== OPTION B: Use AgentFactory with routing (commented) =====
        # # 1. Route to appropriate agent based on description
        # registered_agent = self._route_to_agent(description)
        #
        # # 2. Create/get agent instance from factory (with caching)
        # agent = self._agent_factory.create_agent(registered_agent)
        #
        # logger.info("EXECUTION_MANAGER", f"Routed to agent: {registered_agent.get_agent_name()}")
        # ===============================================================

        # Current: Using MockAgent directly (simple, no routing)
        from tests.test_utils.mock_agent import MockAgent
        agent = MockAgent(
            self._llm,
            self._tool_scheduler,
            self._tool_registry,
            self._memory_manager
        )

        user_prompt = description
        system_prompt = self.context_manager.get_agent_system_prompt()
        system_prompt += "\n\n" + self.context_manager.get_available_tools_prompt(agent)
        # Execute agent with iterative mode using step description
        result = agent.run(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            mode="iterative"
        )
        return result, {"agent_name": agent._identity.agent_name}

    def _generate_final_report(self, state_manager: StateManager, called_agents = []) -> AgentOutput:
        """
        Generate final aggregated report from all findings.

        Args:
            state_manager: StateManager with completed workflow

        Returns:
            AgentOutput with aggregated report
        """
        findings = state_manager.get_findings()
        completed_steps = state_manager.get_completed_steps()
        iteration_count = state_manager.get_iteration_count()

        report_parts = [
            "# Autonomous Workflow Completed",
            "",
            f"Total Steps: {len(completed_steps)}",
            f"Iterations: {iteration_count}",
            "",
            "## Step Results",
            ""
        ]

        # Add results from each completed step
        for step_id in completed_steps:
            if step_id in findings:
                finding = findings[step_id]
                preview = finding[:500]
                if len(finding) > 500:
                    preview += "\n... (truncated)"

                report_parts.extend([
                    f"### {step_id}",
                    preview,
                    ""
                ])

        report_parts.extend([
            "---",
            "Workflow executed successfully."
        ])

        report_text = "\n".join(report_parts)

        logger.info("EXECUTION_MANAGER", "Final report generated", {
            "report_length": len(report_text),
            "steps_included": len(completed_steps)
        })

        return AgentOutput(
            response=report_text,
            success=True,
            agent_id="autonomous_workflow",
            metadata={"called_agents": called_agents}
        )

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
