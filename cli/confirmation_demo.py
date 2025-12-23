"""
Demonstration of the Confirmation Handler

Shows how the interactive confirmation system works for dangerous commands.
"""

from cli.confirmation_handler import get_confirmation_handler


def demo_confirmation_workflow():
    """Demonstrate the confirmation workflow."""

    print("="*70)
    print("DEMO: Système de Confirmation pour Commandes Dangereuses")
    print("="*70)

    handler = get_confirmation_handler()

    # Simulate dangerous commands
    test_commands = [
        {
            "tool": "write_file",
            "args": {
                "file_path": "app.py",
                "content": "print('Hello World')\n"
            },
            "context": "Création du fichier principal de l'application"
        },
        {
            "tool": "edit_file",
            "args": {
                "file_path": "config.yaml",
                "old_string": "debug: false",
                "new_string": "debug: true"
            },
            "context": "Activation du mode debug"
        },
        {
            "tool": "execute_command",
            "args": {
                "command": "pip install -r requirements.txt"
            },
            "context": "Installation des dépendances"
        }
    ]

    print("\nSimulation de 3 commandes dangereuses...")
    print("Vous pouvez utiliser:")
    print("  - 'y' pour accepter une commande")
    print("  - 'n' pour refuser une commande")
    print("  - 'a' pour accepter TOUTES les commandes de cette session")
    print("  - 't' pour accepter toutes les commandes d'un même type")
    print()

    for i, cmd in enumerate(test_commands, 1):
        print(f"\n--- Commande {i}/{len(test_commands)} ---")

        approved = handler.confirm(
            tool_name=cmd["tool"],
            arguments=cmd["args"],
            context=cmd["context"]
        )

        if approved:
            print(f"✅ Commande {cmd['tool']} exécutée")
        else:
            print(f"❌ Commande {cmd['tool']} refusée")

    print("\n" + "="*70)
    print("Historique des confirmations:")
    print("="*70)

    for entry in handler.get_history():
        status = "AUTO-APPROVED" if entry["auto_approved"] else ("APPROVED" if entry["approved"] else "DENIED")
        print(f"{entry['timestamp']} | {entry['tool_name']:20s} | {status}")

    print("\n" + "="*70)
    print("DEMO terminée")
    print("="*70)


if __name__ == "__main__":
    demo_confirmation_workflow()
