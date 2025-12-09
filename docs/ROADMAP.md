# Feuille de Route (Roadmap) pour Maboye.ai (Version 2.0)

Cette feuille de route a été mise à jour pour refléter une compréhension plus profonde de l'architecture des assistants de code avancés comme Gemini CLI. Elle vise à guider l'évolution de `maboye.ai` vers un système plus robuste, intelligent et modulaire.

---

## Phase 1 : Mettre en Place un Cœur Fonctionnel

L'objectif est de passer d'un mock à un système capable de dialoguer avec un LLM et d'utiliser des outils de manière basique.

### 1.1. Implémenter un Client LLM Réel (Priorité Absolue)
*   **Objectif** : Remplacer le backend mock par une véritable connexion à un LLM via une URL.
*   **Actions** :
    1.  Dans votre classe `LLM`, implémentez la logique pour envoyer des requêtes HTTP (avec `requests` ou `httpx`) à l'URL configurée.
    2.  Gérez le formatage du `payload` (JSON) et le parsing de la réponse, en incluant une gestion d'erreurs robuste.

### 1.2. Créer un "Prompt Builder"
*   **Objectif** : Arrêter de construire les prompts manuellement dans le code. Centraliser la logique de construction des prompts.
*   **Actions** :
    1.  Créez une nouvelle classe `PromptBuilder` dans `srcs/`.
    2.  Cette classe aura des méthodes pour assembler les différentes parties du prompt : le prompt système (rôle de l'assistant), l'historique de la conversation, une description des outils disponibles, et la requête de l'utilisateur.
    3.  Votre `Orchestrator` utilisera ce `PromptBuilder` avant chaque appel au LLM.

### 1.3. Mettre en Place un "Tool Scheduler" de Base
*   **Objectif** : Créer un composant dédié à l'exécution des outils demandés par le LLM.
*   **Actions** :
    1.  Créez une classe `ToolScheduler` (ou `ToolExecutor`).
    2.  Le `ToolRegistry` (que vous avez via `register_all_tools`) lui fournira la liste des outils disponibles.
    3.  Après un appel au LLM, l'`Orchestrator` passera la réponse au `ToolScheduler`.
    4.  Le `ToolScheduler` sera responsable de :
        -   Détecter si la réponse du LLM est une demande d'appel d'outil (par ex., un JSON formaté).
        -   Valider l'appel.
        -   Exécuter l'outil correspondant.
        -   Retourner le résultat à l'`Orchestrator`.

---

## Phase 2 : Atteindre une Intelligence "Code-Aware"

Cette phase se concentre sur la capacité de l'assistant à comprendre et interagir avec une base de code.

### 2.1. Implémenter les Outils d'Exploration de Code
*   **Objectif** : Donner à l'assistant des "yeux et des mains" pour naviguer dans le code.
*   **Actions** :
    1.  **Outils Fondamentaux** : Assurez-vous que votre répertoire `tools/` contienne des implémentations robustes pour :
        -   `list_files`: Pour lister les fichiers (potentiellement de manière récursive).
        -   `read_file`: Pour lire le contenu d'un fichier (en entier ou des portions).
        -   `code_search`: Un outil de recherche de code. **Pensez à intégrer `ripgrep` via un sous-processus Python pour des performances maximales sur de grands projets.**
    2.  **Mise à jour du Prompt Builder** : Le `PromptBuilder` doit inclure une section expliquant au LLM comment utiliser ces outils (format de la demande JSON, etc.).

### 2.2. Le Cycle de Raisonnement Itératif
*   **Objectif** : Mettre en place la boucle "Raisonnement -> Outil -> Analyse" au cœur de l'`Orchestrator`.
*   **Actions** :
    1.  Modifiez la méthode `process_query` de l'`Orchestrator` pour qu'elle devienne une boucle.
    2.  **Dans la boucle** :
        -   Appel au LLM.
        -   La réponse est analysée par le `ToolScheduler`.
        -   Si un outil est appelé, son résultat est ajouté à l'historique de la conversation et la boucle continue (nouvel appel au LLM avec le résultat de l'outil).
        -   Si aucun outil n'est appelé, la réponse est considérée comme finale et est retournée à l'utilisateur.
    3.  Implémentez une limite de "tours" pour éviter les boucles infinies.

---

## Phase 3 : Vers un Assistant Spécialisé et Extensible

Cette phase transforme le projet en une plateforme flexible.

### 3.1. Créer votre Premier "Agent Spécialisé"
*   **Objectif** : Créer un agent autonome pour une tâche complexe, en s'inspirant du `codebase-investigator`.
*   **Actions** :
    1.  Dans votre répertoire `agents/`, définissez la structure d'un "Agent" (par ex., une classe `Agent` de base). Un agent aura son propre `PromptBuilder` et une liste d'outils spécifiques.
    2.  Créez un `CodebaseInvestigatorAgent`. Son prompt système lui demandera d'explorer un projet pour répondre à une question d'architecture.
    3.  **Intégration en tant qu'Outil** : Transformez cet agent en un outil que l'`Orchestrator` principal peut appeler. L'outil `run_codebase_investigator` prendra une question en argument et retournera le rapport final de l'agent.

### 3.2. Améliorer la Gestion du Contexte
*   **Objectif** : Fournir un contexte plus riche et automatique au LLM.
*   **Actions** :
    1.  Créez des "Services de Contexte" (par ex. `srcs/context_services/`).
    2.  Implémentez un `GitContextService` qui, avant chaque prompt, ajoute automatiquement des informations pertinentes (branche actuelle, `git diff --stat`, etc.).
    3.  Le `PromptBuilder` appellera ces services pour enrichir le prompt.

### 3.3. Streaming et Expérience Utilisateur
*   **Objectif** : Rendre l'interface plus réactive.
*   **Actions** :
    1.  Modifiez le client `LLM` et l'`Orchestrator` pour gérer les réponses en streaming.
    2.  Affichez les "pensées" (`thoughts`) et les appels d'outils en temps réel dans le terminal pour que l'utilisateur puisse suivre le raisonnement de l'assistant.