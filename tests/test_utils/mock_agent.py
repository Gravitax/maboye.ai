"""
Mock Agent for testing the execution workflow.
"""
from agents.agent import Agent
from core.logger import logger
from core.domain import AgentIdentity, AgentCapabilities, ExecutionPlan, ExecutionStep, ActionStep
import datetime
import uuid
import dataclasses

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
            authorized_tools=["read_file", "write_file"]
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

