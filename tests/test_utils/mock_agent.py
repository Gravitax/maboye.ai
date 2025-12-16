"""
Mock Agent for testing the execution workflow.
"""
from agents.agent import Agent
from core.logger import logger
from core.domain import AgentIdentity, AgentCapabilities, ExecutionPlan, ExecutionStep, ActionStep
from agents.types import AgentOutput
import datetime
import uuid
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
            system_prompt="You are a Mock Agent.",
            authorized_tools=[]
        )
        
        super().__init__(
            agent_identity=mock_identity,
            agent_capabilities=mock_capabilities,
            llm=llm,
            tool_scheduler=tool_scheduler,
            tool_registry=tool_registry,
            memory_coordinator=memory_coordinator
        )

    def run(self, query: str, mode: str = "test", scenario: str = "auto", max_iterations: int = 10):
        """
        Run a test case by name.

        Modes:
        - "iterative": Uses mock backend with conversation history
        - "test": Legacy mode using mock backend test endpoint
        """

        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="user",
            content=query
        )

        if mode == "iterative":
            return self._run_iterative(query, scenario, max_iterations)

        # Legacy test mode
        logger.info("MOCK_AGENT", f"Running: {query}")

        llm_response = self._llm.test(query)

        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="assistant",
            content=llm_response.content
        )

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
            ) for step in llm_response.steps
        ]

        if len(steps) == 0:
            return AgentOutput(
                response="Mock response to " + query,
                success=True,
                agent_id=self._identity.agent_id
            )

        # we received a json from the llm with a series of commands to use step by step
        execution_plan = ExecutionPlan(
            user_query=f"test: {query}",
            steps=steps
        )

        result = self.plan_execution_service.execute_plan(execution_plan, confirm_dangerous=True)

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

        return AgentOutput(
            response="Mock response to " + query,
            success=result.success,
            agent_id=self._identity.agent_id
        )

    def _initialize_messages(self, user_query: str) -> List[Dict[str, Any]]:
        """Initialize conversation messages with history."""
        messages = [
            {"role": "system", "content": self._build_system_prompt()}
        ]
        # Get conversation history from Agent's parent class method
        context = self._memory_coordinator.get_conversation_context(
            agent_identity=self._identity,
            max_turns=self._capabilities.max_memory_turns
        )
        # Add history messages from ConversationContext
        messages.extend(context.conversation_history)
        # Add current user query
        messages.append({"role": "user", "content": user_query})
        return messages

    def _handle_final_response(self, content: str, iteration: int) -> AgentOutput:
        """Handle final text response from LLM."""

        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="assistant",
            content=content
        )

        is_error = content.startswith("ERROR:")

        return AgentOutput(
            response=content,
            success=not is_error,
            error="agent_error" if is_error else None,
            agent_id=self._identity.agent_id
        )

    def _execute_single_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """Execute a single tool and return result."""
        if not self._capabilities.can_use_tool(tool_name):
            return f"Error: Tool '{tool_name}' not authorized"

        try:
            result = self._tool_registry.execute(tool_name, **tool_args)
            return str(result)
        except Exception as error:
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

            result = self._execute_single_tool(tool_name, tool_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": result
            })

            self._save_tool_result_to_memory(tool_name, result)

    def _create_max_iterations_output(self, max_iterations: int) -> AgentOutput:
        """Create output for max iterations reached."""
        return AgentOutput(
            response=f"Max iterations ({max_iterations}) reached without final response",
            success=False,
            error="max_iterations",
            agent_id=self._identity.agent_id
        )

    def _run_iterative(
        self,
        user_query: str,
        scenario: str = "auto",
        max_iterations: int = 10
    ) -> AgentOutput:
        """Run iterative workflow with tool calls and conversation history."""

        # Initialize messages with conversation history
        messages = self._initialize_messages(user_query)

        iteration_count = 0

        while iteration_count < max_iterations:
            iteration_count += 1

            llm_response = self._llm.test_iterative(
                messages,
                scenario,
                temperature=self._capabilities.llm_temperature,
                max_tokens=self._capabilities.llm_max_tokens,
                timeout=self._capabilities.llm_timeout
            )

            if llm_response.get("tool_calls") is None:
                return self._handle_final_response(
                    llm_response.get("content", ""),
                    iteration_count
                )

            tool_calls = llm_response.get("tool_calls", [])
            assistant_content = llm_response.get("content", "")

            messages.append({
                "role": "assistant",
                "content": assistant_content,
                "tool_calls": tool_calls
            })

            self._process_tool_calls(tool_calls, messages)

        return self._create_max_iterations_output(max_iterations)

    def _build_system_prompt(self) -> str:
        """Build system prompt with available tools."""
        tools_list = "\n".join([
            f"- {tool}: {self._tool_registry.get_tool(tool).metadata.description}"
            for tool in self._capabilities.authorized_tools
        ])

        return f"You are an intelligent agent that can use tools to accomplish tasks. Available tools: {tools_list}"
