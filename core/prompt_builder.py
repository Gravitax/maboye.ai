"""
Prompt Builder for Agent System

Provides functionality to construct complex prompts for the LLM, including
system messages, tool descriptions, and conversation history.
"""

from typing import List

from core.logger import logger
from tools.tool_base import ToolRegistry
from agents.types import Message


class PromptBuilder:
    """
    Constructs and formats prompts for the LLM.
    """

    def __init__(self, system_prompt: str, tool_registry: ToolRegistry):
        """
        Initializes the PromptBuilder.

        Args:
            system_prompt: The base system prompt (role and instructions).
            tool_registry: The registry containing available tools.
        """
        self._system_prompt = system_prompt
        self._tool_registry = tool_registry

    def build_from_history(self, history: List[Message]) -> List[Message]:
        """
        Builds the full list of messages for the LLM from a conversation history.

        Args:
            history: The conversation history from a Memory source.

        Returns:
            A list of messages ready to be sent to the LLM, with the system
            prompt prepended and history messages following.
        """
        logger.info(
            "PROMPT_BUILDER",
            f"Building context from {len(history)} history messages"
        )

        messages: List[Message] = []

        # 1. Add the system prompt, including tool descriptions
        full_system_prompt = self._system_prompt + "\n\n" + self._get_tools_prompt()
        system_message = {"role": "system", "content": full_system_prompt}
        messages.append(system_message)

        self._log_system_prompt(full_system_prompt)

        # 2. Add the conversation history (alternating user/assistant)
        messages.extend(history)
        self._log_history_messages(history)

        self._log_final_context(messages)
        return messages

    def _get_tools_prompt(self) -> str:
        """
        Generates the tool description part of the system prompt.

        Formats the metadata of all registered tools in a way that the LLM
        can understand and use.

        Returns:
            A string describing the available tools.
        """
        tool_infos = self._tool_registry.get_all_tools_info()

        if not tool_infos:
            return "No tools are available."

        prompt_lines = [
            "You have access to the following tools. To use a tool, you must respond with a JSON object in the specified format.",
            "Example of a tool call:",
            "```json",
            '{ "tool_calls": [{ "id": "call_123", "name": "tool_name", "args": {"arg1": "value1"} }] }',
            "```",
            "\nAvailable Tools:",
        ]

        for tool_info in tool_infos:
            params_str_list = []
            for param in tool_info.get("parameters", []):
                param_type = param.get('type', 'any')
                required_str = "required" if param.get('required') else "optional"
                params_str_list.append(
                    f"    - {param['name']} ({param_type}, {required_str}): {param['description']}"
                )
            params_str = "\n".join(params_str_list)
            tool_str = (
                f"\n- Tool: `{tool_info['name']}`\n"
                f"  Description: {tool_info['description']}\n"
                f"  Parameters:\n{params_str}"
            )
            prompt_lines.append(tool_str)

        return "\n".join(prompt_lines)

    def _log_system_prompt(self, system_prompt: str) -> None:
        """Logs system prompt details."""
        preview = system_prompt[:300] + "..." if len(system_prompt) > 300 else system_prompt
        logger.info(
            "PROMPT_BUILDER",
            "System prompt constructed",
            {
                "length": len(system_prompt),
                "preview": preview
            }
        )

    def _log_history_messages(self, history: List[Message]) -> None:
        """Logs conversation history messages."""
        logger.info(
            "PROMPT_BUILDER",
            f"Adding {len(history)} messages from history"
        )

        for idx, msg in enumerate(history):
            content = msg.get("content", "")
            content_preview = content[:150] if content else "[no content]"

            logger.debug(
                "PROMPT_BUILDER",
                f"History message {idx + 1}/{len(history)}",
                {
                    "role": msg["role"],
                    "content_length": len(content) if content else 0,
                    "content_preview": content_preview,
                    "has_tool_calls": "tool_calls" in msg
                }
            )

    def _log_final_context(self, messages: List[Message]) -> None:
        """Logs final context summary."""
        role_counts = {}
        for msg in messages:
            role = msg["role"]
            role_counts[role] = role_counts.get(role, 0) + 1

        logger.info(
            "PROMPT_BUILDER",
            f"Final context built with {len(messages)} messages",
            {
                "total_messages": len(messages),
                "by_role": role_counts
            }
        )
