# Core - Architecture Multi-Agents

Ce document explique la nouvelle architecture multi-agents et comment l'intégrer progressivement à la structure actuelle.

## Vue d'ensemble

```
core/
├── domain/           ← Entités métier (Phase 1 ✅)
├── repositories/     ← Persistance abstraite (Phase 1 ✅)
├── services/         ← Logique métier (Phase 2 ✅)
├── orchestrator.py   ← Orchestration actuelle
├── memory.py         ← Gestion mémoire actuelle
├── llm_wrapper/      ← Wrapper LLM
├── tool_scheduler.py ← Ordonnancement outils
└── prompt_builder.py ← Construction prompts
```

## Architecture en couches

### Couches implémentées

```
┌─────────────────────────────────────┐
│     Service Layer (Phase 2 ✅)      │
│  - AgentMemoryCoordinator           │
│  - AgentPromptConstructor           │
│  - AgentExecutionService            │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│     Domain Layer (Phase 1 ✅)       │
│  - AgentIdentity                    │
│  - AgentCapabilities                │
│  - ConversationContext              │
│  - RegisteredAgent                  │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Repository Layer (Phase 1 ✅)     │
│  - AgentRepository                  │
│  - MemoryRepository                 │
│  - InMemory implementations         │
└─────────────────────────────────────┘
```

### Couches existantes

```
┌─────────────────────────────────────┐
│     Orchestration (actuelle)        │
│  - Orchestrator                     │
│  - Terminal/CLI                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Infrastructure (actuelle)         │
│  - LLMWrapper                       │
│  - ToolScheduler                    │
│  - PromptBuilder                    │
│  - MemoryManager                    │
└─────────────────────────────────────┘
```

---

## Étapes d'intégration

### Phase 1 & 2 : Fondations (✅ COMPLETÉ)

**Ce qui a été fait:**
- ✅ Domain Layer : Value Objects et Entities
- ✅ Repository Layer : Interfaces et implémentations in-memory
- ✅ Service Layer : Coordinateurs et services d'exécution

**Bénéfices immédiats:**
- Base solide pour architecture multi-agents
- Patterns éprouvés (Repository, Service Layer, Value Objects)
- Code testable et maintenable
- Isolation et thread-safety

### Phase 3 : Adaptation progressive (EN COURS)

#### Étape 3.1 : Intégration de AgentMemoryCoordinator

**Objectif:** Remplacer accès direct à MemoryManager par AgentMemoryCoordinator

**Changements:**

1. **Dans Orchestrator:**
```python
# AVANT
class Orchestrator:
    def __init__(self, llm_config):
        self._memory_manager = MemoryManager(conversation_size=10)

# APRÈS
class Orchestrator:
    def __init__(self, llm_config):
        memory_repo = InMemoryMemoryRepository()
        self._memory_coordinator = AgentMemoryCoordinator(memory_repo)
```

2. **Dans BaseAgent:**
```python
# AVANT
def __init__(self, memory_manager: MemoryManager, ...):
    self._memory_manager = memory_manager

# APRÈS
def __init__(self, agent_identity: AgentIdentity, memory_coordinator: AgentMemoryCoordinator, ...):
    self._memory_manager = memory_coordinator.get_or_create_memory_manager(agent_identity)
```

**Avantages:**
- Cache automatique des contextes
- Isolation mémoire garantie
- Support cross-agent context prêt
- Nettoyage automatique des mémoires inactives

---

#### Étape 3.2 : Intégration de AgentRepository

**Objectif:** Centraliser la gestion des agents

**Changements:**

1. **Dans main.py:**
```python
# AVANT
def _build_agents(self, llm, tool_scheduler, tool_registry, memory_manager):
    agents = []
    config = AgentConfig(...)
    agent = DefaultAgent(llm, tool_scheduler, ...)
    agents.append(agent)
    return agents

# APRÈS
def _build_agents(self):
    agent_repo = InMemoryAgentRepository()

    # Créer et enregistrer les agents
    code_agent = RegisteredAgent.create_new(
        name="CodeAgent",
        description="Agent spécialisé en code",
        authorized_tools=["read_file", "write_file"],
        system_prompt="You are a code assistant..."
    )
    agent_repo.save(code_agent)

    chat_agent = RegisteredAgent.create_new(
        name="ChatAgent",
        description="Agent conversationnel",
        authorized_tools=None,  # Aucun outil
        system_prompt="You are a friendly chat assistant..."
    )
    agent_repo.save(chat_agent)

    return agent_repo
```

2. **Dans Orchestrator:**
```python
# AVANT
def __init__(self, agents: List[BaseAgent]):
    self._agents = agents
    self._current_agent = agents[0]

# APRÈS
def __init__(self, agent_repository: AgentRepository):
    self._agent_repository = agent_repository
    self._current_agent_id = None  # Set dynamically
```

**Avantages:**
- Gestion centralisée des agents
- Agents peuvent être ajoutés/supprimés à runtime
- Recherche rapide par ID ou nom
- Validation automatique

---

#### Étape 3.3 : Utilisation de AgentExecutionService

**Objectif:** Exécution tracée et métrisée

**Changements:**

1. **Dans Orchestrator:**
```python
# AVANT
def process_user_input(self, user_input: str) -> AgentOutput:
    return self._current_agent.run(user_input)

# APRÈS
def process_user_input(self, user_input: str) -> AgentOutput:
    result = self._execution_service.execute_agent(
        agent_id=self._current_agent_id,
        user_input=user_input,
        execution_options=ExecutionOptions(
            timeout_seconds=30,
            include_metrics=True
        )
    )

    # Log metrics
    logger.info("ORCHESTRATOR", f"Execution time: {result.execution_time_seconds}s")

    return result.output
```

**Avantages:**
- Métriques automatiques (temps d'exécution)
- Gestion d'erreurs robuste
- Logging cohérent
- Support timeout
- Traçabilité complète

---

#### Étape 3.4 : Intégration de AgentPromptConstructor

**Objectif:** Prompts optimisés par agent

**Changements:**

1. **Remplacer PromptBuilder global:**
```python
# AVANT (PromptBuilder unique pour tous)
prompt_builder = PromptBuilder(
    system_prompt="Generic prompt",
    tool_registry=tool_registry
)

# APRÈS (PromptConstructor par agent)
def create_prompt_constructor(agent: RegisteredAgent):
    return AgentPromptConstructor(
        agent_capabilities=agent.agent_capabilities,
        memory_coordinator=memory_coordinator,
        tool_registry=tool_registry
    )
```

**Avantages:**
- Prompt adapté aux capacités de chaque agent
- Cache du system prompt
- Support collaboration inter-agents
- Filtrage automatique des outils

---

### Phase 4 : Multi-Agent Orchestrator (FUTUR)

**Objectif:** Orchestration avancée multi-agents

**Nouvelles fonctionnalités:**

1. **Routing intelligent:**
```python
routing_service = AgentRoutingService(agent_repo)
best_agent = routing_service.route_to_best_agent(
    user_input="Write Python code",
    specialization_required="code"
)
```

2. **Collaboration inter-agents:**
```python
execution_options = ExecutionOptions(
    enable_cross_agent_context=True,
    cross_agent_ids=["agent-1", "agent-2"]
)
result = execution_service.execute_agent(
    agent_id="agent-3",
    user_input="Summarize previous conversations",
    execution_options=execution_options
)
```

3. **Factory pour création d'agents:**
```python
factory = AgentFactory(
    llm_wrapper=llm,
    tool_scheduler=scheduler,
    memory_coordinator=coordinator
)
agent_instance = factory.create_agent(registered_agent)
```

---

## Pourquoi cette architecture ?

### 1. Séparation des responsabilités

**Avant:**
```python
# Tout mélangé dans Orchestrator
class Orchestrator:
    def __init__(self):
        self._llm = LLMWrapper()
        self._memory = MemoryManager()
        self._tools = ToolScheduler()
        self._agent = DefaultAgent(...)
        # 200+ lignes de setup
```

**Après:**
```python
# Responsabilités séparées
domain/         → Entités métier pures
repositories/   → Persistance abstraite
services/       → Logique métier
orchestrator    → Orchestration uniquement
```

**Bénéfices:**
- Code plus lisible et maintenable
- Chaque composant a un rôle clair
- Changements localisés, pas d'effets de bord

---

### 2. Testabilité

**Avant:**
```python
# Difficile à tester, dépendances hardcodées
class Orchestrator:
    def __init__(self):
        self._llm = LLMWrapper()  # Connexion réelle au LLM
        self._memory = MemoryManager()
```

**Après:**
```python
# Facile à mocker
def test_execution_service():
    mock_repo = Mock(spec=AgentRepository)
    mock_coordinator = Mock(spec=AgentMemoryCoordinator)

    service = AgentExecutionService(mock_repo, mock_coordinator)
    # Test isolé
```

**Bénéfices:**
- Tests unitaires rapides
- Mocks faciles
- Pas de dépendances externes en test

---

### 3. Scalabilité

**Avant:**
```python
# Un seul agent à la fois
orchestrator = Orchestrator(agents=[agent1])
```

**Après:**
```python
# 100+ agents sans problème
agent_repo = InMemoryAgentRepository()
for i in range(100):
    agent = RegisteredAgent.create_new(...)
    agent_repo.save(agent)

# Cache LRU évite surcharge mémoire
memory_coordinator = AgentMemoryCoordinator(
    memory_repo,
    cache_strategy=LRUCache(max_size=100)
)

# Cleanup automatique des agents inactifs
memory_coordinator.cleanup_inactive_memories(inactive_threshold_hours=24)
```

**Bénéfices:**
- Support 100+ agents concurrent
- Gestion mémoire optimisée (cache, cleanup)
- Performance préservée (lazy loading, cache)

---

### 4. Extensibilité

**Avant:**
```python
# Changement de DB = réécriture complète
class MemoryManager:
    def __init__(self):
        self._memory = []  # In-memory hardcodé
```

**Après:**
```python
# Changement de DB = nouvelle implémentation du repository
class PostgresMemoryRepository(MemoryRepository):
    def save_turn(self, ...):
        # INSERT en PostgreSQL

# Pas de changement ailleurs
memory_coordinator = AgentMemoryCoordinator(
    PostgresMemoryRepository(conn_string)  # ← Seul changement
)
```

**Bénéfices:**
- Changement d'implémentation sans impact
- Ajout de features facile
- Code fermé aux modifications, ouvert aux extensions (OCP)

---

### 5. Type Safety

**Avant:**
```python
# Types flous, validation manuelle
def create_agent(name, description, tools):
    if not name or len(name) < 3:
        raise ValueError("Invalid name")
    # Validation éparpillée
```

**Après:**
```python
# Types stricts, validation automatique
agent = RegisteredAgent.create_new(
    name="A",  # ❌ ValueError: name too short (automatic)
    description="...",
    authorized_tools=[...]
)
```

**Bénéfices:**
- Erreurs détectées tôt
- Auto-documentation via types
- IDE auto-completion

---

### 6. Réutilisabilité

**Avant:**
```python
# Logique dupliquée
def process_input_agent1(input):
    # Build context, execute, log
    pass

def process_input_agent2(input):
    # Build context, execute, log (copié-collé)
    pass
```

**Après:**
```python
# Logique centralisée
execution_service.execute_agent(agent_id="agent-1", user_input=input)
execution_service.execute_agent(agent_id="agent-2", user_input=input)
# Même logique, pas de duplication
```

**Bénéfices:**
- DRY (Don't Repeat Yourself)
- Maintenance simplifiée
- Bugs fixés une seule fois

---

## Migration progressive

### Approche recommandée

**Ne PAS tout refactorer d'un coup**

```
✅ Approche progressive:
1. Ajouter les nouvelles couches (domain, repositories, services) ← FAIT
2. Utiliser en parallèle de l'ancien code
3. Migrer composant par composant
4. Supprimer l'ancien code quand tout est migré

❌ Approche big bang:
1. Tout casser
2. Tout réécrire
3. Tout debugger
```

### Coexistence temporaire

**Possible d'utiliser les deux systèmes:**

```python
class Orchestrator:
    def __init__(self):
        # Ancien système (pour compatibilité)
        self._old_memory = MemoryManager()

        # Nouveau système (pour nouveaux features)
        memory_repo = InMemoryMemoryRepository()
        self._memory_coordinator = AgentMemoryCoordinator(memory_repo)
        self._agent_repository = InMemoryAgentRepository()

    def process_old_way(self, input):
        # Utilise ancien système
        return self._old_agent.run(input)

    def process_new_way(self, input):
        # Utilise nouveau système
        return self._execution_service.execute_agent(...)
```

**Transition graduelle:**
1. Nouvelle feature → Nouveau système
2. Bug fix ancien code → Migrer vers nouveau
3. Refactoring → Migrer progressivement
4. Suppression ancien code quand 100% migré

---

## Métriques de succès

### Code Quality

| Métrique | Avant | Après |
|----------|-------|-------|
| Lignes par fichier | 500+ | < 300 |
| Responsabilités par classe | 5+ | 1-2 |
| Dépendances circulaires | Oui | Non |
| Coverage tests | < 30% | > 80% |

### Performance

| Métrique | Avant | Après |
|----------|-------|-------|
| Temps création agent | O(n) | O(1) + cache |
| Lookup agent | O(n) | O(1) |
| Mémoire pour 100 agents | ~500MB | ~50MB (cache) |
| Cleanup inactifs | Manuel | Automatique |

### Maintenabilité

| Métrique | Avant | Après |
|----------|-------|-------|
| Temps ajout agent | 2h | 10min |
| Lignes pour nouvel agent | 200+ | 10 |
| Impact changement DB | Réécriture | Nouveau Repository |
| Tests par feature | 5 min | 30s (mocks) |

---
