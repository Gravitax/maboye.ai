"""
Agent Execution Coordinator

Manages single-command execution workflow for agents.
Handles LLM querying, command parsing, and tool execution.
Includes retry logic for JSON syntax errors and robust security checks.
"""

import json
import re
from typing import Optional, Dict, Any, Callable, List, TYPE_CHECKING
from core.logger import logger
from core.tool_scheduler import ToolScheduler
from core.services.context_manager import ContextManager
from agents.types import AgentOutput, ToolCall
from tools.tool_ids import ToolId

if TYPE_CHECKING:
    from agents.agent import Agent

# Regex pour détecter les commandes destructrices dans les arguments bash
DANGEROUS_BASH_REGEX = re.compile(r'(^|[;\s|&])(rm|del|rmdir|mv|rename)(\s+|$)', re.IGNORECASE)

class TaskExecution:
    """
    Coordonne l'exécution d'une commande unique.
    Intègre une logique de 'Retry' pour les erreurs de syntaxe JSON et une abstraction des confirmations utilisateur.
    """

    def __init__(
        self,
        llm,
        tool_scheduler: ToolScheduler,
        context_manager: ContextManager,
        interaction_handler: Optional[Callable[[str, Dict], bool]] = None
    ):
        """
        Args:
            interaction_handler: Callback (msg, args) -> bool pour confirmer les actions dangereuses.
                                 Si None, utilise input() console par défaut.
        """
        self._llm = llm
        self._tool_scheduler = tool_scheduler
        self._context_manager = context_manager
        self._interaction_handler = interaction_handler or self._default_console_confirmation

    def __call__(
        self,
        agent: "Agent",
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 1
    ) -> AgentOutput:
        """
        Exécute le workflow avec tentative de récupération en cas d'erreur de format.
        """
        agent_id = agent.get_identity().agent_id
        capabilities = agent.get_capabilities()

        # Construction du contexte initial
        messages = self._context_manager.build_messages(
            agent_id=agent_id,
            system_prompt=system_prompt,
            max_turns=capabilities.max_memory_turns
        )

        if len(user_prompt) > 0:
            messages.append({"role": "user", "content": user_prompt})

        # Boucle de tentative (Retry Loop) pour corriger les erreurs de syntaxe JSON
        current_retries = 0
        
        while current_retries <= max_retries:
            logger.info("AGENT", "task_attempt", f"Try {current_retries + 1}/{max_retries + 1}")
            user_messages = [msg for msg in messages if msg['role'] == "user" or msg['role'] == "assistant"]
            logger.agent("AGENT", "input", user_messages)

            # Appel LLM
            llm_response = self._llm.chat(
                messages,
                verbose=True,
                temperature=capabilities.llm_temperature,
                max_tokens=capabilities.llm_max_tokens,
                response_format=capabilities.llm_response_format
            )

            message = llm_response.choices[0].message if llm_response.choices else None
            if not message or not message.content:
                return AgentOutput(
                    response="Error: Empty response from LLM",
                    success=False,
                    error="empty_llm_response",
                    cmd="error"
                )

            content = message.content
            
            # Parsing de la commande
            tool_command = self._parse_tool_command(content)

            # Cas : JSON invalide ou introuvable
            if not tool_command:
                # Si c'est juste du texte sans intention d'outil, on retourne le texte
                # Mais si le modèle *essayait* de faire du JSON (détecté par accolades), on retry
                if "{" in content and "}" in content:
                    error_msg = "Invalid JSON format. Return ONLY raw JSON."
                    logger.warning("AGENT", "LLM_RAW_OUTPUT_FAILED_PARSE", {"raw_output": content})
                    logger.warning("AGENT", "json_parse_error", "Retrying...")
                    
                    # On ajoute l'erreur au contexte temporaire pour que le LLM se corrige
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": f"System Error: {error_msg}"})
                    current_retries += 1
                    continue
                else:
                    # Réponse conversationnelle simple
                    return AgentOutput(
                        response=content,
                        success=True,
                        cmd=ToolId.TASK_SUCCESS.value, # Treat direct response as completion
                        log="Direct text response"
                    )

            # Extraction et Validation
            tool_name = tool_command.get("tool_name")
            arguments = tool_command.get("arguments", {})

            # Si on a du JSON valide mais pas de tool_name, c'est une réponse structurée (ex: Plan)
            # On considère ça comme un succès conversationnel/données.
            if not tool_name:
                return AgentOutput(
                    response=json.dumps(tool_command, indent=2), # On renvoie le JSON propre
                    success=True,
                    cmd=ToolId.TASK_SUCCESS.value,
                    log="Structured JSON response received (Plan/Data)."
                )

            # Vérification de Sécurité
            if self._is_dangerous_command(tool_name, arguments):
                confirmed = self._interaction_handler(tool_name, arguments)
                if not confirmed:
                    return AgentOutput(
                        response=f"Action '{tool_name}' denied by user.",
                        success=False,
                        error="user_denied",
                        cmd=tool_name
                    )

            # Exécution de l'outil via le Scheduler
            tool_call = ToolCall(
                id=f"{tool_name}-{agent_id}",
                name=tool_name,
                args=arguments
            )
            
            try:
                # Le Scheduler gère la validation des types, l'exécution et le formatage
                tool_results = self._tool_scheduler.execute_tools([tool_call])
                result = tool_results[0]
                
                # Traitement du résultat (qui peut être un Dict ou un Str)
                result_data = result.get("result")
                is_scheduler_success = result.get("success", False)
                
                # Détermination du succès métier (command failed vs tool crash)
                command_success = is_scheduler_success
                if isinstance(result_data, dict) and "success" in result_data:
                     command_success = result_data.get("success", True)

                # Gestion spécifique de task_success ou task_error
                if tool_name == ToolId.TASK_SUCCESS.value and command_success:
                    final_msg = "Task completed successfully."
                    if isinstance(result_data, dict):
                        final_msg = result_data.get("message", final_msg)
                    elif isinstance(result_data, str):
                        final_msg = result_data
                        
                    return AgentOutput(
                        response=final_msg,
                        success=True,
                        cmd=ToolId.TASK_SUCCESS.value,
                        args=arguments,
                        log="Objective reached via tool execution."
                    )
                elif tool_name == ToolId.TASK_ERROR.value:
                    error_msg = "Task failed as declared by agent."
                    if isinstance(result_data, dict):
                        error_msg = result_data.get("error_message", error_msg)
                    elif isinstance(result_data, str):
                        error_msg = result_data

                    return AgentOutput(
                        response=error_msg,
                        success=False,
                        error="agent_declared_error",
                        cmd=ToolId.TASK_ERROR.value,
                        args=arguments,
                        log=f"Agent declared task error: {error_msg}"
                    )

                # Conversion du résultat en string pour l'AgentOutput si c'est un dict
                response_str = str(result_data) if not isinstance(result_data, str) else result_data

                return AgentOutput(
                    response=response_str,
                    success=command_success,
                    cmd=tool_name,
                    args=arguments,
                    log=f"Tool {tool_name} executed. Success: {command_success}"
                )

            except Exception as e:
                logger.error("EXEC_ERR", f"Unhandled exception in TaskExecution for {tool_name}", str(e))
                return AgentOutput(
                    response=f"Internal Tool Error: {str(e)}",
                    success=False,
                    error="tool_exception",
                    cmd=tool_name
                )

        # Fin de la boucle de retry sans succès
        return AgentOutput(
            response="Failed to generate valid JSON command after retries.",
            success=False,
            error="max_retries_exceeded",
            cmd="json_error"
        )

    def _parse_tool_command(self, content: str) -> Optional[Dict[str, Any]]:
        """Tente d'extraire le JSON de manière agressive."""
        try:
            # Nettoyage des balises markdown
            cleaned = re.sub(r'^```(json)?|```$', '', content.strip(), flags=re.MULTILINE).strip()
            
            # Recherche du premier '{' et dernier '}'
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            
            if start != -1 and end != -1:
                json_str = cleaned[start:end+1]
                data = json.loads(json_str)
                
                # Gestion des structures imbriquées courantes
                if "tool_name" in data:
                    return data
                elif "function" in data and "name" in data["function"]:
                    # Support format OpenAI functions
                    return {
                        "tool_name": data["function"]["name"],
                        "arguments": json.loads(data["function"]["arguments"]) if isinstance(data["function"]["arguments"], str) else data["function"]["arguments"]
                    }
                
                # Si c'est un JSON valide mais pas une commande d'outil explicite
                # (ex: le plan du TasksAgent), on le retourne tel quel.
                # L'appelant décidera si c'est valide ou non.
                return data

            return None
        except Exception:
            return None

    def _is_dangerous_command(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Vérifie la dangerosité via ToolId et Regex."""
        # 1. Vérification via la liste centralisée des outils dangereux
        dangerous_tools = ToolId.dangerous_tools()
        
        if tool_name in dangerous_tools:
            # Cas spécial Bash: on analyse la commande interne
            if tool_name == ToolId.EXECUTE_COMMAND.value or tool_name == "bash": # Support legacy alias
                cmd = arguments.get("command", "")
                if DANGEROUS_BASH_REGEX.search(cmd):
                    logger.warning("SECURITY", "Dangerous Bash Pattern", cmd)
                    return True
                # Si c'est juste "ls" ou "echo", on peut considérer safe,
                # mais par défaut EXECUTE_COMMAND est classé dangereux. 
                # On retourne True pour forcer la confirmation sauf whitelist explicite (optionnel)
                return True
            
            return True
            
        return False

    def _default_console_confirmation(self, tool_name: str, arguments: Dict) -> bool:
        """Fallback pour utilisation console."""
        print(f"\n⚠️  CONFIRMATION REQUISE : {tool_name}")
        print(json.dumps(arguments, indent=2))
        res = input("Exécuter ? (y/n): ").strip().lower()
        return res in ['y', 'yes']
