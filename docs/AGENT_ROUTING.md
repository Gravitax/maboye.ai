# Agent Routing - Option B

## Vue d'ensemble

L'**Option B** permet de router automatiquement les tâches vers des agents spécialisés au lieu d'utiliser un seul `MockAgent` pour tout.

## Concept

### Avant (Actuel - MockAgent)
```
User: "commit my changes"
    ↓
MockAgent (agent générique de test)
    ↓
Résultat générique
```

### Après (Option B - Routing)
```
User: "commit my changes"
    ↓
Router analyse "commit" → détecte Git
    ↓
GitAgent (expert git avec git_status, git_add, git_commit)
    ↓
Décomposition optimale en commandes git
    ↓
Résultat précis
```

## Exemples de routing

| Description de tâche | Agent routé | Pourquoi |
|---------------------|-------------|----------|
| "commit changes with message 'fix'" | **GitAgent** | Mots-clés: commit, git |
| "list files in /tmp" | **BashAgent** | Mots-clés: list, files, shell |
| "create python script hello.py" | **PythonAgent** | Mots-clés: python, script |
| "hello, how are you?" | **DefaultAgent** | Pas de mots-clés techniques |

## Bénéfices

1. **Agents spécialisés** : Chaque agent connait son domaine
2. **Outils adaptés** : GitAgent a git_status, BashAgent a bash, etc.
3. **Caching** : AgentFactory garde les instances en cache
4. **Prompts optimisés** : Chaque agent a son prompt spécialisé

## Comment activer

### Étape 1 : Décommenter dans `orchestrator.py`

Ligne ~100-110 :
```python
# Décommenter ces lignes :
from core.services import AgentFactory
self._agent_factory = AgentFactory(
    llm=self._llm,
    tool_scheduler=self._tool_scheduler,
    tool_registry=self._tool_registry,
    memory=self._memory_manager
)
```

Ligne ~113-121 :
```python
# Décommenter ces paramètres :
self._execution_manager = ExecutionManager(
    llm=self._llm,
    tool_scheduler=self._tool_scheduler,
    tool_registry=self._tool_registry,
    memory_manager=self._memory_manager,
    context_manager=self._context_manager,
    agent_factory=self._agent_factory,  # ← Décommenter
    agent_repository=self._agent_repository  # ← Décommenter
)
```

### Étape 2 : Décommenter dans `execution_manager.py`

Ligne ~29-30 (dans `__init__`) :
```python
# Décommenter ces lignes :
agent_factory=None,
agent_repository=None
```

Ligne ~51-52 :
```python
# Décommenter ces lignes :
self._agent_factory = agent_factory
self._agent_repository = agent_repository
```

Ligne ~210-243 (méthode `_route_to_agent`) :
```python
# Décommenter toute la méthode _route_to_agent
```

Ligne ~274-282 (dans `_execute_step`) :
```python
# Décommenter le bloc Option B :
registered_agent = self._route_to_agent(description)
agent = self._agent_factory.create_agent(registered_agent)
logger.info("EXECUTION_MANAGER", f"Routed to agent: {registered_agent.get_agent_name()}")

# Commenter/supprimer le bloc MockAgent actuel
```

### Étape 3 : Charger les agents depuis JSON

Dans `main.py`, la fonction `_register_agents()` charge déjà les agents depuis les JSON.
Vérifier que ces agents existent :
- `agents/profiles/git_agent.json`
- `agents/profiles/bash_agent.json`
- `agents/profiles/default_agent.json`
- `agents/profiles/todolist_agent.json`

## Architecture

```
User Query
    ↓
StateManager → TodoList (step_1, step_2, ...)
    ↓
ExecutionManager.execute()
    ↓
Pour chaque step:
    ↓
1. _route_to_agent(description)
   ├─ Analyse mots-clés
   ├─ Trouve RegisteredAgent
   └─ Retourne profil agent
    ↓
2. AgentFactory.create_agent(registered_agent)
   ├─ Check cache
   ├─ Si cached: retourne instance
   └─ Sinon: crée + cache + retourne
    ↓
3. Agent.run(step_description)
   ├─ Décompose en commandes
   ├─ Utilise ses tools
   └─ Retourne résultat
    ↓
4. Mise à jour StateManager
    ↓
Loop jusqu'à completion
```

## Amélioration du routing

Le routing actuel utilise des mots-clés simples. Pour l'améliorer :

### Option 1 : Embeddings (semantic search)
```python
def _route_to_agent(self, description: str):
    # Utiliser embeddings pour comparer description avec profiles
    embedding = get_embedding(description)
    best_agent = find_most_similar(embedding, agent_profiles)
    return best_agent
```

### Option 2 : LLM-based routing
```python
def _route_to_agent(self, description: str):
    # Demander au LLM quel agent utiliser
    prompt = f"Which agent for: {description}? (git/bash/python/default)"
    agent_name = llm.query(prompt)
    return self._agent_repository.find_by_name(agent_name)
```

### Option 3 : Tags matching
```python
def _route_to_agent(self, description: str):
    # Matcher les tags de specialization
    for agent in self._agent_repository.find_active():
        if any(tag in description.lower() for tag in agent.specialization_tags):
            return agent
    return default_agent
```

## Logs de routing

Quand activé, vous verrez dans les logs :
```
[EXECUTION_MANAGER] Creating agent for step: step_1
[EXECUTION_MANAGER] Routed to agent: GitAgent
[AGENT_FACTORY] Returning cached agent: GitAgent
```

## Désactiver le routing

Pour revenir à MockAgent simple :
1. Re-commenter tout le code Option B
2. Le système revient au mode simple actuel
