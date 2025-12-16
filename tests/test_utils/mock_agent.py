"""
Mock Agent for testing the execution workflow.
"""
from agents.agent import Agent
from core.logger import logger
from core.domain import AgentIdentity, AgentCapabilities, ExecutionPlan, ExecutionStep, ActionStep
from agents.types import AgentOutput
import datetime
import uuid
import dataclasses
from typing import Dict, List, Any

class MockAgent(Agent):
    def __init__(
        self,
        llm,
        tool_scheduler,
        tool_registry,
        memory_coordinator
    ):
        mock_identity = AgentIdentity(
            agent_id=str(uuid.uuid4()), 
            agent_name="MockAgent", 
            creation_timestamp=datetime.datetime.now()
        )
        mock_capabilities = AgentCapabilities(
            description="Mock Agent for testing purposes.",
            authorized_tools=[
                "read_file", "write_file", "edit_file", "list_files", "file_info",
                "grep", "find_file", "get_file_structure", "code_search",
                "bash", "git_status", "git_log"
            ]
        )
        
        super().__init__(
            agent_identity=mock_identity,
            agent_capabilities=mock_capabilities,
            llm=llm,
            tool_scheduler=tool_scheduler,
            tool_registry=tool_registry,
            memory_coordinator=memory_coordinator
        )

    def run(self, test_name: str, mode: str = "test") -> dict:
        """
        Run a test case by name.
        1. Get a plan from the mock backend.
        2. Execute the plan.
        3. Save the results to memory.
        4. Return the execution results.
        """
        logger.info("MOCK_AGENT", f"Running test: {test_name}")

        # 1. Get a plan from the mock backend
        llm_plan = self._llm.test(test_name)
        
        steps = [
            ExecutionStep(
                step_number=step.step_number,
                description=step.description,
                actions=[
                    ActionStep(
                        tool_name=action.tool_name,
                        arguments=action.arguments,
                        description=action.description
                    ) for action in step.actions
                ]
            ) for step in llm_plan.steps
        ]
        execution_plan = ExecutionPlan(
            user_query=f"test: {test_name}",
            steps=steps
        )
        
        logger.info("MOCK_AGENT", "Plan to execute:", {"plan": execution_plan})
        self.display_plan(execution_plan)

        # 2. Execute the plan
        result = self.plan_execution_service.execute_plan(execution_plan, confirm_dangerous=True)
        logger.info("MOCK_AGENT", "Plan execution result:", {"result": result})

        # 3. Save the results to memory
        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="user",
            content=f"test: {test_name}"
        )
        # Save tool calls and results from the execution
        if result.success:
            for step_result in result.completed_steps:
                for action_result in step_result.action_results:
                    self._memory_coordinator.save_conversation_turn(
                        agent_id=self._identity.agent_id,
                        role="tool",
                        content=str(action_result.result),
                        metadata={
                            "tool_name": action_result.tool_name, 
                            "success": action_result.success
                        }
                    )

        return dataclasses.asdict(result)

    def _initialize_messages(self, user_query: str) -> List[Dict[str, Any]]:
        """Initialize conversation messages."""
        return [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_query}
        ]

    def _save_user_query_to_memory(self, user_query: str) -> None:
        """Save user query to memory."""
        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="user",
            content=user_query
        )

    def _handle_final_response(self, content: str, iteration: int) -> AgentOutput:
        """Handle final text response from LLM."""
        logger.info("MOCK_AGENT", "Received final text response", {
            "iteration": iteration,
            "response_length": len(content)
        })

        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="assistant",
            content=content
        )

        is_error = content.startswith("ERROR:")
        if is_error:
            logger.error("MOCK_AGENT", "Agent returned error response", {
                "content": content[:100]
            })

        return AgentOutput(
            response=content,
            success=not is_error,
            error="agent_error" if is_error else None,
            agent_id=self._identity.agent_id
        )

    def _execute_single_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Execute a single tool and return result."""
        if not self._capabilities.can_use_tool(tool_name):
            logger.warning("MOCK_AGENT", f"Tool not authorized: {tool_name}")
            return f"Error: Tool '{tool_name}' not authorized"

        try:
            result = self._tool_registry.execute(tool_name, **tool_args)
            return str(result)
        except Exception as error:
            logger.error("MOCK_AGENT", "Tool execution error", {
                "tool": tool_name,
                "error": str(error)
            })
            return f"Error executing tool: {str(error)}"

    def _save_tool_result_to_memory(self, tool_name: str, result: str) -> None:
        """Save tool execution result to memory."""
        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="tool",
            content=result,
            metadata={
                "tool_name": tool_name,
                "success": "Error" not in result
            }
        )

    def _process_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        messages: List[Dict[str, Any]]
    ) -> None:
        """Process all tool calls and update messages."""
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"].get("arguments", {})
            tool_id = tool_call["id"]

            logger.info("MOCK_AGENT", f"Executing tool: {tool_name}", {
                "arguments": tool_args
            })

            result = self._execute_single_tool(tool_name, tool_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": result
            })

            self._save_tool_result_to_memory(tool_name, result)

    def _check_stagnation(self, stagnation_check: List[tuple]) -> bool:
        """Check if agent is stagnating by repeating same actions."""
        if len(stagnation_check) < 3:
            return False

        return (stagnation_check[-1] == stagnation_check[-2] == stagnation_check[-3])

    def _create_stagnation_output(self) -> AgentOutput:
        """Create output for stagnation detected."""
        logger.warning("MOCK_AGENT", "Stagnation detected, stopping")
        return AgentOutput(
            response="Stagnation detected: Agent is repeating the same actions",
            success=False,
            error="stagnation",
            agent_id=self._identity.agent_id
        )

    def _create_max_iterations_output(self, max_iterations: int) -> AgentOutput:
        """Create output for max iterations reached."""
        logger.warning("MOCK_AGENT", f"Max iterations ({max_iterations}) reached")
        return AgentOutput(
            response=f"Max iterations ({max_iterations}) reached without final response",
            success=False,
            error="max_iterations",
            agent_id=self._identity.agent_id
        )

    def run_iterative(
        self,
        user_query: str,
        scenario: str = "auto",
        max_iterations: int = 10
    ) -> AgentOutput:
        """Run iterative workflow with tool calls."""
        logger.info("MOCK_AGENT", "Starting iterative workflow", {
            "query": user_query,
            "scenario": scenario,
            "max_iterations": max_iterations
        })

        messages = self._initialize_messages(user_query)
        self._save_user_query_to_memory(user_query)

        iteration_count = 0
        stagnation_check = []

        while iteration_count < max_iterations:
            iteration_count += 1
            logger.info("MOCK_AGENT", f"Iteration {iteration_count}/{max_iterations}")

            llm_response = self._llm.chat_iterative(messages, scenario)

            if llm_response.get("tool_calls") is None:
                return self._handle_final_response(
                    llm_response.get("content", ""),
                    iteration_count
                )

            tool_calls = llm_response.get("tool_calls", [])
            assistant_content = llm_response.get("content", "")

            logger.info("MOCK_AGENT", f"Received {len(tool_calls)} tool calls")

            messages.append({
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": tool_calls
            })

            self._process_tool_calls(tool_calls, messages)

            stagnation_check.append(tuple(tc["function"]["name"] for tc in tool_calls))

            if self._check_stagnation(stagnation_check):
                return self._create_stagnation_output()

        return self._create_max_iterations_output(max_iterations)

    def _build_system_prompt(self) -> str:
        """Build system prompt for iterative mode."""
        tools_list = "\n".join([
            f"- {tool}: {self._tool_registry.get_tool(tool).metadata.description}"
            for tool in self._capabilities.authorized_tools
        ])

        return f"""You are an intelligent agent that can use tools to accomplish tasks.

Available tools:
{tools_list}

Instructions:
1. Analyze the user query
2. Use tools as needed to gather information or perform actions
3. When you have enough information, provide a final text response
4. Be concise and focused in your tool usage"""

