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
        Initialize state manager with orchestrator components.

        Args:
            orchestrator_components: Dictionary containing:
                - llm: LLM wrapper instance
                - tool_scheduler: Tool scheduler instance
                - tool_registry: Tool registry instance
                - memory: Memory coordinator instance
        """
        self._context_manager = context_manager
        self.agent = agent
        self._state = {
            "query": "",
            "todo_list": [],
            "completed": [],
            "findings": {},
            "iteration": 0
        }

        logger.info("STATE_MANAGER", "StateManager initialized")

    def init_todolist(self, user_query: str, context: str = "") -> tuple:
        """
        Initialize todolist by calling an agent to generate it.

        The agent receives the user query and conversation context,
        then generates a structured todolist in JSON format.

        Args:
            user_query: User's original query
            agent: Agent instance to use for todolist generation
            context: Conversation context (recent history)

        Returns:
            Tuple of (success: bool, raw_response: Optional[str])
            - (True, None) if todolist generated successfully
            - (False, raw_text) if response was plain text instead of JSON
            - (False, None) if error occurred
        """
        logger.info("STATE_MANAGER", "Initializing todolist", {
            "query": user_query[:100]
        })

        # todo
        user_prompt = context + "\n\ngenerate todolist on: " + user_query
        system_prompt = self._context_manager.get_todolist_system_prompt()

        # Generate todolist
        result = self.agent.run(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            mode="iterative",
            scenario="auto"
        )

        if not result.success:
            logger.error("STATE_MANAGER", "TodoList generation failed", {
                "error": result.error
            })
            return (False, None)

        logger.debug("STATE_MANAGER", "Agent response received", {
            "response_type": type(result.response).__name__,
            "response_preview": str(result.response)[:200] if result.response else "None"
        })

        # Parse and store todolist
        return self._parse_and_store_todolist(result.response, user_query)

    def _parse_and_store_todolist(self, response: str, user_query: str) -> tuple:
        """
        Parse agent response and store todolist.

        Args:
            response: Agent response containing JSON or plain text
            user_query: Original user query

        Returns:
            Tuple of (success: bool, raw_response: Optional[str])
            - (True, None) if parsed and stored successfully
            - (False, raw_text) if response was plain text instead of JSON
            - (False, None) if error occurred
        """
        try:
            # Direct JSON parse - backend returns valid JSON
            response_stripped = response.strip()

            todolist = json.loads(response_stripped)

            success = self._store_todolist(todolist, user_query)
            return (success)

        except json.JSONDecodeError as e:
            logger.info("STATE_MANAGER", "Response is not JSON, returning raw text", {
                "response_preview": response[:200] if response else "None"
            })
            return (False)

        except Exception as e:
            logger.error("STATE_MANAGER", "Failed to parse todolist", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return (False)

    def _store_todolist(self, todolist: dict, user_query: str) -> bool:
        """
        Validate and store todolist.

        Args:
            todolist: Parsed todolist dictionary
            user_query: Original user query

        Returns:
            True if stored successfully
        """
        # Validate structure
        if "todo_list" not in todolist:
            logger.error("STATE_MANAGER", "No todo_list in JSON")
            return False

        # Store in state and initialize status if not present
        self._state["query"] = todolist.get("query", user_query)
        steps = todolist.get("todo_list", [])

        # Ensure all steps have status field
        for step in steps:
            if "status" not in step:
                step["status"] = "pending"

        self._state["todo_list"] = steps

        logger.info("STATE_MANAGER", "TodoList initialized", {
            "total_steps": len(self._state["todo_list"])
        })

        return True

    def get_next_step(self) -> Optional[Dict[str, Any]]:
        """
        Get next pending step from todolist.

        Returns:
            Next step dict with keys: step_id, description, status, depends_on
            None if no pending steps available
        """
        for step in self._state["todo_list"]:
            if step.get("status") == "pending":
                # Check if dependencies are met
                depends_on = step.get("depends_on")
                if depends_on and depends_on not in self._state["completed"]:
                    continue

                return step

        return None

    def update_from_result(self, step_id: str, result: AgentOutput) -> None:
        """
        Update todolist based on agent execution result.

        The agent can include todolist updates in its response using:
        todo_update: {
            "add": [{"step_id": "...", "description": "..."}],
            "remove": ["step_x"],
            "modify": [{"step_id": "step_y", "description": "new desc"}]
        }

        Args:
            step_id: ID of the completed step
            result: Agent output containing result and optional updates
        """
        logger.info("STATE_MANAGER", f"Updating state for step {step_id}")

        # Mark step as completed
        self._mark_step_completed(step_id)

        # Save findings
        self._state["findings"][step_id] = result.response
        self._state["completed"].append(step_id)

        # Parse and apply todolist updates if present
        self._parse_and_apply_updates(result.response)

        # Increment iteration counter
        self._state["iteration"] += 1

    def _mark_step_completed(self, step_id: str) -> None:
        """
        Mark a step as completed in the todolist.

        Args:
            step_id: Step ID to mark as completed
        """
        for step in self._state["todo_list"]:
            if step.get("step_id") == step_id:
                step["status"] = "completed"
                logger.debug("STATE_MANAGER", f"Marked {step_id} as completed")
                return

        logger.warning("STATE_MANAGER", f"Step {step_id} not found in todolist")

    def _parse_and_apply_updates(self, result_text: str) -> None:
        """
        Parse todolist updates from agent result and apply them.

        Looks for pattern: todo_update: {...}

        Args:
            result_text: Agent result text
        """
        # Look for todo_update in result
        match = re.search(r'todo_update:\s*(\{.*?\})', result_text, re.DOTALL)
        if not match:
            return

        try:
            update = json.loads(match.group(1))

            # Apply additions
            added_count = self._apply_additions(update.get("add", []))

            # Apply removals
            removed_count = self._apply_removals(update.get("remove", []))

            # Apply modifications
            modified_count = self._apply_modifications(update.get("modify", []))

            if added_count or removed_count or modified_count:
                logger.info("STATE_MANAGER", "TodoList updated", {
                    "added": added_count,
                    "removed": removed_count,
                    "modified": modified_count
                })

        except json.JSONDecodeError as e:
            logger.warning("STATE_MANAGER", "Failed to parse todo_update", {
                "error": str(e)
            })

    def _apply_additions(self, additions: List[Dict[str, Any]]) -> int:
        """
        Add new steps to todolist.

        Args:
            additions: List of steps to add

        Returns:
            Number of steps added
        """
        count = 0
        for new_step in additions:
            if "step_id" not in new_step or "description" not in new_step:
                logger.warning("STATE_MANAGER", "Invalid step format in addition")
                continue

            new_step["status"] = "pending"
            self._state["todo_list"].append(new_step)
            count += 1

            logger.debug("STATE_MANAGER", f"Added step: {new_step['step_id']}")

        return count

    def _apply_removals(self, removals: List[str]) -> int:
        """
        Remove steps from todolist.

        Args:
            removals: List of step IDs to remove

        Returns:
            Number of steps removed
        """
        count = 0
        for remove_id in removals:
            initial_len = len(self._state["todo_list"])
            self._state["todo_list"] = [
                s for s in self._state["todo_list"]
                if s.get("step_id") != remove_id
            ]

            if len(self._state["todo_list"]) < initial_len:
                count += 1
                logger.debug("STATE_MANAGER", f"Removed step: {remove_id}")

        return count

    def _apply_modifications(self, modifications: List[Dict[str, Any]]) -> int:
        """
        Modify existing steps in todolist.

        Args:
            modifications: List of step modifications

        Returns:
            Number of steps modified
        """
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
                    logger.debug("STATE_MANAGER", f"Modified step: {step_id}")
                    break

        return count

    def is_complete(self) -> bool:
        """
        Check if all steps in todolist are completed.

        Returns:
            True if all steps completed, False otherwise
        """
        if not self._state["todo_list"]:
            return False

        all_completed = all(
            step.get("status") == "completed"
            for step in self._state["todo_list"]
        )

        return all_completed

    def get_findings(self) -> Dict[str, str]:
        """
        Get all findings from completed steps.

        Returns:
            Dictionary mapping step_id to result text
        """
        return self._state["findings"].copy()

    def get_state_summary(self) -> str:
        """
        Get human-readable summary of current state.

        Returns:
            Summary string
        """
        total = len(self._state["todo_list"])
        completed = len(self._state["completed"])
        iteration = self._state["iteration"]

        return f"Iteration {iteration}: {completed}/{total} steps completed"

    def get_todolist(self) -> List[Dict[str, Any]]:
        """
        Get current todolist.

        Returns:
            List of step dictionaries
        """
        return self._state["todo_list"].copy()

    def get_completed_steps(self) -> List[str]:
        """
        Get list of completed step IDs.

        Returns:
            List of step IDs
        """
        return self._state["completed"].copy()

    def get_iteration_count(self) -> int:
        """
        Get current iteration count.

        Returns:
            Number of iterations executed
        """
        return self._state["iteration"]

    def __str__(self) -> str:
        """String representation for logging."""
        return f"StateManager({self.get_state_summary()})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"StateManager("
            f"query='{self._state['query'][:50]}...', "
            f"steps={len(self._state['todo_list'])}, "
            f"completed={len(self._state['completed'])}, "
            f"iteration={self._state['iteration']})"
        )
