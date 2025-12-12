# Service Layer

Le Service Layer contient la logique métier applicative. Il orchestre les opérations entre le Domain Layer et le Repository Layer.

## Principes

- **Séparation des responsabilités** : Chaque service a un rôle unique
- **Orchestration** : Les services coordonnent les objets du domain et repositories
- **Stateless** : Les services ne stockent pas d'état métier
- **Réutilisabilité** : Logique métier partagée entre différents points d'entrée

## Architecture

```
Service Layer
├── Cache Strategy
│   ├── CacheStrategy (interface)
│   └── LRUCache (implémentation)
├── Coordination Services
│   ├── AgentMemoryCoordinator
│   └── AgentPromptConstructor
├── Execution Services
│   └── AgentExecutionService
└── Types
    ├── ExecutionOptions
    ├── AgentExecutionResult
    └── Exceptions
```

## Fichiers

### Cache Strategy

#### `cache_strategy.py` (193 lignes)
**Stratégies de caching pour optimisation**

Fournit une abstraction pour différentes stratégies de cache.

**Interface CacheStrategy:**
```python
class CacheStrategy(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def size(self) -> int:
        pass
```

**Implémentation LRUCache:**

Implémente Least Recently Used cache avec éviction automatique.

**Caractéristiques:**
- **Thread-safe** : Utilise RLock
- **O(1) access** : Utilise OrderedDict
- **Auto-éviction** : Supprime LRU quand plein
- **Configurable** : Taille max paramétrable

**Structure:**
```python
_max_size: int                              # Taille maximum
_cache: OrderedDict[str, Any]               # Cache ordonné
_lock: RLock                                # Thread-safety
```

**Méthodes:**
```python
cache.get("key")                # Récupère et marque comme utilisé
cache.put("key", value)         # Ajoute/update, évicte si plein
cache.contains("key")           # Vérifie existence
cache.remove("key")             # Supprime clé spécifique
cache.get_stats()               # Statistiques (size, utilization)
```

**Usage:**
```python
cache = LRUCache(max_size=100)
cache.put("agent-123", context)
context = cache.get("agent-123")  # O(1)
stats = cache.get_stats()
# {'size': 50, 'max_size': 100, 'utilization': 0.5}
```

---

### Coordination Services

#### `agent_memory_coordinator.py` (306 lignes)
**Coordonne l'accès aux mémoires multi-agents**

Service central pour gérer la mémoire de tous les agents avec isolation et cache.

**Responsabilités:**
- Isolation des mémoires par agent
- Accès cross-agent sécurisé
- Cache des contextes fréquemment accédés
- Nettoyage automatique des mémoires inactives

**Structure:**
```python
_memory_repository: MemoryRepository           # Persistance
_cache: CacheStrategy                          # Cache LRU
_memory_managers: Dict[str, MemoryManager]     # Managers actifs
```

**Méthodes principales:**

**Gestion des Memory Managers:**
```python
get_or_create_memory_manager(agent_identity: AgentIdentity) -> MemoryManager
```
- Lazy loading des memory managers
- Cache en mémoire pour réutilisation
- Un manager par agent

**Récupération de contexte (avec cache):**
```python
get_conversation_context(
    agent_identity: AgentIdentity,
    max_turns: Optional[int] = None
) -> ConversationContext
```
- Vérifie le cache d'abord
- Construit depuis repository si absent
- Met en cache le résultat

**Collaboration inter-agents:**
```python
build_cross_agent_context(
    requesting_agent_id: str,
    other_agent_ids: List[str],
    max_turns_per_agent: int = 5
) -> CrossAgentContext
```
- Récupère les contextes de plusieurs agents
- Construit un contexte partagé
- Exclut l'agent demandeur

**Sauvegarde (avec invalidation cache):**
```python
save_conversation_turn(
    agent_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict] = None
) -> bool
```
- Sauvegarde dans repository
- Invalide le cache pour cet agent

**Nettoyage automatique:**
```python
cleanup_inactive_memories(
    inactive_threshold_hours: int = 24
) -> int
```
- Nettoie les mémoires des agents inactifs
- Stratégie de scalabilité
- Retourne le nombre de mémoires nettoyées

**Statistiques:**
```python
get_memory_stats() -> Dict
# {
#     'active_memory_managers': 5,
#     'cache_stats': {'size': 20, 'max_size': 100},
#     'total_agents_with_memory': 12
# }
```

---

#### `agent_prompt_constructor.py` (251 lignes)
**Construit des prompts spécifiques par agent**

Service pour construire des prompts optimisés selon les capacités de chaque agent.

**Responsabilités:**
- Construction du system prompt avec capacités
- Intégration de l'historique conversationnel
- Injection du contexte cross-agent
- Cache des prompts compilés

**Structure:**
```python
_capabilities: AgentCapabilities                  # Capacités de l'agent
_memory_coordinator: AgentMemoryCoordinator       # Accès mémoire
_tool_registry: ToolRegistry                      # Registry des outils
_system_prompt_cache: Optional[str]               # Cache du system prompt
```

**Méthodes principales:**

**System Prompt (avec cache):**
```python
build_system_prompt() -> str
```
Format généré:
```
{description}

Capabilities:
- Max reasoning turns: 10
- Max memory turns: 10
- Specializations: code, files

Available tools:
- read_file: Read file contents
- write_file: Write content to file
```

**Messages de conversation:**
```python
build_conversation_messages(
    conversation_context: ConversationContext
) -> List[Message]
```
- Ajoute system prompt
- Ajoute tout l'historique
- Retourne liste prête pour LLM

**Avec contexte cross-agent:**
```python
build_with_cross_agent_context(
    conversation_context: ConversationContext,
    cross_agent_context: CrossAgentContext
) -> List[Message]
```
- Construit messages normaux
- Formate contexte des autres agents
- Injecte avant dernier message

**Gestion du cache:**
```python
invalidate_cache()  # Force reconstruction au prochain appel
```

**Filtrage des outils:**
- Seuls les outils autorisés sont inclus dans le prompt
- Si authorized_tools est vide, tous les outils sont inclus

---

### Execution Services

#### `agent_execution_service.py` (260 lignes)
**Service d'exécution avec traçabilité complète**

Service central pour exécuter des agents avec métriques et gestion d'erreurs.

**Responsabilités:**
- Validation de l'agent (existe, actif)
- Préparation du contexte d'exécution
- Exécution avec timeout et métriques
- Post-traitement et logging
- Gestion d'erreurs complète

**Structure:**
```python
_agent_repository: AgentRepository
_memory_coordinator: AgentMemoryCoordinator
```

**Méthodes principales:**

**Exécution par ID:**
```python
execute_agent(
    agent_id: str,
    user_input: str,
    execution_options: Optional[ExecutionOptions] = None
) -> AgentExecutionResult
```

**Workflow:**
1. Récupère l'agent depuis repository
2. Vérifie qu'il est actif
3. Prépare le contexte d'exécution
4. Execute avec mesure du temps
5. Capture les erreurs
6. Crée AgentExecutionResult
7. Log les détails

**Exécution par nom:**
```python
execute_agent_by_name(
    agent_name: str,
    user_input: str,
    execution_options: Optional[ExecutionOptions] = None
) -> AgentExecutionResult
```

**Préparation du contexte:**
```python
_prepare_execution_context(agent, user_input, options) -> dict
```
Construit:
- Informations sur l'input
- Métadonnées de l'agent
- Configuration de timeout
- Contexte cross-agent si activé

**Statistiques:**
```python
get_execution_stats() -> dict
# {
#     'total_agents': 10,
#     'active_agents': 8,
#     'memory_stats': {...}
# }
```

**Exceptions:**
- `AgentNotFoundError` : Agent inexistant
- `AgentInactiveError` : Agent désactivé
- `AgentExecutionError` : Échec critique

---

### Types

#### `service_types.py` (141 lignes)
**Types de données pour les services**

Définit les structures de données utilisées par les services.

**ExecutionOptions:**
```python
@dataclass
class ExecutionOptions:
    timeout_seconds: Optional[int] = None
    enable_cross_agent_context: bool = False
    cross_agent_ids: list = field(default_factory=list)
    max_cross_agent_turns: int = 5
    include_metrics: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
```

Configuration pour l'exécution d'un agent.

**AgentExecutionResult:**
```python
@dataclass
class AgentExecutionResult:
    agent_id: str
    agent_name: str
    output: AgentOutput
    execution_time_seconds: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        # Conversion en dictionnaire
```

Résultat complet avec métriques et traçabilité.

**Exceptions:**
- `AgentNotFoundError` : Agent introuvable
- `AgentInactiveError` : Agent inactif
- `AgentExecutionError` : Erreur d'exécution

---

## Patterns utilisés

### Service Layer Pattern
**Logique métier dans des services dédiés**

Les services orchestrent domain et repositories sans contenir de logique métier complexe.

```python
class AgentExecutionService:
    # Service orchestre, ne contient pas logique domain
    def execute_agent(self, agent_id, user_input):
        agent = self._agent_repository.find_by_id(agent_id)  # Repository
        context = self._memory_coordinator.get_context(...)   # Service
        # Orchestration, pas logique métier
```

### Coordinator Pattern
**Coordination d'accès complexes**

AgentMemoryCoordinator coordonne l'accès à la mémoire de multiples agents.

```python
# Au lieu d'accéder directement au repository
memory_repo.get_context(agent_id)  # ❌ Direct

# On passe par le coordinator
memory_coordinator.get_conversation_context(identity)  # ✅ Coordinated
```

**Avantages:**
- Cache centralisé
- Isolation garantie
- Logique de nettoyage centralisée

### Builder Pattern
**Construction progressive de prompts**

AgentPromptConstructor construit progressivement des prompts complexes.

```python
constructor.build_system_prompt()              # Étape 1
constructor.build_conversation_messages(ctx)   # Étape 2
constructor.build_with_cross_agent_context()   # Étape 3 (optionnelle)
```

### Strategy Pattern (Cache)
**Stratégies de cache interchangeables**

```python
# Différentes stratégies possibles
cache = LRUCache(max_size=100)           # LRU
cache = LFUCache(max_size=100)           # Least Frequently Used
cache = TTLCache(ttl_seconds=3600)       # Time To Live

# Interface identique
coordinator = AgentMemoryCoordinator(repo, cache_strategy=cache)
```

## Usage complet

```python
from core.domain import AgentIdentity, RegisteredAgent
from core.repositories import InMemoryAgentRepository, InMemoryMemoryRepository
from core.services import (
    LRUCache,
    AgentMemoryCoordinator,
    AgentPromptConstructor,
    AgentExecutionService,
    ExecutionOptions
)
from tools.tool_base import get_registry

# Setup repositories
agent_repo = InMemoryAgentRepository()
memory_repo = InMemoryMemoryRepository()

# Setup services
cache = LRUCache(max_size=100)
memory_coordinator = AgentMemoryCoordinator(memory_repo, cache)
execution_service = AgentExecutionService(agent_repo, memory_coordinator)

# Créer et enregistrer un agent
agent = RegisteredAgent.create_new(
    name="CodeAgent",
    description="Code analysis agent",
    authorized_tools=["read_file", "write_file"],
    system_prompt="You are a code assistant"
)
agent_repo.save(agent)

# Construire un prompt
identity = agent.agent_identity
tool_registry = get_registry()
prompt_constructor = AgentPromptConstructor(
    agent.agent_capabilities,
    memory_coordinator,
    tool_registry
)
system_prompt = prompt_constructor.build_system_prompt()

# Exécuter l'agent
options = ExecutionOptions(
    timeout_seconds=30,
    enable_cross_agent_context=False,
    include_metrics=True
)
result = execution_service.execute_agent(
    agent_id=agent.get_agent_id(),
    user_input="Analyze this code",
    execution_options=options
)

print(f"Success: {result.success}")
print(f"Time: {result.execution_time_seconds}s")
print(f"Response: {result.output.response}")
```

## Avantages

1. **Réutilisabilité** - Logique métier centralisée et réutilisable
2. **Performance** - Cache LRU pour optimisation
3. **Isolation** - Coordination centralisée évite les conflits
4. **Traçabilité** - Métriques et logging complets
5. **Flexibilité** - Services composables et interchangeables
6. **Testabilité** - Services faciles à mocker et tester
7. **Scalabilité** - Cleanup automatique, cache, lazy loading
