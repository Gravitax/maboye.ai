"""
Context Manager

Manages conversation context retrieval and message formatting for LLM.
Serves both orchestrator and agents.
"""

import platform
import sys
import os
import fnmatch

from typing import List, Dict, Any, Optional
from datetime import datetime
from core.repositories.memory_repository import MemoryRepository
from core.logger import logger
from tools.tool_ids import ToolId


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
        return "-"
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

        lines = []
        for turn in turns:
            role = turn.get("role", "unknown")
            content = turn.get("content", "")
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
        # Create a list copy to safely modify
        tools_to_display = list(agent._capabilities.authorized_tools) if agent._capabilities.authorized_tools else []
        
        
        # Ensure task_success and task_error are always displayed
        if ToolId.TASK_SUCCESS.value not in tools_to_display:
            tools_to_display.append(ToolId.TASK_SUCCESS.value)
        if ToolId.TASK_ERROR.value not in tools_to_display:
            tools_to_display.append(ToolId.TASK_ERROR.value)
        if ToolId.TASKS_COMPLETED.value not in tools_to_display:
            tools_to_display.append(ToolId.TASKS_COMPLETED.value)

        if not tools_to_display:
            return "No tools available."

        tool_registry = agent._tool_registry
        lines = ["## AVAILABLE TOOLS"]

        for tool_name in tools_to_display:
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
                
                # Special note for task_success
                if tool_name == ToolId.TASKS_COMPLETED.value:
                    lines.append("NOTE: Use this tool immediately when the **USER QUERY is COMPLETE**.")
                if tool_name == ToolId.TASK_SUCCESS.value:
                    lines.append("NOTE: Use this tool **IMMEDIATELY** when the **CURRENT TASK's OBJECTIVE is FULLY ACHIEVED**.")
                elif tool_name == ToolId.TASK_ERROR.value:
                    lines.append("NOTE: Use this tool **IMMEDIATELY** when an unrecoverable **ERROR PREVENTS TASK COMPLETION**.")

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
    {
      "step": "Clear and specific action to perform.",
      "expected_outcome": "Concrete condition or result that must be met to consider this step complete and enable the next."
    },
    {
      "step": "Next action...",
      "expected_outcome": "Result..."
    }
  ]
}

TASK GUIDELINES:
- ATOMICITY: Each task should be a clear, achievable objective (e.g., "Read src/main.py to understand the logic" instead of "Understand the code").
- SEQUENCE: Order tasks logically (Investigation -> Modification -> Verification).
- SCOPE: Do NOT specify exact tool calls (e.g., do not say "use read_file tool"), just state the GOAL. The Developer Agent will choose the tools.
- CONTEXT: If the user refers to specific files, mention them explicitly in the tasks.
- OUTCOMES: The `expected_outcome` must be verifiable (e.g., \"File path is confirmed\" is better than \"Know where the file is\").

SPECIAL CASES:
- If the request is a simple greeting or pure conversation unrelated to code/system, return an EMPTY list `[]` for "tasks".
- If the request requires knowledge retrieval (e.g., "How does auth work?"), create a task to "Inspect code to explain authentication mechanism".
"""

    def get_verification_prompt(self) -> str:
        return f"""
VERIFICATION REQUIRED (Check strictly in this order):\n"
1. **GLOBAL COMPLETION (HIGHEST PRIORITY)**: Look at the output/context. If the evidence shows the **USER QUERY is FULLY ACHIEVED** (regardless of whether the specific command succeeded or failed), use **{ToolId.TASKS_COMPLETED.value}** IMMEDIATELY.
2. **IMPLICIT SUCCESS (IDEMPOTENCY)**: If the command failed (exit code != 0) BUT the output implies the target state already exists (e.g., 'already exists', 'nothing to change', 'same source/dest'), consider the task done. Use **{ToolId.TASK_SUCCESS.value}**.
3. **STEP SUCCESS**: If the output confirms the current task's objective is met, use **{ToolId.TASK_SUCCESS.value}**.
4. **FATAL**: Only use **{ToolId.TASK_ERROR.value}** if the goal is blocked and strictly impossible to achieve.
        """

    def get_execution_system_prompt(self) -> str:
        return f"""
You are an autonomous execution agent.
Your goal is to complete the specific task assigned, BUT your ultimate priority is the USER QUERY.

EXECUTION RULES:
1. **PRIORITY 0: GLOBAL SHORT-CIRCUIT**: 
   Before doing anything, ask: "Is the USER QUERY already fully achieved based on the context/history?"
   - If YES -> Use **{ToolId.TASKS_COMPLETED.value}** IMMEDIATELY. Ignore the current task.
   - Do not perform unnecessary actions if the final goal is met.
2. **ANALYSIS**: Analyze the current context and the specific 'Expected Outcome' of the task.
3. **OBJECTIVE**: Your goal is the RESULT, not the ACTION. 
   - If the task asks to "Move X", but X is already there -> Success.
   - If the task asks to "Create Y", but Y exists -> Success.
4. **VERIFICATION**: Compare tool outputs against the goal.
   - Treat "Resource already exists" or "No changes made" as SUCCESS.
5. **STOPPING CONDITION**: 
   - Use **{ToolId.TASK_SUCCESS.value}** when the current step is done.
   - Use **{ToolId.TASKS_COMPLETED.value}** when the User Query is done.
6. **FORMAT**: Return ONLY the raw JSON object.

JSON SCHEMA:
{{
  "tool_name": "exact_name_of_the_tool",
  "arguments": {{
    "arg_name": "value"
  }}
}}
"""

    def get_environment_variables_prompt(self) -> str:
            """
            Génère une section listant l'OS, la version Python et les variables d'environnement sûres.
            """

            lines = ["## ENVIRONMENT CONTEXT"]

            # 1. Informations Système (OS & Python)
            os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
            python_info = f"Python {sys.version.split()[0]}"
            
            lines.append("### System Information")
            lines.append(f"- **OS:** {os_info}")
            lines.append(f"- **Runtime:** {python_info}")
            lines.append(f"- **CWD:** {os.getcwd()}") # Current Working Directory est crucial

            # 2. Variables d'environnement (Filtrées)
            safe_env_vars = ["HOME", "PATH", "LANG", "TERM", "USER", "SHELL"]
            
            env_lines = []
            for key in safe_env_vars:
                value = os.getenv(key)
                if value:
                    # On tronque les valeurs trop longues (ex: PATH) pour économiser des tokens
                    if len(value) > 200: 
                        value = value[:197] + "..."
                    env_lines.append(f"- `{key}`: `{value}`")

            if env_lines:
                lines.append("\n### Active Environment Variables")
                lines.extend(env_lines)

            return "\n".join(lines)

    def _get_gitignore_patterns(self) -> list[str]:
            """
            Lit et parse le fichier .gitignore local.
            Retourne une liste de patterns nettoyés.
            """
            
            patterns = []
            gitignore_path = ".gitignore"

            if not os.path.exists(gitignore_path):
                return patterns

            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # On ignore les lignes vides et les commentaires
                        if not line or line.startswith("#"):
                            continue
                        
                        # Nettoyage pour faciliter le match avec fnmatch :
                        # On retire le slash final (ex: "dist/" -> "dist")
                        # car os.walk retourne les noms de dossiers sans slash.
                        clean_pattern = line.rstrip("/")
                        patterns.append(clean_pattern)
                        
            except Exception as e:
                # En cas d'erreur (droits, encodage), on échoue silencieusement
                # pour ne pas bloquer l'agent.
                pass

            return patterns

    def get_project_structure_prompt(self) -> str:
            # 1. Chargement des exclusions
            # Liste de sécurité (toujours ignorée)
            ALWAYS_IGNORE = {'.git', '__pycache__', '.idea', '.vscode', '.DS_Store', 'venv', '.venv', '.env'}
            
            # Récupération dynamique depuis .gitignore
            gitignore_patterns = self._get_gitignore_patterns()

            def should_ignore(name):
                """Vérifie si un fichier/dossier doit être ignoré."""
                # Vérification rapide (exact match)
                if name in ALWAYS_IGNORE:
                    return True
                
                # Vérification des patterns .gitignore
                for pattern in gitignore_patterns:
                    if fnmatch.fnmatch(name, pattern):
                        return True
                return False

            # 2. Construction de l'arbre
            MAX_DEPTH = 2
            lines = ["## PROJECT STRUCTURE"]
            lines.append(f"(Root: {os.getcwd()})")

            start_path = "."
            
            for root, dirs, files in os.walk(start_path):
                level = root.replace(start_path, '').count(os.sep)
                
                if level > MAX_DEPTH:
                    continue

                # Élagage des dossiers ignorés (modification in-place de dirs)
                # Cela empêche os.walk de descendre inutilement
                dirs[:] = [d for d in dirs if not d.startswith('.') and not should_ignore(d)]
                
                # Affichage du dossier
                indent = "  " * level
                folder_name = os.path.basename(root)
                if folder_name == ".": 
                    folder_name = "/"
                
                lines.append(f"{indent}{folder_name}/")
                
                # Affichage des fichiers
                subindent = "  " * (level + 1)
                for f in files:
                    if not f.startswith('.') and not should_ignore(f):
                        lines.append(f"{subindent}{f}")

            return "\n".join(lines)

    def build_system_prompt(self, agent):
        parts = [
            self.get_available_tools_prompt(agent),
            self.get_environment_variables_prompt(),
            self.get_project_structure_prompt()
        ]
        return "\n\n".join(parts)
