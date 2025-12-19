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
    
    def get_available_tools_prompt(self, agent) -> str:
        """
        Génère une description riche des outils incluant types et descriptions des arguments.
        """
        authorized_tools = agent._capabilities.authorized_tools
        if not authorized_tools:
            return "No tools available."

        tool_registry = agent._tool_registry
        lines = ["\n## AVAILABLE TOOLS"]

        for tool_name in authorized_tools:
            tool_info = tool_registry.get_tool_info(tool_name)
            if tool_info:
                # Titre et description de l'outil
                lines.append(f"\n### Tool: `{tool_info['name']}`")
                lines.append(f"Description: {tool_info['description']}")

                # Détails des paramètres
                if tool_info.get('parameters'):
                    lines.append("Arguments:")
                    for param in tool_info['parameters']:
                        p_name = param['name']
                        # Gestion propre du type (si c'est une classe Python ou une string)
                        raw_type = param.get('type', 'string')
                        if isinstance(raw_type, type):
                            p_type = raw_type.__name__ # Transforme <class 'str'> en 'str'
                        else:
                            p_type = str(raw_type)

                        p_req = "required" if param.get('required') else "optional"
                        p_desc = param.get('description', '')
                        # Ajout de la valeur par défaut si elle existe (très utile pour l'agent)
                        default_info = ""
                        if 'default' in param and not param.get('required'):
                            default_info = f" (default: {param['default']})"

                        lines.append(f"  - `{p_name}` ({p_type}, {p_req}){default_info}: {p_desc}")    
        return "\n".join(lines)
    
    def get_taskslist_system_prompt(self) -> str:
        return """
You are a Senior Software Architect.
Your role is to break down the user's request into a logical sequence of actionable steps (tasks) for a Developer Agent.

OUTPUT RULES:
1. Respond ONLY in strict JSON format.
2. NO conversational text before or after the JSON.
3. Ensure all strings are properly escaped for JSON.

JSON SCHEMA:
{
  "analyse": "Brief technical analysis of the request and context.",
  "tasks": [
    "Step 1: specific objective",
    "Step 2: specific objective"
  ]
}

TASK GUIDELINES:
- ATOMICITY: Each task should be a clear, achievable objective (e.g., "Read src/main.py to understand the logic" instead of "Understand the code").
- SEQUENCE: Order tasks logically (Investigation -> Modification -> Verification).
- SCOPE: Do NOT specify exact tool calls (e.g., do not say "use read_file tool"), just state the GOAL. The Developer Agent will choose the tools.
- CONTEXT: If the user refers to specific files, mention them explicitly in the tasks.

SPECIAL CASES:
- If the request is a simple greeting or pure conversation unrelated to code/system, return an EMPTY list `[]` for "tasks".
- If the request requires knowledge retrieval (e.g., "How does auth work?"), create a task to "Inspect code to explain authentication mechanism".
"""

    def get_execution_system_prompt(self) -> str:
        return """
You are an autonomous execution agent.
Your goal is to complete the specific task assigned strictly, without deviating.

EXECUTION RULES:
1. Analyze the current context and previous tool outputs.
2. STRICT SCOPE: Do NOT invent new steps. If asked to "list files", ONLY list files. Do NOT read them unless explicitly asked.
3. STOPPING CONDITION: If the previous tool output contains the requested information or completes the action, you MUST use the "task_completed" tool immediately.
4. FORMAT: Return ONLY the raw JSON object. Do NOT wrap it in markdown code blocks (like ```json). Do NOT add conversational text.

JSON SCHEMA:
{
  "tool_name": "exact_name_of_the_tool",
  "arguments": {
    "arg_name": "value" // Ensure value matches the expected type (int, string, bool)
  }
}
"""
