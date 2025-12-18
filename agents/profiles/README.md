# Agent Profiles
 
## format.json
{
    "name": "Lorem Ipsunm.",
    "description": "Lorem Ipsunm.",
    "authorized_tools": [],
    "system_prompt": "Lorem Ipsunm."
    "max_reasoning_turns": 2,
    "max_memory_turns": 2,
    "specialization_tags": [
        "execution"
    ],
    "llm_config": {
        "temperature": 0,
        "max_tokens": 1000,
        "timeout": 30
    }
}

Le système utilise une enum centralisée (`ToolId`) pour identifier tous les outils disponibles.
Chaque agent possède une configuration qui spécifie quels outils il peut utiliser.

## Méthode 1: Utiliser l'enum ToolId
tools=[ 
    ToolId.READ_FILE,
    ToolId.WRITE_FILE,
    ToolId.EDIT_FILE,
    ToolId.LIST_DIRECTORY
]
 
## Méthode 2: Utiliser des strings
tools=["read_file", "write_file", "edit_file", "list_directory"]
 
## No tools
tools=[]
