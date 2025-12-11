# Agent Tools Configuration

Ce guide explique comment configurer les outils disponibles pour chaque agent en utilisant le système d'enum `ToolId`.

## Vue d'ensemble

Le système utilise une enum centralisée (`ToolId`) pour identifier tous les outils disponibles. Chaque agent possède une configuration qui spécifie quels outils il peut utiliser. Le `ToolsAgentManager` filtre automatiquement les appels d'outils selon cette configuration.

## Architecture

```
tools/
└── tool_ids.py          → Enum ToolId (tous les IDs d'outils)

agents/
├── config.py            → AgentConfig (contient description + tools)
└── base_agent/
    ├── agent.py         → BaseAgent.update_config()
    └── tools_manager.py → Filtrage par config
```

## Utilisation de base

### 1. Import de l'enum ToolId

```python
from tools.tool_ids import ToolId
from agents.config import AgentConfig
```

### 2. Créer une configuration avec des outils

```python
# Méthode 1: Utiliser l'enum ToolId (recommandé)
config = AgentConfig(
    name="FileAgent",
    description="Agent spécialisé dans la gestion de fichiers",
    tools=[
        ToolId.READ_FILE,
        ToolId.WRITE_FILE,
        ToolId.EDIT_FILE,
        ToolId.LIST_DIRECTORY
    ]
)

# Méthode 2: Utiliser des strings (acceptable)
config = AgentConfig(
    name="FileAgent",
    description="Agent spécialisé dans la gestion de fichiers",
    tools=["read_file", "write_file", "edit_file", "list_directory"]
)

# Méthode 3: Utiliser les helpers de ToolId
config = AgentConfig(
    name="FileAgent",
    description="Agent spécialisé dans la gestion de fichiers",
    tools=ToolId.file_tools()  # Tous les outils de fichiers
)
```

### 3. Mettre à jour la configuration d'un agent

```python
from agents.base_agent import BaseAgent
from tools.tool_ids import ToolId

# Créer un agent
agent = DefaultAgent(llm, tool_scheduler, prompt_builder, memory_manager, config)

# Mettre à jour la configuration
agent.update_config(
    description="Agent de recherche et analyse de code",
    tools=[
        ToolId.READ_FILE,
        ToolId.GREP_CONTENT,
        ToolId.CODE_SEARCH,
        ToolId.GLOB_FILES
    ]
)
```

## Catégories d'outils disponibles

### Outils de fichiers
```python
ToolId.file_tools()
# Retourne: ['read_file', 'write_file', 'edit_file', 'list_directory']
```

- `ToolId.READ_FILE` - Lire le contenu d'un fichier
- `ToolId.WRITE_FILE` - Écrire dans un fichier
- `ToolId.EDIT_FILE` - Éditer un fichier existant
- `ToolId.LIST_DIRECTORY` - Lister le contenu d'un répertoire

### Outils de recherche
```python
ToolId.search_tools()
# Retourne: ['glob_files', 'grep_content', 'code_search']
```

- `ToolId.GLOB_FILES` - Rechercher des fichiers par pattern
- `ToolId.GREP_CONTENT` - Rechercher du contenu dans des fichiers
- `ToolId.CODE_SEARCH` - Recherche avancée dans le code

### Outils Git
```python
ToolId.git_tools()
# Retourne: ['git_status', 'git_add', 'git_commit', 'git_diff', 'git_log']
```

- `ToolId.GIT_STATUS` - Statut Git
- `ToolId.GIT_ADD` - Ajouter des fichiers au staging
- `ToolId.GIT_COMMIT` - Créer un commit
- `ToolId.GIT_DIFF` - Voir les différences
- `ToolId.GIT_LOG` - Historique des commits

### Outils Shell
```python
ToolId.shell_tools()
# Retourne: ['execute_command']
```

- `ToolId.EXECUTE_COMMAND` - Exécuter une commande shell

### Outils sûrs (lecture seule)
```python
ToolId.safe_tools()
# Tous les outils en lecture seule (pas d'écriture, pas d'exécution)
```

### Outils dangereux (écriture/exécution)
```python
ToolId.dangerous_tools()
# Outils qui modifient ou exécutent
```

## Exemples de configurations d'agents

### Agent de lecture seule
```python
config = AgentConfig(
    name="ReadOnlyAgent",
    description="Agent qui ne peut que lire et analyser",
    tools=ToolId.safe_tools()
)
```

### Agent de développement complet
```python
config = AgentConfig(
    name="DevAgent",
    description="Agent de développement avec tous les outils",
    tools=ToolId.all_tools()
)
```

### Agent Git spécialisé
```python
config = AgentConfig(
    name="GitAgent",
    description="Agent spécialisé pour les opérations Git",
    tools=ToolId.git_tools() + [ToolId.READ_FILE]
)
```

### Agent personnalisé
```python
config = AgentConfig(
    name="CustomAgent",
    description="Agent avec configuration personnalisée",
    tools=[
        ToolId.READ_FILE,
        ToolId.WRITE_FILE,
        ToolId.GREP_CONTENT,
        ToolId.GIT_STATUS
    ]
)
```

## Comportement du filtrage

### Si aucun outil n'est configuré
```python
config = AgentConfig(
    name="UnrestrictedAgent",
    tools=[]  # Liste vide
)
# → L'agent peut utiliser TOUS les outils disponibles
```

### Si des outils sont configurés
```python
config = AgentConfig(
    name="RestrictedAgent",
    tools=[ToolId.READ_FILE]
)
# → L'agent ne peut utiliser QUE read_file
# → Tout autre outil sera rejeté avec un message d'erreur
```

### Exemple de rejet d'outil

Si l'agent essaie d'utiliser un outil non autorisé:

```python
# Configuration: uniquement READ_FILE
config = AgentConfig(tools=[ToolId.READ_FILE])

# L'agent essaie d'utiliser WRITE_FILE
# → ToolsAgentManager le rejette automatiquement
# → Retourne: "Error: Tool 'write_file' is not authorized for this agent.
#             Allowed tools: [read_file]"
```

## Méthodes de configuration

### AgentConfig

```python
config = AgentConfig(name="MyAgent", tools=[...])

# Vérifier si un outil est disponible
config.has_tool(ToolId.READ_FILE)  # → True/False

# Ajouter un outil
config.add_tool(ToolId.WRITE_FILE)

# Retirer un outil
config.remove_tool(ToolId.WRITE_FILE)

# Obtenir la liste des outils
tools_list = config.get_tools()  # → ['read_file', ...]

# Mettre à jour la configuration
config.update(
    description="Nouvelle description",
    tools=[ToolId.READ_FILE, ToolId.WRITE_FILE]
)
```

### BaseAgent

```python
agent = DefaultAgent(...)

# Mettre à jour la configuration
agent.update_config(
    description="Agent modifié",
    tools=[ToolId.READ_FILE]
)

# Obtenir la configuration
config = agent.get_config()
```

## Bonnes pratiques

1. **Utilisez l'enum ToolId** plutôt que des strings pour éviter les erreurs de frappe
2. **Soyez restrictif** - Ne donnez que les outils nécessaires à l'agent
3. **Documentez le rôle** - Utilisez le champ `description` pour clarifier le but de l'agent
4. **Utilisez les helpers** - `ToolId.file_tools()`, `ToolId.safe_tools()`, etc.
5. **Testez la configuration** - Vérifiez que l'agent a bien les outils dont il a besoin

## Logging

Le système log automatiquement les tentatives d'utilisation d'outils non autorisés:

```
[WARNING] [TOOLS_MANAGER] Tool 'execute_command' rejected - not in agent configuration
  {
    "agent": "RestrictedAgent",
    "allowed_tools": ["read_file", "write_file"]
  }
```

## Extension du système

Pour ajouter un nouvel outil:

1. Ajouter l'enum dans `tools/tool_ids.py`:
```python
class ToolId(str, Enum):
    # ... autres outils
    NEW_TOOL = "new_tool"
```

2. Implémenter l'outil dans `tools/implementations.py`

3. L'outil est automatiquement disponible pour configuration des agents
