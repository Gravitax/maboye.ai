"""
Modern Agent Implementation

Refactored agent that uses the new domain-driven architecture directly.
Now includes a planning and execution workflow.
"""

from core.logger import logger
from core.llm_wrapper import LLMWrapper
from core.tool_scheduler import ToolScheduler
from tools.tool_base import ToolRegistry
from core.domain import AgentIdentity, AgentCapabilities, ExecutionPlan
from core.services.agent_memory_coordinator import AgentMemoryCoordinator
from core.services.agent_prompt_constructor import AgentPromptConstructor
from core.services.plan_execution_service import PlanExecutionService, PlanExecutionError
from core.services.plan_parser import parse_json_to_plan, PlanParseError
from agents.types import AgentOutput
import json

class Agent:
    """
    Modern agent implementation using domain-driven architecture.
    Can operate in two modes: 'direct' for immediate tool calls, 
    and 'plan' for generating and executing a plan.
    """

    def __init__(
        self,
        agent_identity: AgentIdentity,
        agent_capabilities: AgentCapabilities,
        llm: LLMWrapper,
        tool_scheduler: ToolScheduler,
        tool_registry: ToolRegistry,
        memory_coordinator: AgentMemoryCoordinator,
    ):
        self._identity = agent_identity
        self._capabilities = agent_capabilities
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._tool_registry = tool_registry
        self._memory_coordinator = memory_coordinator
        
        self.plan_execution_service = PlanExecutionService(tool_scheduler, self._tool_registry)

        self._prompt_constructor = AgentPromptConstructor(
            agent_capabilities=agent_capabilities,
            memory_coordinator=memory_coordinator,
            tool_registry=tool_registry
        )

        logger.info("AGENT", f"Agent initialized: {agent_identity.agent_name}")

    def run(self, user_prompt: str, mode: str = "plan") -> AgentOutput:
        """
        Execute agent with user input based on the selected mode.
        """
        logger.info("AGENT", "Starting agent execution", {
            "agent_name": self._identity.agent_name,
            "mode": mode,
            "input_length": len(user_prompt)
        })

        try:
            if mode == "plan":
                final_response = self._execute_planning_workflow(user_prompt)
            else:
                final_response = self._execute_direct_workflow(user_prompt)

            self._memory_coordinator.save_conversation_turn(
                agent_id=self._identity.agent_id,
                role="assistant",
                content=final_response
            )

            logger.info("AGENT", "Agent execution completed", {
                "agent_name": self._identity.agent_name,
                "response_length": len(final_response)
            })

            return AgentOutput(response=final_response, success=True)

        except (PlanExecutionError, PlanParseError, Exception) as e:
            logger.error("AGENT", "Agent execution failed", {
                "agent_name": self._identity.agent_name,
                "error": str(e)
            })
            return AgentOutput(response=f"Error: {str(e)}", success=False, error=str(e))

    def _execute_planning_workflow(self, user_prompt: str) -> str:
        """Generates, confirms, and executes a plan, or returns a direct response."""
        
        planning_prompt = self._build_planning_prompt()
        messages = [
            {"role": "system", "content": planning_prompt},
            {"role": "user", "content": f"Create a plan to: {user_prompt}"}
        ]

        response_content = self._llm.chat(messages, verbose=False)

        try:
            # Try to parse the response as a JSON plan
            plan = parse_json_to_plan(response_content, user_prompt)
            
            self.display_plan(plan)

            if plan.requires_confirmation:
                confirmed = self.get_user_confirmation(plan)
                if not confirmed:
                    return "Plan cancelled by user."

            result = self.plan_execution_service.execute_plan(
                plan,
                confirm_dangerous=True # Assuming confirmation was given
            )

            if result.success:
                return f"Plan executed successfully. Completed {len(result.completed_steps)} steps."
            else:
                return f"Plan execution failed: {result.error}"

        except (json.JSONDecodeError, PlanParseError):
            # If parsing fails, assume it's a direct string response
            return response_content

    def _execute_direct_workflow(self, user_prompt: str) -> str:
        """Executes the agent in direct tool-calling mode."""
        context = self._memory_coordinator.get_conversation_context(
            agent_identity=self._identity,
            max_turns=self._capabilities.max_memory_turns
        )
        messages = self._prompt_constructor.build_conversation_messages(context)
        messages.append({"role": "user", "content": user_prompt})

        self._memory_coordinator.save_conversation_turn(
            agent_id=self._identity.agent_id,
            role="user",
            content=user_prompt
        )
        
        return self._execute_reasoning_loop(messages)

    def _execute_reasoning_loop(self, messages: list) -> str:
        """Execute the think-act-observe reasoning loop for direct mode."""
        max_turns = self._capabilities.max_reasoning_turns
        for turn in range(max_turns):
            logger.info("AGENT", f"Reasoning turn {turn + 1}/{max_turns}")
            response = self._llm.chat(messages, verbose=True)
            message = response.choices[0].message if response.choices else None
            if not message:
                logger.error("AGENT", "No message in LLM response")
                return "Error: No response from LLM"

            tool_calls = message.tool_calls if message.tool_calls else []
            if not tool_calls:
                content = message.content or ""
                logger.info("AGENT", "Final response received (no tool calls)")
                return content

            tool_calls_dict = [{"id": tc.id, "type": tc.type, "function": tc.function} for tc in tool_calls]
            messages.append({"role": "assistant", "content": message.content, "tool_calls": tool_calls_dict})

            for tool_call in tool_calls:
                tool_name = tool_call.function.get("name")
                tool_args = tool_call.function.get("arguments", {})
                tool_id = tool_call.id
                logger.info("AGENT", f"Executing tool: {tool_name}")
                if not self._capabilities.can_use_tool(tool_name):
                    result = f"Error: Tool '{tool_name}' not authorized"
                    logger.warning("AGENT", f"Tool not authorized: {tool_name}")
                else:
                    result = self._tool_scheduler.execute_tool(tool_name, tool_args)
                messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})

        logger.warning("AGENT", f"Max reasoning turns ({max_turns}) reached")
        return str(messages[-1].get("content", "Max reasoning turns reached"))

    def _build_planning_prompt(self) -> str:
        """Build system prompt for planning"""
        tools_description = self._prompt_constructor.format_tools_section()
        return f"""You are a planning agent. Your task is to break down user requests into a step-by-step JSON execution plan.

Available tools:
{tools_description}

Output format (JSON):
{{
  "steps": [
    {{
      "step_number": 1,
      "description": "Description of the first step",
      "actions": [
        {{
          "tool_name": "tool_name_1",
          "arguments": {{"arg1": "value1"}},
          "description": "Action description"
        }}
      ]
    }}
  ],
  "requires_confirmation": true
}}

Rules:
1. Break complex tasks into small, logical steps.
2. Each step must have a clear description.
3. List all required actions for each step.
4. Set `depends_on` for steps that rely on previous results.
5. Set `requires_confirmation=true` for any destructive or file-modifying operations.
6. Be precise with tool arguments.
"""

    def display_plan(self, plan: ExecutionPlan):
        """Display plan to user for review"""
        print("\n" + "="*60)
        print("EXECUTION PLAN")
        print("="*60)
        print(f"Query: {plan.user_query}")
        print(f"Steps: {len(plan.steps)}")
        if plan.estimated_duration:
            print(f"Estimated duration: {plan.estimated_duration}")
        print()

        for step in plan.steps:
            print(f"Step {step.step_number}: {step.description}")
            for action in step.actions:
                tool_desc = f"  → {action.tool_name}"
                if action.description:
                    tool_desc += f": {action.description}"
                print(tool_desc)
                for key, value in action.arguments.items():
                    print(f"      {key}: {str(value)[:50]}...")
            print()

        if plan.is_dangerous(self._tool_registry):
            print("⚠️  WARNING: This plan contains potentially dangerous operations")
        print("="*60)

    def get_user_confirmation(self, plan: ExecutionPlan) -> bool:
        """Get user confirmation for plan execution"""
        while True:
            response = input("Execute this plan? [y/n]: ").lower()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            else:
                print("Please answer 'y' or 'n'")

    def get_identity(self) -> AgentIdentity:
        """Get agent identity."""
        return self._identity

    def get_capabilities(self) -> AgentCapabilities:
        """Get agent capabilities."""
        return self._capabilities

    def __repr__(self) -> str:
        return f"<Agent name='{self._identity.agent_name}' id='{self._identity.agent_id}'>"
