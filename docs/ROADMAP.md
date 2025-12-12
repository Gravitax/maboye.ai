# ROADMAP V2: Architecture Multi-Agents Scalable

## 📋 Vue d'ensemble

Migration vers une architecture multi-agents **évolutive**, **maintenable** et **performante** avec séparation claire des responsabilités et patterns de conception éprouvés.

## Standards de Code
- Convention snake_case stricte
- Fonctions courtes et à responsabilité unique
- Documentation professionnelle, sans emojis
- Flux de contrôle simplifié
- Aucun credential en clair (utiliser .env)

### Principes directeurs

1. **Separation of Concerns** - Chaque composant a une responsabilité unique
2. **Dependency Injection** - Couplage faible, testabilité maximale
3. **Interface Segregation** - Interfaces spécifiques et cohérentes
4. **Scalability First** - Conception pour supporter 100+ agents

---

## 🏗️ Architecture cible en couches

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                         │
│  main.py, cli/terminal.py, cli/commands/                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestration Layer                        │
│  MultiAgentOrchestrator, AgentLifecycleManager                 │
│  AgentRoutingService, AgentCoordinationService                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                            │
│  AgentExecutionService, AgentMemoryCoordinator                 │
│  PromptConstructionService, AgentContextBuilder                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Domain Layer                             │
│  RegisteredAgent, AgentIdentity, AgentCapabilities             │
│  ConversationContext, AgentMemorySnapshot                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Repository Layer                           │
│  AgentRepository, MemoryRepository                             │
│  ConversationHistoryRepository                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                         │
│  InMemoryAgentRepository, FileSystemMemoryRepository           │
│  LLMWrapper, ToolScheduler                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Composants principaux

### 1. Domain Layer (Entités métier)

#### `AgentIdentity` (Value Object)
```python
@dataclass(frozen=True)
class AgentIdentity:
    """
    Identité unique et immuable d'un agent.
    Value Object qui garantit l'unicité et l'intégrité.
    """
    agent_id: str  # UUID v4
    agent_name: str  # Nom unique lisible (ex: "CodeAgent")
    creation_timestamp: datetime

    def __post_init__(self):
        # Validation: agent_name doit être unique et valide
        # agent_id doit être un UUID valide
        pass
```

#### `AgentCapabilities` (Value Object)
```python
@dataclass(frozen=True)
class AgentCapabilities:
    """
    Capacités et contraintes d'un agent.
    Définit ce que l'agent peut faire.
    """
    description: str
    authorized_tools: List[str]  # IDs des outils autorisés
    max_reasoning_turns: int
    max_memory_turns: int
    specialization_tags: List[str]  # Ex: ["code", "git", "files"]

    def can_use_tool(self, tool_id: str) -> bool:
        """Vérifie si l'outil est autorisé"""
        return tool_id in self.authorized_tools

    def has_specialization(self, tag: str) -> bool:
        """Vérifie si l'agent a cette spécialisation"""
        return tag in self.specialization_tags
```

#### `RegisteredAgent` (Entity)
```python
@dataclass
class RegisteredAgent:
    """
    Entité représentant un agent enregistré dans le système.
    Agrège l'identité, les capacités et les dépendances.
    """
    identity: AgentIdentity
    capabilities: AgentCapabilities
    agent_instance: BaseAgent
    memory_manager: MemoryManager
    prompt_constructor: AgentPromptConstructor

    # Métadonnées runtime
    total_interactions: int = 0
    last_interaction_timestamp: Optional[datetime] = None
    is_active: bool = True

    def execute(self, user_input: str) -> AgentOutput:
        """Exécute l'agent avec traçabilité"""
        self.total_interactions += 1
        self.last_interaction_timestamp = datetime.now()
        return self.agent_instance.run(user_input)
```

#### `ConversationContext` (Value Object)
```python
@dataclass(frozen=True)
class ConversationContext:
    """
    Contexte d'une conversation pour un agent.
    Snapshot immuable du contexte à un instant T.
    """
    agent_identity: AgentIdentity
    conversation_history: List[Dict[str, Any]]
    context_metadata: Dict[str, Any]
    created_at: datetime

    @staticmethod
    def create_from_memory(
        agent_identity: AgentIdentity,
        memory_manager: MemoryManager,
        max_turns: int
    ) -> 'ConversationContext':
        """Factory method pour créer depuis la mémoire"""
        pass
```

---

### 2. Repository Layer (Accès aux données)

#### `AgentRepository` (Interface)
```python
class AgentRepository(ABC):
    """
    Interface pour la persistance et récupération des agents.
    Abstraction du stockage physique.
    """

    @abstractmethod
    def register(self, agent: RegisteredAgent) -> None:
        """Enregistre un nouvel agent"""
        pass

    @abstractmethod
    def find_by_id(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Trouve un agent par son ID"""
        pass

    @abstractmethod
    def find_by_name(self, agent_name: str) -> Optional[RegisteredAgent]:
        """Trouve un agent par son nom"""
        pass

    @abstractmethod
    def find_all(self) -> List[RegisteredAgent]:
        """Récupère tous les agents enregistrés"""
        pass

    @abstractmethod
    def find_by_specialization(self, tag: str) -> List[RegisteredAgent]:
        """Trouve les agents ayant une spécialisation"""
        pass

    @abstractmethod
    def update(self, agent: RegisteredAgent) -> None:
        """Met à jour un agent"""
        pass

    @abstractmethod
    def remove(self, agent_id: str) -> bool:
        """Supprime un agent"""
        pass

    @abstractmethod
    def count(self) -> int:
        """Compte le nombre d'agents"""
        pass
```

#### `InMemoryAgentRepository` (Implémentation)
```python
class InMemoryAgentRepository(AgentRepository):
    """
    Implémentation en mémoire du repository d'agents.
    Thread-safe avec RLock pour accès concurrent.
    """

    def __init__(self):
        self._agents_by_id: Dict[str, RegisteredAgent] = {}
        self._agents_by_name: Dict[str, RegisteredAgent] = {}
        self._lock = RLock()

    def register(self, agent: RegisteredAgent) -> None:
        with self._lock:
            # Vérifier unicité
            if agent.identity.agent_id in self._agents_by_id:
                raise AgentAlreadyExistsError(...)
            if agent.identity.agent_name in self._agents_by_name:
                raise AgentNameConflictError(...)

            # Enregistrer
            self._agents_by_id[agent.identity.agent_id] = agent
            self._agents_by_name[agent.identity.agent_name] = agent

    # ... autres méthodes
```

#### `MemoryRepository` (Interface)
```python
class MemoryRepository(ABC):
    """
    Interface pour la persistance des mémoires d'agents.
    Permet différentes stratégies de stockage.
    """

    @abstractmethod
    def save_conversation_turn(
        self,
        agent_id: str,
        turn_data: Dict[str, Any]
    ) -> None:
        """Sauvegarde un tour de conversation"""
        pass

    @abstractmethod
    def get_conversation_history(
        self,
        agent_id: str,
        max_turns: int = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Récupère l'historique avec pagination"""
        pass

    @abstractmethod
    def clear_agent_memory(self, agent_id: str) -> None:
        """Efface la mémoire d'un agent"""
        pass

    @abstractmethod
    def get_memory_statistics(self, agent_id: str) -> Dict[str, Any]:
        """Statistiques sur la mémoire (taille, nb tours, etc.)"""
        pass
```

---

### 3. Service Layer (Logique métier)

#### `AgentMemoryCoordinator`
```python
class AgentMemoryCoordinator:
    """
    Coordonne l'accès aux mémoires des agents.
    Centralise la logique de gestion mémoire multi-agents.

    Responsabilités:
    - Isolation des mémoires par agent
    - Accès cross-agent sécurisé
    - Cache des contextes fréquemment accédés
    - Nettoyage automatique (LRU, TTL)
    """

    def __init__(
        self,
        memory_repository: MemoryRepository,
        cache_strategy: Optional[CacheStrategy] = None
    ):
        self._memory_repository = memory_repository
        self._cache = cache_strategy or LRUCache(max_size=100)
        self._memory_managers: Dict[str, MemoryManager] = {}

    def get_or_create_memory_manager(
        self,
        agent_identity: AgentIdentity
    ) -> MemoryManager:
        """
        Récupère ou crée un MemoryManager pour un agent.
        Utilise lazy loading + cache.
        """
        agent_id = agent_identity.agent_id

        if agent_id not in self._memory_managers:
            memory_manager = MemoryManager(
                agent_id=agent_id,
                agent_name=agent_identity.agent_name
            )
            self._memory_managers[agent_id] = memory_manager

        return self._memory_managers[agent_id]

    def build_cross_agent_context(
        self,
        requesting_agent_id: str,
        other_agent_ids: List[str],
        max_turns_per_agent: int = 5
    ) -> CrossAgentContext:
        """
        Construit un contexte partagé entre plusieurs agents.
        Utilisé pour la collaboration inter-agents.
        """
        contexts = []

        for agent_id in other_agent_ids:
            if agent_id == requesting_agent_id:
                continue

            history = self._memory_repository.get_conversation_history(
                agent_id=agent_id,
                max_turns=max_turns_per_agent
            )
            contexts.append({
                "agent_id": agent_id,
                "history": history
            })

        return CrossAgentContext(
            requesting_agent_id=requesting_agent_id,
            shared_contexts=contexts
        )

    def cleanup_inactive_memories(self, inactive_threshold_hours: int = 24):
        """
        Nettoie les mémoires des agents inactifs.
        Stratégie de gestion mémoire pour scalabilité.
        """
        # Implémentation du nettoyage
        pass
```

#### `AgentPromptConstructor`
```python
class AgentPromptConstructor:
    """
    Construit des prompts spécifiques pour chaque agent.
    Utilise le pattern Builder pour composition flexible.

    Responsabilités:
    - Construction du system prompt avec capacités
    - Intégration de l'historique
    - Injection du contexte cross-agent
    - Cache des prompts compilés
    """

    def __init__(
        self,
        agent_capabilities: AgentCapabilities,
        memory_coordinator: AgentMemoryCoordinator
    ):
        self._capabilities = agent_capabilities
        self._memory_coordinator = memory_coordinator
        self._system_prompt_cache: Optional[str] = None

    def build_system_prompt(self) -> str:
        """
        Construit le system prompt avec cache.
        Format:
            You are {name}: {description}

            Capabilities:
            - {capability_1}
            - {capability_2}

            Available tools:
            - {tool_1}: {description}
            - {tool_2}: {description}
        """
        if self._system_prompt_cache is not None:
            return self._system_prompt_cache

        prompt = self._construct_system_prompt()
        self._system_prompt_cache = prompt
        return prompt

    def build_conversation_messages(
        self,
        conversation_context: ConversationContext
    ) -> List[Message]:
        """
        Construit les messages de conversation depuis le contexte.
        """
        messages = []

        # System prompt
        messages.append({
            "role": "system",
            "content": self.build_system_prompt()
        })

        # Historique
        for turn in conversation_context.conversation_history:
            messages.append({
                "role": turn["role"],
                "content": turn["content"]
            })

        return messages

    def build_with_cross_agent_context(
        self,
        conversation_context: ConversationContext,
        cross_agent_context: CrossAgentContext
    ) -> List[Message]:
        """
        Construit les messages avec contexte d'autres agents.
        Utilisé pour collaboration inter-agents.
        """
        messages = self.build_conversation_messages(conversation_context)

        # Injecter contexte cross-agent avant le dernier message
        context_message = self._format_cross_agent_context(cross_agent_context)
        messages.insert(-1, {
            "role": "system",
            "content": context_message
        })

        return messages
```

#### `AgentExecutionService`
```python
class AgentExecutionService:
    """
    Service d'exécution des agents avec traçabilité complète.

    Responsabilités:
    - Préparation du contexte
    - Exécution de l'agent
    - Post-traitement des résultats
    - Logging et métriques
    """

    def __init__(
        self,
        agent_repository: AgentRepository,
        memory_coordinator: AgentMemoryCoordinator
    ):
        self._agent_repository = agent_repository
        self._memory_coordinator = memory_coordinator

    def execute_agent(
        self,
        agent_id: str,
        user_input: str,
        execution_options: Optional[ExecutionOptions] = None
    ) -> AgentExecutionResult:
        """
        Exécute un agent avec traçabilité complète.

        Returns:
            AgentExecutionResult avec output, métriques, traces
        """
        # 1. Récupérer l'agent
        agent = self._agent_repository.find_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent {agent_id} not found")

        # 2. Vérifier que l'agent est actif
        if not agent.is_active:
            raise AgentInactiveError(f"Agent {agent_id} is inactive")

        # 3. Préparer le contexte d'exécution
        execution_context = self._prepare_execution_context(
            agent=agent,
            user_input=user_input,
            options=execution_options
        )

        # 4. Exécuter l'agent avec métriques
        start_time = time.time()

        try:
            output = agent.execute(user_input)
            success = output.success
            error = output.error

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            output = AgentOutput(
                response=f"Execution error: {str(e)}",
                success=False,
                error=str(e)
            )
            success = False
            error = str(e)

        execution_time = time.time() - start_time

        # 5. Créer le résultat avec métriques
        result = AgentExecutionResult(
            agent_id=agent_id,
            agent_name=agent.identity.agent_name,
            output=output,
            execution_time_seconds=execution_time,
            success=success,
            error=error,
            timestamp=datetime.now()
        )

        # 6. Logger les métriques
        self._log_execution_metrics(result)

        return result
```

#### `AgentRoutingService`
```python
class AgentRoutingService:
    """
    Service de routage intelligent vers le bon agent.
    Utilise le pattern Strategy pour différentes stratégies.

    Stratégies possibles:
    - Rule-based (keywords, patterns)
    - ML-based (classification)
    - LLM-based (ask LLM to choose)
    """

    def __init__(
        self,
        agent_repository: AgentRepository,
        routing_strategy: RoutingStrategy
    ):
        self._agent_repository = agent_repository
        self._routing_strategy = routing_strategy

    def route_to_best_agent(
        self,
        user_input: str,
        context: Optional[RoutingContext] = None
    ) -> AgentRoutingDecision:
        """
        Détermine quel agent est le plus approprié.

        Returns:
            AgentRoutingDecision avec agent_id, confidence, reasoning
        """
        available_agents = self._agent_repository.find_all()

        # Filtrer les agents actifs
        active_agents = [a for a in available_agents if a.is_active]

        if not active_agents:
            raise NoActiveAgentsError("No active agents available")

        # Utiliser la stratégie de routage
        decision = self._routing_strategy.decide(
            user_input=user_input,
            available_agents=active_agents,
            context=context
        )

        return decision
```

---

### 4. Orchestration Layer

#### `MultiAgentOrchestrator`
```python
class MultiAgentOrchestrator:
    """
    Orchestrateur principal du système multi-agents.
    Point d'entrée unique pour toutes les opérations.

    Responsabilités:
    - Coordination globale
    - Gestion du cycle de vie des agents
    - Routing des requêtes
    - Monitoring et métriques
    """

    def __init__(
        self,
        llm_config: LLMWrapperConfig,
        agent_repository: AgentRepository,
        memory_repository: MemoryRepository,
        agent_factory: AgentFactory,
        routing_service: Optional[AgentRoutingService] = None
    ):
        self._llm_config = llm_config
        self._agent_repository = agent_repository
        self._memory_repository = memory_repository
        self._agent_factory = agent_factory

        # Services
        self._memory_coordinator = AgentMemoryCoordinator(memory_repository)
        self._execution_service = AgentExecutionService(
            agent_repository,
            self._memory_coordinator
        )
        self._routing_service = routing_service

        # État
        self._active_agent_id: Optional[str] = None
        self._orchestrator_metrics = OrchestratorMetrics()

    def register_agents(
        self,
        agents_configs: List[AgentConfig]
    ) -> List[AgentIdentity]:
        """
        Enregistre plusieurs agents depuis leurs configurations.
        Utilise la factory pour création.

        Returns:
            Liste des identités des agents créés
        """
        registered_identities = []

        for config in agents_configs:
            identity = self._register_single_agent(config)
            registered_identities.append(identity)

        # Définir le premier agent comme actif par défaut
        if registered_identities and not self._active_agent_id:
            self._active_agent_id = registered_identities[0].agent_id

        return registered_identities

    def process_user_input(
        self,
        user_input: str,
        agent_id: Optional[str] = None,
        use_routing: bool = False
    ) -> AgentExecutionResult:
        """
        Traite l'input utilisateur.

        Modes:
        1. agent_id spécifié → utilise cet agent
        2. use_routing=True → route vers le meilleur agent
        3. Défaut → utilise l'agent actif
        """
        # Déterminer l'agent à utiliser
        target_agent_id = self._determine_target_agent(
            user_input=user_input,
            agent_id=agent_id,
            use_routing=use_routing
        )

        # Exécuter
        result = self._execution_service.execute_agent(
            agent_id=target_agent_id,
            user_input=user_input
        )

        # Mettre à jour les métriques
        self._orchestrator_metrics.record_execution(result)

        return result

    def get_agent_by_name(self, agent_name: str) -> Optional[RegisteredAgent]:
        """Récupère un agent par son nom"""
        return self._agent_repository.find_by_name(agent_name)

    def list_all_agents(self) -> List[AgentSummary]:
        """
        Liste tous les agents avec leurs statistiques.

        Returns:
            Liste de AgentSummary (lightweight DTO)
        """
        agents = self._agent_repository.find_all()

        summaries = []
        for agent in agents:
            summary = AgentSummary(
                agent_id=agent.identity.agent_id,
                agent_name=agent.identity.agent_name,
                description=agent.capabilities.description,
                specializations=agent.capabilities.specialization_tags,
                total_interactions=agent.total_interactions,
                is_active=agent.is_active,
                last_interaction=agent.last_interaction_timestamp
            )
            summaries.append(summary)

        return summaries

    def switch_active_agent(self, agent_id: str) -> bool:
        """Change l'agent actif"""
        agent = self._agent_repository.find_by_id(agent_id)
        if not agent:
            return False

        self._active_agent_id = agent_id
        return True

    def get_orchestrator_metrics(self) -> OrchestratorMetrics:
        """Métriques globales de l'orchestrateur"""
        return self._orchestrator_metrics
```

#### `AgentFactory`
```python
class AgentFactory:
    """
    Factory pour création d'agents.
    Centralise la logique de création complexe.

    Pattern: Abstract Factory + Builder
    """

    def __init__(
        self,
        llm_wrapper: LLMWrapper,
        tool_scheduler: ToolScheduler,
        memory_coordinator: AgentMemoryCoordinator
    ):
        self._llm = llm_wrapper
        self._tool_scheduler = tool_scheduler
        self._memory_coordinator = memory_coordinator

    def create_agent(self, config: AgentConfig) -> RegisteredAgent:
        """
        Crée un agent complet depuis sa configuration.

        Steps:
        1. Créer l'identité
        2. Créer les capacités
        3. Créer le memory manager
        4. Créer le prompt constructor
        5. Créer l'instance d'agent
        6. Assembler le RegisteredAgent
        """
        # 1. Créer l'identité
        identity = AgentIdentity(
            agent_id=self._generate_agent_id(),
            agent_name=config.name,
            creation_timestamp=datetime.now()
        )

        # 2. Créer les capacités
        capabilities = AgentCapabilities(
            description=config.description,
            authorized_tools=config.tools,
            max_reasoning_turns=config.max_agent_turns,
            max_memory_turns=config.max_history_turns,
            specialization_tags=self._extract_specializations(config)
        )

        # 3. Memory manager
        memory_manager = self._memory_coordinator.get_or_create_memory_manager(
            identity
        )

        # 4. Prompt constructor
        prompt_constructor = AgentPromptConstructor(
            agent_capabilities=capabilities,
            memory_coordinator=self._memory_coordinator
        )

        # 5. Créer le prompt builder pour l'agent
        prompt_builder = PromptBuilderAdapter(
            prompt_constructor=prompt_constructor,
            agent_identity=identity,
            memory_manager=memory_manager
        )

        # 6. Créer l'instance d'agent
        agent_instance = DefaultAgent(
            llm=self._llm,
            tool_scheduler=self._tool_scheduler,
            prompt_builder=prompt_builder,
            memory_manager=memory_manager,
            config=config
        )

        # 7. Assembler
        registered_agent = RegisteredAgent(
            identity=identity,
            capabilities=capabilities,
            agent_instance=agent_instance,
            memory_manager=memory_manager,
            prompt_constructor=prompt_constructor
        )

        return registered_agent

    def _generate_agent_id(self) -> str:
        """Génère un ID unique (UUID v4)"""
        return str(uuid.uuid4())

    def _extract_specializations(self, config: AgentConfig) -> List[str]:
        """Extrait les tags de spécialisation depuis la config"""
        # Analyser les tools pour déduire les spécialisations
        # Ex: git_tools → tag "git", file_tools → tag "files"
        pass
```

---

## 🔄 Plan d'implémentation progressif

### Phase 1: Domain + Repository Layer (3-4 jours)
**Objectif**: Établir les fondations solides

#### Étape 1.1: Créer les Value Objects
- `AgentIdentity` (`core/domain/agent_identity.py`)
- `AgentCapabilities` (`core/domain/agent_capabilities.py`)
- `ConversationContext` (`core/domain/conversation_context.py`)

#### Étape 1.2: Créer les Entities
- `RegisteredAgent` (`core/domain/registered_agent.py`)

#### Étape 1.3: Créer les Repository Interfaces
- `AgentRepository` (`core/repositories/agent_repository.py`)
- `MemoryRepository` (`core/repositories/memory_repository.py`)

#### Étape 1.4: Implémenter les Repositories
- `InMemoryAgentRepository` (`core/repositories/in_memory_agent_repository.py`)
- `InMemoryMemoryRepository` (`core/repositories/in_memory_memory_repository.py`)

#### Étape 1.5: Tests unitaires
- Tests des Value Objects (immutabilité, validation)
- Tests des Repositories (CRUD, thread-safety)

---

### Phase 2: Service Layer
**Objectif**: Implémenter la logique métier

#### Étape 2.1: AgentMemoryCoordinator
- Créer `AgentMemoryCoordinator` (`core/services/agent_memory_coordinator.py`)
- Implémenter cache strategy (LRU)
- Tests d'isolation mémoire

#### Étape 2.2: AgentPromptConstructor
- Créer `AgentPromptConstructor` (`core/services/agent_prompt_constructor.py`)
- Implémenter cache de prompts
- Tests de construction de prompts

#### Étape 2.3: AgentExecutionService
- Créer `AgentExecutionService` (`core/services/agent_execution_service.py`)
- Implémenter métriques et logging
- Tests d'exécution

#### Étape 2.4: AgentRoutingService (Optionnel)
- Créer interface `RoutingStrategy` (`core/services/routing/routing_strategy.py`)
- Implémenter `RuleBasedRoutingStrategy`
- Créer `AgentRoutingService`
- Tests de routage

---

### Phase 3: Orchestration Layer
**Objectif**: Assembler les composants

#### Étape 3.1: AgentFactory
- Créer `AgentFactory` (`core/orchestration/agent_factory.py`)
- Implémenter création complète d'agents
- Tests de factory

#### Étape 3.2: MultiAgentOrchestrator
- Créer `MultiAgentOrchestrator` (`core/orchestration/multi_agent_orchestrator.py`)
- Implémenter enregistrement d'agents
- Implémenter exécution avec routing
- Tests d'orchestration

#### Étape 3.3: Métriques et Monitoring
- Créer `OrchestratorMetrics` (`core/orchestration/metrics.py`)
- Implémenter collecte de métriques
- Dashboard de métriques (optionnel)

---

### Phase 4: Adaptation des couches existantes
**Objectif**: Intégrer avec le code existant

#### Étape 4.1: Adapter MemoryManager
- Ajouter `agent_id` et `agent_name`
- Implémenter marquage `from: <agent_name>`
- Maintenir compatibilité

#### Étape 4.2: Créer PromptBuilderAdapter
- Adapter entre ancien PromptBuilder et nouveau AgentPromptConstructor
- Tests d'adaptation

#### Étape 4.3: Modifier main.py
- Créer configurations multi-agents
- Utiliser `MultiAgentOrchestrator`
- Tests end-to-end

---

### Phase 5: Fonctionnalités avancées (optionnel)
**Objectif**: Features avancées et optimisations

#### Étape 5.1: Persistance
- Implémenter `FileSystemMemoryRepository`
- Implémenter `FileSystemAgentRepository`
- Tests de persistance

#### Étape 5.2: Collaboration inter-agents
- Créer `AgentCoordinationService`
- Implémenter délégation entre agents
- Tests de collaboration

#### Étape 5.3: Commandes CLI
- `/agents list` - Liste des agents
- `/agent switch <name>` - Changer d'agent
- `/agent info <name>` - Info d'un agent
- `/agent stats` - Statistiques

#### Étape 5.4: Optimisations
- Implémenter lazy loading
- Ajouter pagination historique
- Implémenter stratégies de cache avancées

---

## 📂 Structure de fichiers finale

```
core/
├── domain/                                 (Phase 1)
│   ├── __init__.py
│   ├── agent_identity.py                  Value Object
│   ├── agent_capabilities.py              Value Object
│   ├── registered_agent.py                Entity
│   ├── conversation_context.py            Value Object
│   └── cross_agent_context.py             Value Object
│
├── repositories/                           (Phase 1)
│   ├── __init__.py
│   ├── agent_repository.py                Interface
│   ├── memory_repository.py               Interface
│   ├── in_memory_agent_repository.py      Implémentation
│   └── in_memory_memory_repository.py     Implémentation
│
├── services/                               (Phase 2)
│   ├── __init__.py
│   ├── agent_memory_coordinator.py        Service
│   ├── agent_prompt_constructor.py        Service
│   ├── agent_execution_service.py         Service
│   ├── agent_routing_service.py           Service
│   └── routing/
│       ├── routing_strategy.py            Interface
│       ├── rule_based_routing.py          Implémentation
│       └── llm_based_routing.py           Implémentation
│
├── orchestration/                          (Phase 3)
│   ├── __init__.py
│   ├── multi_agent_orchestrator.py        Orchestrateur principal
│   ├── agent_factory.py                   Factory
│   ├── agent_lifecycle_manager.py         Gestion cycle de vie
│   └── metrics.py                         Métriques
│
├── adapters/                               (Phase 4)
│   ├── __init__.py
│   └── prompt_builder_adapter.py          Adapter ancien/nouveau
│
└── cache/                                  (Phase 5)
    ├── __init__.py
    ├── cache_strategy.py                   Interface
    └── lru_cache.py                        Implémentation LRU
```

---

## 🎯 Patterns de conception utilisés

### 1. Repository Pattern
- **Quoi**: Abstraction de la couche de persistance
- **Pourquoi**: Découplage, testabilité, flexibilité de stockage
- **Où**: `AgentRepository`, `MemoryRepository`

### 2. Factory Pattern
- **Quoi**: Création d'objets complexes
- **Pourquoi**: Centraliser logique de création, masquer complexité
- **Où**: `AgentFactory`

### 3. Strategy Pattern
- **Quoi**: Algorithmes interchangeables
- **Pourquoi**: Flexibilité des stratégies de routage
- **Où**: `RoutingStrategy`, `CacheStrategy`

### 4. Adapter Pattern
- **Quoi**: Adaptation d'interfaces incompatibles
- **Pourquoi**: Compatibilité avec code existant
- **Où**: `PromptBuilderAdapter`

### 5. Value Object Pattern
- **Quoi**: Objets immuables identifiés par valeur
- **Pourquoi**: Intégrité, thread-safety, cache
- **Où**: `AgentIdentity`, `AgentCapabilities`, `ConversationContext`

### 6. Service Layer Pattern
- **Quoi**: Logique métier dans services dédiés
- **Pourquoi**: Séparation responsabilités, réutilisabilité
- **Où**: `AgentExecutionService`, `AgentMemoryCoordinator`

---

## ⚡ Considérations de scalabilité

### 1. Lazy Loading
```python
# Charger les agents uniquement quand nécessaire
def get_agent(self, agent_id: str) -> RegisteredAgent:
    if agent_id not in self._loaded_agents:
        agent = self._repository.find_by_id(agent_id)
        self._loaded_agents[agent_id] = agent
    return self._loaded_agents[agent_id]
```

### 2. Cache multi-niveaux
```python
# L1: Prompts compilés (mémoire)
# L2: Contextes de conversation (mémoire, LRU)
# L3: Historiques complets (disque, lazy)
```

### 3. Pagination
```python
# Ne jamais charger tout l'historique
def get_history(self, agent_id: str, page: int = 0, size: int = 50):
    offset = page * size
    return self._repository.get_history(agent_id, limit=size, offset=offset)
```

### 4. Thread-safety
```python
# Utiliser RLock pour accès concurrent
from threading import RLock

class ThreadSafeRepository:
    def __init__(self):
        self._lock = RLock()

    def register(self, agent):
        with self._lock:
            # Operations atomiques
            pass
```

### 5. Nettoyage automatique
```python
# TTL pour mémoires inactives
def cleanup_inactive(self, hours_threshold: int = 24):
    now = datetime.now()
    for agent_id, last_active in self._last_active.items():
        if (now - last_active).hours > hours_threshold:
            self._unload_agent(agent_id)
```

---

## 🧪 Stratégie de tests

### Tests unitaires (80% couverture)
```python
# test_agent_identity.py
def test_agent_identity_immutability()
def test_agent_identity_validation()

# test_agent_repository.py
def test_register_agent()
def test_find_by_id()
def test_thread_safety()

# test_agent_memory_coordinator.py
def test_memory_isolation()
def test_cross_agent_context()
```

### Tests d'intégration (composants)
```python
# test_orchestrator_integration.py
def test_register_and_execute_agent()
def test_agent_switching()
def test_routing_to_correct_agent()
```

### Tests end-to-end (workflow complet)
```python
# test_e2e_multi_agent.py
def test_complete_multi_agent_workflow()
def test_multiple_agents_with_memory_isolation()
def test_cross_agent_collaboration()
```

---

## 📊 Métriques et monitoring

### Métriques par agent
- Nombre total d'interactions
- Temps moyen d'exécution
- Taux de succès
- Temps depuis dernière utilisation
- Taille mémoire utilisée

### Métriques orchestrateur
- Nombre total d'agents actifs
- Distribution des requêtes par agent
- Performance globale
- Cache hit rate
- Erreurs par type

### Dashboard (optionnel)
```python
orchestrator.get_metrics_summary()
# {
#   "total_agents": 5,
#   "active_agents": 3,
#   "total_executions": 1523,
#   "success_rate": 0.97,
#   "avg_execution_time": 2.3,
#   "cache_hit_rate": 0.85,
#   "agents": [
#     {
#       "name": "CodeAgent",
#       "executions": 543,
#       "success_rate": 0.98,
#       "avg_time": 2.1
#     },
#     ...
#   ]
# }
```


