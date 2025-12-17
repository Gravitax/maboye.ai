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
        memory_manager
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
            memory_manager=memory_manager
        )

    def _format_output(self, response: str, success: bool, error: str = None) -> AgentOutput:
        return AgentOutput(
            response=response,
            success=success,
            agent_id=self._identity.agent_id,
            error=error
        )

    def run(self, user_prompt: str, system_prompt:str = "", mode: str = "test", scenario: str = "auto"):
        """
        Run a test case by name.

        Modes:
        - "iterative": Uses mock backend tests/iterative/ endpoint
        - "test": Legacy mode using mock backend tests/ endpoint
        """

        self._memory_manager.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="user",
            content=user_prompt
        )

        if mode == "iterative":
            return self._run_iterative(user_prompt, system_prompt, scenario)

        # test mode
        logger.info("MOCK_AGENT", f"Running: {user_prompt}")

        llm_response = self._llm.test(user_prompt)

        self._memory_manager.save_conversation_turn(
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
            return self._format_output(
                response="Mock response to " + user_prompt,
                success=True
            )

        # we received a json from the llm with a series of commands to use step by step
        execution_plan = ExecutionPlan(
            user_query=f"test: {user_prompt}",
            steps=steps
        )

        result = self.plan_execution_service.execute_plan(execution_plan, confirm_dangerous=True)

        # Save tool calls and results from the execution
        if result.success:
            for step_result in result.completed_steps:
                for action_result in step_result.action_results:
                    self._memory_manager.save_conversation_turn(
                        agent_id=self._identity.agent_id,
                        role="tool",
                        content=str(action_result.result),
                        metadata={
                            "tool_name": action_result.tool_name, 
                            "success": action_result.success
                        }
                    )

        return self._format_output(
            response="Mock response to " + user_prompt,
            success=result.success
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

            self._memory_manager.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="tool",
                content=result,
                metadata={
                    "tool_name": tool_name,
                    "success": "Error" not in result
                }
            )

    def _run_iterative(
        self,
        user_prompt: str,
        system_prompt: str,
        scenario: str = "auto"
    ) -> AgentOutput:
        """Run iterative workflow with tool calls and conversation history."""

        messages = [
            {
                "role": "user",
                "content": user_prompt
            }
        ]


        llm_response = self._llm.test_iterative(
            messages,
            scenario
        )

        if llm_response is None:
            return self._format_output(
                response="Error: No response from LLM",
                success=False,
                error="no_llm_response"
            )

        content = llm_response.get("content", "")
        tool_calls = llm_response.get("tool_calls")

        if tool_calls and len(tool_calls) > 0:
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls
            })

            self._process_tool_calls(tool_calls, messages)

        self._memory_manager.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="assistant",
            content=content
        )
        is_error = content.startswith("ERROR:")

        logger.info("MOCK_AGENT", "Response analysis", {
            "content_preview": content[:100],
            "is_error": is_error,
            "will_return_success": not is_error
        })

        return self._format_output(
            response=content,
            success=not is_error,
            error="agent_error" if is_error else None
        )
