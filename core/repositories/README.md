# Repository Layer

Le Repository Layer fournit l'abstraction pour la persistance des données. Il sépare la logique de stockage de la logique métier selon le pattern Repository.

## Principes

- **Abstraction** : Interfaces définissent le contrat, implémentations sont interchangeables
- **Isolation** : Le domain ne dépend jamais directement d'une implémentation
- **Thread-safety** : Toutes les implémentations sont thread-safe (RLock)
- **Testabilité** : Facile de mocker les repositories pour les tests

## Architecture

```
Repository Layer
├── Interfaces (abstraites)
│   ├── AgentRepository
│   └── MemoryRepository
└── Implementations (concrètes)
    ├── InMemoryAgentRepository
    └── InMemoryMemoryRepository
```

## Fichiers

### Interfaces

#### `agent_repository.py` (182 lignes)
**Interface abstraite pour la persistance des agents**

Définit le contrat pour toutes les opérations de persistance des agents.

**Méthodes principales:**

**Création/Modification:**
```python
save(agent: RegisteredAgent) -> RegisteredAgent
```
- Sauvegarde ou met à jour un agent
- Si l'ID existe déjà, mise à jour
- Sinon, création

**Recherche:**
```python
find_by_id(agent_id: str) -> Optional[RegisteredAgent]
find_by_name(agent_name: str) -> Optional[RegisteredAgent]
find_all() -> List[RegisteredAgent]
find_active() -> List[RegisteredAgent]
```

**Vérification:**
```python
exists(agent_id: str) -> bool
exists_by_name(agent_name: str) -> bool
count() -> int
```

**Suppression:**
```python
delete(agent_id: str) -> bool
clear() -> None  # DANGER: supprime tout
```

**Exceptions:**
- `ValueError` : Si l'agent est invalide ou nom en conflit
- `RepositoryError` : Si l'opération échoue

---

#### `memory_repository.py` (217 lignes)
**Interface abstraite pour la persistance de la mémoire conversationnelle**

Définit le contrat pour stocker et récupérer l'historique des conversations.

**Méthodes principales:**

**Sauvegarde:**
```python
save_turn(agent_id: str, role: str, content: Any, metadata: Optional[Dict] = None) -> bool
append_turns(agent_id: str, turns: List[Dict]) -> bool
```

**Récupération:**
```python
get_conversation_history(agent_id: str, max_turns: Optional[int] = None) -> List[Dict]
get_context(agent_id: str, max_turns: Optional[int] = None) -> Optional[ConversationContext]
get_last_turn(agent_id: str) -> Optional[Dict]
```

**Gestion:**
```python
clear_agent_memory(agent_id: str) -> bool        # Vide la mémoire, garde la structure
delete_agent_memory(agent_id: str) -> bool       # Supprime complètement
clear_all() -> None                               # DANGER: supprime tout
```

**Statistiques:**
```python
exists(agent_id: str) -> bool
get_turn_count(agent_id: str) -> int
get_all_agent_ids() -> List[str]
```

**Validation des turns:**
- Chaque turn doit avoir 'role' et 'content'
- Role doit être: 'user', 'assistant', 'system', ou 'tool'

---

### Implémentations

#### `in_memory_agent_repository.py` (245 lignes)
**Implémentation in-memory thread-safe du AgentRepository**

Stocke les agents en mémoire avec deux index pour performance.

**Structure de stockage:**
```python
_agents_by_id: Dict[str, RegisteredAgent]     # Index par ID
_agents_by_name: Dict[str, RegisteredAgent]   # Index par nom
_lock: RLock                                    # Pour thread-safety
```

**Caractéristiques:**
- **Thread-safe** : Utilise RLock pour toutes les opérations
- **Double indexation** : Recherche O(1) par ID et par nom
- **Deep copy** : Retourne des copies pour éviter modifications externes
- **Validation** : Vérifie les conflits de noms

**Gestion des conflits:**
```python
# Interdit deux agents différents avec le même nom
if existing_by_name and existing_by_name.get_agent_id() != agent_id:
    raise ValueError(f"Agent name '{agent_name}' already exists")
```

**Méthodes de convenance:**
```python
len(repository)              # Nombre d'agents
agent_id in repository       # Vérifie existence
str(repository)              # "InMemoryAgentRepository(total=5, active=3)"
```

**Usage:**
```python
from core.repositories import InMemoryAgentRepository

repo = InMemoryAgentRepository()
repo.save(agent)
found = repo.find_by_name("CodeAgent")
all_active = repo.find_active()
```

---

#### `in_memory_memory_repository.py` (405 lignes)
**Implémentation in-memory thread-safe du MemoryRepository**

Stocke l'historique conversationnel de chaque agent isolément.

**Structure de stockage:**
```python
_memories: Dict[str, List[Dict[str, Any]]]    # agent_id -> list of turns
_lock: RLock                                   # Pour thread-safety
```

**Caractéristiques:**
- **Isolation par agent** : Chaque agent a sa propre liste de turns
- **Thread-safe** : RLock sur toutes les opérations
- **Deep copy** : Retourne des copies pour éviter modifications
- **Auto-timestamp** : Ajoute timestamp si absent

**Format des turns:**
```python
{
    'role': 'user' | 'assistant' | 'system' | 'tool',
    'content': Any,
    'timestamp': '2025-12-12T10:30:00',  # ISO format
    'metadata': {...}  # Optionnel
}
```

**Validation stricte:**
- Role doit être dans ['user', 'assistant', 'system', 'tool']
- Chaque turn doit avoir 'role' et 'content'
- Agent_id non vide

**Méthodes de convenance:**
```python
len(repository)              # Nombre d'agents avec mémoire
agent_id in repository       # Vérifie si agent a mémoire
str(repository)              # "InMemoryMemoryRepository(agents=3, total_turns=45)"
```

**Création de contexte:**
```python
context = repository.get_context("agent-123", max_turns=10)
# Retourne un ConversationContext complet
```

**Usage:**
```python
from core.repositories import InMemoryMemoryRepository

repo = InMemoryMemoryRepository()
repo.save_turn("agent-123", "user", "Hello")
repo.save_turn("agent-123", "assistant", "Hi there!")
history = repo.get_conversation_history("agent-123")
```

---

## Patterns utilisés

### Repository Pattern
**Abstraction de la persistance**

Sépare la logique métier de la logique de stockage.

**Avantages:**
- Changement facile d'implémentation (in-memory → database)
- Tests faciles avec mocks
- Logique métier indépendante du stockage

**Exemple:**
```python
# Interface
repo: AgentRepository = get_repository()  # Type abstrait

# Implémentation peut changer sans impact
repo = InMemoryAgentRepository()          # Dev/Test
repo = PostgresAgentRepository()          # Production
```

### Dependency Injection
**Injection des repositories dans les services**

```python
class AgentExecutionService:
    def __init__(
        self,
        agent_repository: AgentRepository,  # Interface, pas implémentation
        memory_coordinator: AgentMemoryCoordinator
    ):
        self._agent_repository = agent_repository
        self._memory_coordinator = memory_coordinator
```

### Thread-Safety Pattern
**Utilisation de RLock**

```python
with self._lock:
    # Opération atomique
    agent = self._agents_by_id.get(agent_id)
    return copy.deepcopy(agent) if agent else None
```

## Implémentations futures possibles

### PostgresAgentRepository
```python
class PostgresAgentRepository(AgentRepository):
    def __init__(self, connection_string: str):
        self.db = psycopg2.connect(connection_string)

    def save(self, agent: RegisteredAgent) -> RegisteredAgent:
        # INSERT ou UPDATE en base
        pass
```

### RedisMemoryRepository
```python
class RedisMemoryRepository(MemoryRepository):
    def __init__(self, redis_client):
        self.redis = redis_client

    def save_turn(self, agent_id: str, role: str, content: Any):
        # LPUSH dans Redis
        pass
```

## Exception Handling

### RepositoryError
Exception de base pour toutes les erreurs de repository.

**Usage:**
```python
try:
    repo.save(agent)
except RepositoryError as e:
    logger.error(f"Repository error: {e}")
```

**Cas d'usage:**
- Échec de suppression
- Échec de nettoyage
- Corruption de données

## Usage complet

```python
from core.domain import RegisteredAgent
from core.repositories import (
    InMemoryAgentRepository,
    InMemoryMemoryRepository
)

# Créer les repositories
agent_repo = InMemoryAgentRepository()
memory_repo = InMemoryMemoryRepository()

# Créer et sauvegarder un agent
agent = RegisteredAgent.create_new(
    name="CodeAgent",
    description="Code analysis agent",
    authorized_tools=["read_file"],
    system_prompt="You are a code assistant"
)
agent_repo.save(agent)

# Sauvegarder de la mémoire
agent_id = agent.get_agent_id()
memory_repo.save_turn(agent_id, "user", "Hello")
memory_repo.save_turn(agent_id, "assistant", "Hi!")

# Récupérer
found_agent = agent_repo.find_by_name("CodeAgent")
history = memory_repo.get_conversation_history(agent_id)
context = memory_repo.get_context(agent_id, max_turns=10)
```

## Avantages

1. **Flexibilité** - Changement d'implémentation sans impact sur le code métier
2. **Testabilité** - Mock facile des repositories pour tests unitaires
3. **Isolation** - Chaque agent a sa mémoire isolée
4. **Performance** - Double indexation pour recherche rapide
5. **Thread-safety** - Utilisable dans environnement multi-thread
6. **Type-safety** - Interfaces définissent clairement les contrats
