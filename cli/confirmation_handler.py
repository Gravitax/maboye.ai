"""
Confirmation Handler for Dangerous Commands

Manages user confirmations for dangerous tool executions with interactive prompts.
Supports batch approval and detailed command preview.
"""

import json
from typing import Dict, Any, Optional, Set
from datetime import datetime
from core.logger import logger


class ConfirmationHandler:
    """
    Interactive confirmation handler for dangerous operations.

    Features:
    - Blocking user prompts for dangerous commands
    - Batch approval mode ("yes to all" for workflow)
    - Detailed command preview with syntax highlighting
    - Confirmation history logging
    """

    def __init__(self):
        """Initialize confirmation handler."""
        self._auto_confirm_all = False
        self._auto_confirm_tools: Set[str] = set()
        self._confirmation_history = []

    def confirm(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[str] = None
    ) -> bool:
        """
        Request user confirmation for dangerous command execution.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            context: Optional context description

        Returns:
            True if user confirmed, False otherwise
        """
        # Check auto-confirm modes
        if self._auto_confirm_all:
            self._log_confirmation(tool_name, arguments, auto_approved=True)
            return True

        if tool_name in self._auto_confirm_tools:
            self._log_confirmation(tool_name, arguments, auto_approved=True)
            return True

        # Display confirmation prompt
        print("\n" + "="*70)
        print("⚠️  CONFIRMATION REQUISE - COMMANDE DANGEREUSE")
        print("="*70)

        if context:
            print(f"\n📋 Contexte: {context}")

        print(f"\n🔧 Outil: {tool_name}")
        print(f"\n📝 Arguments:")
        print(json.dumps(arguments, indent=2, ensure_ascii=False))

        # Preview file content for edit/write operations
        self._preview_operation(tool_name, arguments)

        print("\n" + "-"*70)
        print("Options:")
        print("  [y]   Oui - Exécuter cette commande")
        print("  [n]   Non - Refuser cette commande")
        print("  [a]   Tout accepter - Oui pour TOUTES les commandes de cette session")
        print(f"  [t]   Toujours pour '{tool_name}' - Oui pour tous les '{tool_name}' de cette session")
        print("-"*70)

        while True:
            try:
                response = input("\nVotre choix [y/n/a/t]: ").strip().lower()

                if response in ['y', 'yes', 'o', 'oui']:
                    self._log_confirmation(tool_name, arguments, approved=True)
                    return True

                elif response in ['n', 'no', 'non']:
                    self._log_confirmation(tool_name, arguments, approved=False)
                    print("❌ Commande refusée par l'utilisateur.")
                    return False

                elif response == 'a':
                    self._auto_confirm_all = True
                    self._log_confirmation(tool_name, arguments, approved=True)
                    print("✅ Mode 'Tout accepter' activé pour cette session.")
                    logger.info("CONFIRMATION", "Auto-confirm ALL enabled")
                    return True

                elif response == 't':
                    self._auto_confirm_tools.add(tool_name)
                    self._log_confirmation(tool_name, arguments, approved=True)
                    print(f"✅ Auto-confirmation activée pour '{tool_name}' dans cette session.")
                    logger.info("CONFIRMATION", f"Auto-confirm enabled for {tool_name}")
                    return True

                else:
                    print("⚠️  Réponse invalide. Utilisez: y, n, a, ou t")

            except (KeyboardInterrupt, EOFError):
                print("\n❌ Interruption - Commande refusée.")
                self._log_confirmation(tool_name, arguments, approved=False)
                return False

    def _preview_operation(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """
        Display preview of file operation.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
        """
        if tool_name == "write_file":
            file_path = arguments.get("file_path", "unknown")
            content = arguments.get("content", "")
            lines = content.split('\n')
            preview_lines = lines[:10]

            print(f"\n📄 Fichier à créer/écraser: {file_path}")
            print(f"   Taille: {len(content)} caractères, {len(lines)} lignes")
            print(f"\n   Aperçu (10 premières lignes):")
            for i, line in enumerate(preview_lines, 1):
                print(f"   {i:3d} | {line[:80]}")
            if len(lines) > 10:
                print(f"   ... ({len(lines) - 10} lignes supplémentaires)")

        elif tool_name == "edit_file":
            file_path = arguments.get("file_path", "unknown")
            old_string = arguments.get("old_string", "")
            new_string = arguments.get("new_string", "")

            print(f"\n📄 Fichier à modifier: {file_path}")
            print(f"\n   🔴 Ancien texte ({len(old_string)} caractères):")
            for line in old_string.split('\n')[:5]:
                print(f"      - {line[:80]}")
            if len(old_string.split('\n')) > 5:
                print(f"      ... ({len(old_string.split('\n')) - 5} lignes)")

            print(f"\n   🟢 Nouveau texte ({len(new_string)} caractères):")
            for line in new_string.split('\n')[:5]:
                print(f"      + {line[:80]}")
            if len(new_string.split('\n')) > 5:
                print(f"      ... ({len(new_string.split('\n')) - 5} lignes)")

        elif tool_name == "execute_command" or tool_name == "bash":
            command = arguments.get("command", "unknown")
            print(f"\n💻 Commande shell à exécuter:")
            print(f"   $ {command}")

    def _log_confirmation(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        approved: bool = False,
        auto_approved: bool = False
    ) -> None:
        """
        Log confirmation decision.

        Args:
            tool_name: Tool name
            arguments: Tool arguments
            approved: Whether user approved
            auto_approved: Whether auto-approved (batch mode)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "arguments": arguments,
            "approved": approved,
            "auto_approved": auto_approved
        }
        self._confirmation_history.append(entry)

        status = "AUTO-APPROVED" if auto_approved else ("APPROVED" if approved else "DENIED")
        logger.info("CONFIRMATION", f"{status}: {tool_name}")

    def get_history(self) -> list:
        """
        Get confirmation history.

        Returns:
            List of confirmation entries
        """
        return self._confirmation_history.copy()

    def reset_auto_confirm(self) -> None:
        """Reset all auto-confirmation settings."""
        self._auto_confirm_all = False
        self._auto_confirm_tools.clear()
        logger.info("CONFIRMATION", "Auto-confirm settings reset")

    def is_auto_confirm_enabled(self) -> bool:
        """Check if auto-confirm mode is active."""
        return self._auto_confirm_all or len(self._auto_confirm_tools) > 0


# Global instance
_handler = None


def get_confirmation_handler() -> ConfirmationHandler:
    """
    Get global confirmation handler instance.

    Returns:
        ConfirmationHandler instance
    """
    global _handler
    if _handler is None:
        _handler = ConfirmationHandler()
    return _handler


def confirm_dangerous_command(
    tool_name: str,
    arguments: Dict[str, Any],
    context: Optional[str] = None
) -> bool:
    """
    Request user confirmation for dangerous command.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments
        context: Optional context description

    Returns:
        True if confirmed, False otherwise
    """
    handler = get_confirmation_handler()
    return handler.confirm(tool_name, arguments, context)
