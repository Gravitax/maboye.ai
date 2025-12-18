"""
State Manager for Dynamic TodoList

Manages the execution state of an autonomous agent workflow.
Handles dynamic todolist updates during execution.
"""

import json
import re
from typing import Dict, List, Optional, Any
from core.logger import logger
from agents.types import AgentOutput


class StateManager:
    """
    Manages dynamic todolist that updates during execution.

    The StateManager is responsible for:
    - Initializing the todolist by calling an agent
    - Tracking execution progress
    - Updating the todolist dynamically based on agent results
    - Storing cumulative findings from completed steps
    - Determining when workflow is complete
    """

    def __init__(self, context_manager, agent):
        """
        Initialize state manager.

        Args:
            context_manager: Context manager for prompts
            agent: Agent instance for todolist generation
        """
        self._context_manager = context_manager
        self.agent = agent
        self._state = {
            "query": "",
            "todo_list": [],
            "completed": [],
            "step_results": {},
            "iteration": 0
        }

    def init_todolist(self, user_query: str, context: str = "") -> bool:
        """
        Initialize todolist by calling an agent to generate it.

        Args:
            user_query: User's original query
            context: Conversation context (recent history)

        Returns:
            True if todolist generated successfully, False otherwise
        """
        if context:
            user_prompt = f"{context}\n\nGenerate todolist for: {user_query}"
        else:
            user_prompt = f"Generate todolist for: {user_query}"

        system_prompt = self._context_manager.get_todolist_system_prompt()
        system_prompt += "\n\n" + self._context_manager.get_available_tools_prompt(self.agent)

        result = self.agent.run(
            user_prompt=user_prompt,
            system_prompt=system_prompt
        )

        if not result.success:
            return False

        return self._parse_and_store_todolist(result.response, user_query)

    def _parse_and_store_todolist(self, response: str, user_query: str) -> bool:
        """
        Parse agent response and store todolist.

        Args:
            response: Agent response containing JSON or plain text
            user_query: Original user query

        Returns:
            True if parsed and stored successfully, False otherwise
        """
        try:
            response_stripped = response.strip()

            # Extract JSON from markdown code blocks if wrapped
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_stripped, re.DOTALL)
            if json_match:
                response_stripped = json_match.group(1).strip()

            todolist = json.loads(response_stripped)
            return self._store_todolist(todolist, user_query)

        except json.JSONDecodeError as e:
            return False

        except Exception as e:
            return False

    def _store_todolist(self, todolist: dict, user_query: str) -> bool:
        """
        Validate and store todolist.

        Args:
            todolist: Parsed todolist dictionary
            user_query: Original user query

        Returns:
            True if stored successfully, False otherwise
        """
        if not isinstance(todolist, dict) or "todo_list" not in todolist:
            return False

        steps = todolist.get("todo_list", [])

        if not isinstance(steps, list) or len(steps) == 0:
            return False

        # Validate each step
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                return False
            if "step_id" not in step or "description" not in step:
                return False

        # Store and initialize status
        self._state["query"] = todolist.get("query", user_query)

        for step in steps:
            if "status" not in step:
                step["status"] = "pending"
        self._state["todo_list"] = steps
        return True

    def get_next_step(self) -> Optional[Dict[str, Any]]:
        """
        Get next pending step from todolist.

        Returns:
            Next step dict or None if no pending steps available
        """
        for step in self._state["todo_list"]:
            if step.get("status") == "pending":
                depends_on = step.get("depends_on")
                if depends_on and depends_on not in self._state["completed"]:
                    continue
                return step
        return None

    def update_from_result(self, step_id: str, result: AgentOutput) -> None:
        """
        Update todolist based on agent execution result.

        Args:
            step_id: ID of the completed step
            result: Agent output containing result and optional updates
        """
        self._mark_step_completed(step_id)
        self._state["step_results"][step_id] = result.response
        self._state["completed"].append(step_id)
        self._parse_and_apply_updates(result.response)
        self._state["iteration"] += 1

    def _mark_step_completed(self, step_id: str) -> None:
        """Mark a step as completed in the todolist."""
        for step in self._state["todo_list"]:
            if step.get("step_id") == step_id:
                step["status"] = "completed"
                return

    def _parse_and_apply_updates(self, result_text: str) -> None:
        """Parse todolist updates from agent result and apply them."""
        match = re.search(r'todo_update:\s*(\{.*?\})', result_text, re.DOTALL)
        if not match:
            return

        try:
            update = json.loads(match.group(1))
            added = self._apply_additions(update.get("add", []))
            removed = self._apply_removals(update.get("remove", []))
            modified = self._apply_modifications(update.get("modify", []))

            if added or removed or modified:
                pass
        except json.JSONDecodeError:
            pass

    def _apply_additions(self, additions: List[Dict[str, Any]]) -> int:
        """Add new steps to todolist."""
        count = 0
        for new_step in additions:
            if "step_id" not in new_step or "description" not in new_step:
                continue
            new_step["status"] = "pending"
            self._state["todo_list"].append(new_step)
            count += 1
        return count

    def _apply_removals(self, removals: List[str]) -> int:
        """Remove steps from todolist."""
        count = 0
        for remove_id in removals:
            initial_len = len(self._state["todo_list"])
            self._state["todo_list"] = [
                s for s in self._state["todo_list"]
                if s.get("step_id") != remove_id
            ]
            if len(self._state["todo_list"]) < initial_len:
                count += 1
        return count

    def _apply_modifications(self, modifications: List[Dict[str, Any]]) -> int:
        """Modify existing steps in todolist."""
        count = 0
        for mod in modifications:
            step_id = mod.get("step_id")
            if not step_id:
                continue
            for step in self._state["todo_list"]:
                if step.get("step_id") == step_id:
                    if "description" in mod:
                        step["description"] = mod["description"]
                    if "depends_on" in mod:
                        step["depends_on"] = mod["depends_on"]
                    count += 1
                    break
        return count

    def is_complete(self) -> bool:
        """Check if all steps in todolist are completed."""
        if not self._state["todo_list"]:
            return False
        return all(step.get("status") == "completed" for step in self._state["todo_list"])

    def get_step_results(self) -> Dict[str, str]:
        """Get all step results from completed steps."""
        return self._state["step_results"].copy()

    def get_todolist(self) -> List[Dict[str, Any]]:
        """Get current todolist."""
        return self._state["todo_list"].copy()

    def get_state(self, field: Optional[str] = None) -> Any:
        """
        Get entire state or specific field.

        Args:
            field: Optional field name (query, todo_list, completed, step_results, iteration)
                   If None, returns entire state

        Returns:
            State dict copy or specific field value
        """
        if field is None:
            return self._state.copy()

        if field in self._state:
            value = self._state[field]
            if isinstance(value, (list, dict)):
                return value.copy()
            return value

        return None

    def get_completed_steps(self) -> List[str]:
        """Get list of completed step IDs."""
        return self._state["completed"].copy()

    def display_todolist(self) -> str:
        """
        Display todolist in a clean, indented format for terminal.

        Returns:
            Formatted string with todolist and progress
        """
        if not self._state["todo_list"]:
            return "No todolist"

        total = len(self._state["todo_list"])
        completed = len(self._state["completed"])
        iteration = self._state["iteration"]

        lines = [
            f"TodoList Progress: {completed}/{total} steps completed (iteration {iteration})",
            ""
        ]

        for step in self._state["todo_list"]:
            step_id = step.get("step_id", "unknown")
            status = step.get("status", "unknown")
            description = step.get("description", "")
            depends_on = step.get("depends_on")

            status_icon = "✓" if status == "completed" else "○"
            lines.append(f"  {status_icon} {step_id}: {description}")

            if depends_on:
                lines.append(f"      depends_on: {depends_on}")

        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation for logging."""
        total = len(self._state["todo_list"])
        completed = len(self._state["completed"])
        return f"StateManager({completed}/{total} completed)"
