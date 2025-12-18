"""
Context Manager

Manages conversation context retrieval and message formatting for LLM.
Serves both orchestrator and agents.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from core.repositories.memory_repository import MemoryRepository
from core.logger import logger


class ContextManager:
    """
    Manages conversation context for orchestrator and agents.

    Responsibilities:
    - Retrieve conversation history by agent_id
    - Format messages for LLM consumption
    - Build context with system prompts

    This manager serves:
    - Orchestrator: retrieves history with agent_id="orchestrator"
    - Agents: retrieves history with their own agent_id
    """

    def __init__(self, memory_repository: MemoryRepository):
        """
        Initialize context manager.

        Args:
            memory_repository: Repository to access conversation history
        """
        self._memory_repository = memory_repository

    def _format_timestamp(self, timestamp_str: str) -> str:
        """
        Format ISO timestamp to hh:mm:ss format.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            Formatted time string (hh:mm:ss)
        """
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime("%H:%M:%S")
        except (ValueError, AttributeError):
            return "00:00:00"

    def get_context(
        self,
        agent_id: str,
        max_turns: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context for an agent.

        Retrieves the N most recent conversation turns from the agent's history.
        Works for both orchestrator (agent_id="orchestrator") and regular agents.

        Args:
            agent_id: Agent identifier (e.g., "orchestrator" or agent-specific ID)
            max_turns: Maximum number of recent turns to retrieve (None = all)

        Returns:
            List of conversation turns (dicts with role, content, timestamp, metadata)
        """
        if not self._memory_repository.exists(agent_id):
            return []

        turns = self._memory_repository.get_conversation_history(
            agent_id=agent_id,
            max_turns=max_turns
        )
        return turns

    def build_messages(
        self,
        agent_id: str,
        system_prompt: Optional[str] = None,
        max_turns: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Build messages list for LLM from agent's conversation history.

        Formats conversation turns into messages array suitable for LLM APIs.
        Optionally prepends a system prompt.
        Messages are sorted from oldest to most recent with timestamps.

        Args:
            agent_id: Agent identifier
            system_prompt: Optional system prompt to prepend
            max_turns: Maximum number of recent turns to include

        Returns:
            List of message dicts with role and content ready for LLM
        """
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Get conversation history (already sorted oldest to most recent)
        turns = self.get_context(agent_id, max_turns)

        # Add conversation turns with timestamps
        for turn in turns:
            content = turn.get("content", "")

            messages.append({
                "role": turn.get("role", "user"),
                "content": content
            })

        return messages

    def format_context_as_string(
        self,
        agent_id: str,
        max_turns: Optional[int] = None
    ) -> str:
        """
        Get conversation context formatted as a string.

        Useful for including context in prompts or logging.
        Messages are sorted from oldest to most recent with timestamps.

        Args:
            agent_id: Agent identifier
            max_turns: Maximum number of recent turns

        Returns:
            Formatted string with conversation history
        """
        turns = self.get_context(agent_id, max_turns)

        if not turns:
            return ""

        lines = ["History:"]
        for turn in turns:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")[:150]
            timestamp = turn.get("timestamp", "")
            time_str = self._format_timestamp(timestamp) if timestamp else "00:00:00"

            lines.append(f"[{time_str}] {role}: {content}")

        return "\n".join(lines)

    def get_last_turn(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent conversation turn for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Last turn dict or None if no history
        """
        return self._memory_repository.get_last_turn(agent_id)

    def __str__(self) -> str:
        """String representation."""
        return "ContextManager(ready)"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ContextManager(memory_repository={type(self._memory_repository).__name__})"
    
    def get_available_tools_prompt(self, agent) -> str:
        """
        Generate prompt describing available tools for the agent.

        Args:
            agent: Agent instance with tool registry and capabilities

        Returns:
            Formatted string describing available tools
        """
        authorized_tools = agent._capabilities.authorized_tools

        if not authorized_tools:
            return "No tools available."

        tool_registry = agent._tool_registry
        lines = ["Available tools:"]

        for tool_name in authorized_tools:
            tool_info = tool_registry.get_tool_info(tool_name)
            if tool_info:
                # Format: - tool_name: description
                lines.append(f"- {tool_info['name']}: {tool_info['description']}")

                # Add parameters info
                if tool_info.get('parameters'):
                    params = []
                    for param in tool_info['parameters']:
                        param_name = param['name']
                        param_required = " (required)" if param.get('required') else ""
                        params.append(f"{param_name}{param_required}")
                    if params:
                        lines.append(f"  Parameters: {', '.join(params)}")

        return "\n".join(lines)
    
    def get_todolist_system_prompt(self) -> str:
        return """
You analyze user queries and return ONLY one of two responses:

1. For SIMPLE queries:
   - Greetings/Social: "Hello", "How are you?"
   - Informational/Memory: "Remember this...", "My name is...", "Keep in mind X"
   - Single direct questions: "What is 2+2?"
   - Identity changes: "Your name is now..."
   RESPONSE: No TodoList needed for this simple query.

2. For COMPLEX queries (Requiring external tools or multi-step technical workflows):
   - File manipulation, code analysis, system commands, or data processing.
   RESPONSE: RAW JSON ONLY (NO markdown).

JSON Schema:
{
  "todo_list": [
    {
      "step_id": "step_1",
      "description": "string",
      "depends_on": null | "step_n"
    },
    {
      "step_id": "step_2",
      "description": "string",
      "depends_on": step_1"
    }
  ]
}

RULES:
- STRICT JSON output only. No markdown, no prose, no ```json.
- NO conversational text before or after output.
- If the request can be fulfilled by the LLM's internal memory or knowledge without using a tool: Return "No TodoList needed".
- Do not plan "Store in memory" or "Note this" as steps.
- Max 6 steps.
- Use sequential IDs (step_1, step_2...).
- Keep descriptions clear and actionable

Examples:
User: "Hello how are you ?"
Assistant: No TodoList needed for this simple query.

User: "Analyse ce dossier"
Assistant: {"todo_list": [{"step_id": "step_1", "description": "Lister le contenu du répertoire", "depends_on": null}, {"step_id": "step_2", "description": "Lire le contenu des fichiers identifiés", "depends_on": "step_1"}, {"step_id": "step_3", "description": "Synthétiser les informations", "depends_on": "step_2"}]}
"""

    def get_agent_system_prompt(self) -> str:
        return """
JSON Schema:
{
  "steps": [
    {
      "step_number": integer,
      "description": "string",
      "actions": [
        {
          "tool_name": "string",
          "arguments": {},
          "description": "string"
        }
      ]
    },
    {
      "step_number": integer,
      "description": "string",
      "actions": [
        {
          "tool_name": "string",
          "arguments": {},
          "description": "string"
        }
      ]
    }
  ]
}

RULES:
- STRICT JSON output only. No markdown, no prose, no ```json.
- NO conversational text before or after output.
- Each step must be logically sequenced.
- Keep descriptions clear and actionable
- Only use tools listed in 'Authorized Tools'.
- 'arguments' must strictly match the tool signature.
"""
