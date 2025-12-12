# Domain Layer

Le Domain Layer contient les entités métier et Value Objects du système multi-agents. C'est le cœur de la logique métier, complètement indépendant de l'infrastructure.

## Principes

- **Immutabilité** : Les Value Objects sont frozen (immuables)
- **Validation stricte** : Tous les objets se valident dans `__post_init__()`
- **Indépendance** : Aucune dépendance vers les couches supérieures
- **Type safety** : Utilisation extensive des type hints

## Fichiers

### Value Objects (Immuables)

#### `agent_identity.py` (152 lignes)
**Identité unique d'un agent**

Représente l'identité immuable et unique d'un agent dans le système.

**Attributs:**
- `agent_id`: UUID v4 unique
- `agent_name`: Nom unique et lisible (ex: "CodeAgent")
- `creation_timestamp`: Date de création

**Validation:**
- UUID v4 valide obligatoire
- Nom doit matcher le pattern `^[a-zA-Z][a-zA-Z0-9_]{2,49}$`
- Nom entre 3 et 50 caractères
- Timestamp ne peut pas être dans le futur

**Factory method:**
```python
identity = AgentIdentity.create_new("CodeAgent")
```

---

#### `agent_capabilities.py` (237 lignes)
**Capacités et contraintes d'un agent**

Définit ce qu'un agent peut faire et ses limites opérationnelles.

**Attributs:**
- `description`: Rôle et objectif de l'agent (10-500 caractères)
- `authorized_tools`: Liste des IDs d'outils autorisés
- `max_reasoning_turns`: Nombre maximum d'itérations de raisonnement (1-100)
- `max_memory_turns`: Nombre maximum de tours en mémoire (1-1000)
- `specialization_tags`: Tags de spécialisation (ex: ["code", "git"])

**Validation:**
- Description non vide et dans les limites
- Liste d'outils sans doublons
- Limites de tours dans les ranges valides
- Tags sans doublons et < 50 caractères

**Méthodes principales:**
```python
capabilities.can_use_tool("read_file")      # Vérifie autorisation
capabilities.has_specialization("code")     # Vérifie spécialisation
capabilities.is_unrestricted()              # Vérifie accès total
```

---

#### `conversation_context.py` (218 lignes)
**Snapshot immuable d'une conversation**

Capture l'état complet d'une conversation à un moment donné.

**Attributs:**
- `agent_identity`: Identité de l'agent propriétaire
- `conversation_history`: Liste des tours de conversation
- `context_metadata`: Métadonnées additionnelles
- `created_at`: Timestamp de création du snapshot

**Validation:**
- Identité valide (AgentIdentity)
- Historique est une liste de dicts
- Chaque tour a 'role' et 'content'
- Métadonnées est un dict

**Factory method:**
```python
context = ConversationContext.create_from_memory(
    agent_identity=identity,
    memory_manager=memory,
    max_turns=10
)
```

**Méthodes utiles:**
```python
context.get_turn_count()          # Nombre de tours
context.get_last_turn()           # Dernier tour
context.get_user_turns()          # Uniquement tours utilisateur
context.get_assistant_turns()     # Uniquement tours assistant
context.is_empty()                # Vérifie si vide
```

---

#### `cross_agent_context.py` (264 lignes)
**Contexte partagé entre plusieurs agents**

Capture les contextes de plusieurs agents pour la collaboration inter-agents.

**Attributs:**
- `requesting_agent_id`: ID de l'agent demandeur
- `shared_contexts`: Liste de ConversationContext d'autres agents
- `context_metadata`: Métadonnées sur le partage
- `created_at`: Timestamp de création

**Validation:**
- Agent demandeur non vide
- Contextes partagés sont des ConversationContext valides
- Métadonnées est un dict

**Factory method:**
```python
cross_context = CrossAgentContext.create_from_agents(
    requesting_agent_id="agent-123",
    agent_contexts=[context1, context2],
    metadata={'purpose': 'collaboration'}
)
```

**Méthodes de recherche:**
```python
cross_context.get_context_by_agent_id("agent-456")
cross_context.get_context_by_agent_name("CodeAgent")
cross_context.get_all_agent_identities()
cross_context.has_context_from_agent("agent-456")
```

**Métriques:**
```python
cross_context.get_total_turns_across_agents()
cross_context.get_shared_agent_count()
cross_context.is_empty()
```

---

### Entities (Mutables)

#### `registered_agent.py` (327 lignes)
**Agent enregistré dans le système avec lifecycle**

Entité mutable représentant un agent avec son cycle de vie complet.

**Attributs:**
- `agent_identity`: Identité immuable (AgentIdentity)
- `agent_capabilities`: Capacités (AgentCapabilities)
- `system_prompt`: Prompt système définissant le comportement (10-5000 chars)
- `is_active`: État actif/inactif de l'agent
- `created_at`: Date de création
- `updated_at`: Date de dernière modification
- `metadata`: Métadonnées additionnelles

**Validation:**
- Identité et capacités valides
- System prompt entre 10 et 5000 caractères
- updated_at >= created_at

**Factory method:**
```python
agent = RegisteredAgent.create_new(
    name="CodeAgent",
    description="Agent spécialisé en code",
    authorized_tools=["read_file", "write_file"],
    system_prompt="You are a code analysis assistant..."
)
```

**Méthodes de modification:**
```python
agent.update_capabilities(new_capabilities)
agent.update_system_prompt(new_prompt)
agent.activate()
agent.deactivate()
agent.update_metadata("key", "value")
```

**Accesseurs:**
```python
agent.get_agent_id()
agent.get_agent_name()
agent.get_description()
agent.get_authorized_tools()
agent.can_use_tool("read_file")
```

---

## Patterns utilisés

### Value Object Pattern
- **Immutabilité** : `@dataclass(frozen=True)`
- **Auto-validation** : Validation dans `__post_init__()`
- **Égalité par valeur** : Comparaison automatique par contenu

### Entity Pattern
- **Identité** : Un agent est identifié par son ID, pas par ses attributs
- **Mutabilité contrôlée** : Méthodes dédiées pour modifications
- **Lifecycle** : Gestion de l'état (active/inactive, created/updated)

### Factory Pattern
- Méthodes `create_new()` pour création simplifiée
- Méthodes `create_from_*()` pour construction depuis sources externes

## Usage

```python
from core.domain import (
    AgentIdentity,
    AgentCapabilities,
    ConversationContext,
    CrossAgentContext,
    RegisteredAgent
)

# Créer une identité
identity = AgentIdentity.create_new("CodeAgent")

# Créer des capacités
capabilities = AgentCapabilities(
    description="Agent spécialisé en code",
    authorized_tools=["read_file", "write_file"],
    max_reasoning_turns=10,
    max_memory_turns=10,
    specialization_tags=["code", "files"]
)

# Créer un agent
agent = RegisteredAgent.create_new(
    name="CodeAgent",
    description="Agent spécialisé en code",
    authorized_tools=["read_file", "write_file"],
    system_prompt="You are a code analysis assistant..."
)
```

## Avantages

1. **Type Safety** - Validation stricte des données métier
2. **Immutabilité** - Évite les bugs de modification accidentelle
3. **Testabilité** - Objets simples à tester unitairement
4. **Documentation** - Les types documentent l'usage
5. **Indépendance** - Pas de dépendances externes
