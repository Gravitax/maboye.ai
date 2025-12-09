# Feuille de Route (Roadmap) pour Maboye.ai (Version 3.0)

Cette feuille de route guide l'évolution de `maboye.ai` vers un assistant de code avancé inspiré de Claude Code et Gemini CLI, capable d'analyser, générer, refactoriser et maintenir du code de manière autonome.

---

## État Actuel (Janvier 2025)

### Architecture de Base
- **Agents modulaires**: Architecture basée sur des agents spécialisés (DefaultAgent)
- **Orchestrateur**: Gestion centralisée des agents et coordination des tâches
- **Système de mémoire**: Stockage et récupération des conversations et contextes
- **Interface CLI**: Terminal interactif avec gestion des commandes via CommandManager
- **LLM Wrapper**: Abstraction pour l'intégration de différents modèles (Gemini, Anthropic)
- **Logging structuré**: Système de logs avec différents niveaux de verbosité

### Standards de Code
- Convention snake_case stricte
- Fonctions courtes et à responsabilité unique
- Documentation professionnelle, sans emojis
- Flux de contrôle simplifié

---

## Phase 1: Fondations du Système de Fichiers (Q1 2025)

### 1.1 Outils de Manipulation de Fichiers

**Priorité: HAUTE**

Implémenter les outils essentiels pour la manipulation de fichiers:

- [ ] **ReadTool**: Lecture de fichiers avec support de:
  - Offset et limit pour les gros fichiers
  - Détection automatique de l'encodage
  - Support des images (PNG, JPG) via vision
  - Support des PDFs et notebooks (.ipynb)

- [ ] **WriteTool**: Écriture de fichiers avec:
  - Vérification de l'existence avant écrasement
  - Création de répertoires parents si nécessaire
  - Validation du contenu avant écriture

- [ ] **EditTool**: Édition précise de fichiers avec:
  - Remplacement exact de chaînes (old_string → new_string)
  - Option replace_all pour renommage de variables
  - Préservation de l'indentation
  - Validation que old_string est unique

- [ ] **GlobTool**: Recherche de fichiers par patterns avec:
  - Support des glob patterns (**.js, src/**/*.ts)
  - Tri par date de modification
  - Cache des résultats pour optimisation

- [ ] **GrepTool**: Recherche de contenu avec:
  - Support regex complet
  - Filtrage par type de fichier
  - Modes: content, files_with_matches, count
  - Support multiline
  - Context lines (-A, -B, -C)

### 1.2 Validation et Sécurité

- [ ] Détection de fichiers sensibles (.env, credentials.json)
- [ ] Prévention de l'écrasement accidentel
- [ ] Sandbox pour l'exécution de commandes
- [ ] Validation des chemins pour éviter les directory traversal

---

## Phase 2: Système d'Outils Avancé (Q2 2025)

### 2.1 Outils de Développement

**Priorité: HAUTE**

- [ ] **BashTool**: Exécution de commandes shell avec:
  - Timeout configurable
  - Capture stdout/stderr
  - Support des commandes longues en arrière-plan
  - Gestion des hooks (pre/post execution)
  - Historique des commandes

### 2.2 Outils d'Analyse de Code

- [ ] **ASTAnalyzer**: Analyse syntaxique du code
  - Détection des fonctions, classes, imports
  - Calcul de métriques (complexité cyclomatique)
  - Détection de code mort

- [ ] **DependencyAnalyzer**: Analyse des dépendances
  - Graphe de dépendances du projet
  - Détection de dépendances circulaires
  - Suggestion de refactoring

- [ ] **TestRunner**: Exécution de tests
  - a definir

---

## Phase 3: Agents Spécialisés (Q2-Q3 2025)

### 3.1 Agent de Code (CodeAgent)

**Priorité: HAUTE**

creer un agent de code:

- [ ] **Analyse de codebase**:
  - Compréhension de l'architecture globale
  - Détection des patterns utilisés
  - Identification des conventions de codage

- [ ] **Génération de code**:
  - Respect des conventions du projet
  - Génération de tests automatiques
  - Documentation inline

- [ ] **Refactoring intelligent**:
  - Extraction de méthodes/classes
  - Simplification de code complexe
  - Application des design patterns

- [ ] **Validation continue**:
  - Exécution des tests après modifications
  - Vérification de la syntaxe
  - Linting automatique

### 3.2 Agent Explorateur (ExploreAgent)

**Priorité: MOYENNE**

agent pour l'exploration de codebase:

- [ ] Recherche rapide par patterns
- [ ] Recherche par mots-clés
- [ ] Réponse aux questions sur la structure
- [ ] Niveaux de thoroughness: quick, medium, very thorough
- [ ] Cartographie du projet

### 3.3 Agent Planificateur (PlanAgent)

**Priorité: MOYENNE**

agent pour la planification d'implémentation:

- [ ] Analyse des tâches complexes
- [ ] Génération de plans step-by-step
- [ ] Identification des fichiers critiques
- [ ] Évaluation des trade-offs architecturaux
- [ ] Validation du plan avec l'utilisateur

### 3.4 Agents Spécialisés Additionnels

- [ ] **ReviewAgent**: Revue de code automatique
- [ ] **DocumentationAgent**: Génération de documentation
- [ ] **SecurityAgent**: Analyse de sécurité
- [ ] **PerformanceAgent**: Optimisation de performance

---

## Phase 4: Gestion du Contexte Avancée (Q3 2025)

### 4.1 Système de Mémoire Hiérarchique

**Priorité: HAUTE**

Améliorer le système de mémoire actuel:

- [ ] **Mémoire de travail** (Working Memory):
  - Contexte de la session courante
  - Fichiers récemment modifiés
  - Commandes récentes

- [ ] **Mémoire sémantique** (Semantic Memory):
  - Connaissances sur le projet
  - Patterns identifiés
  - Conventions de codage

- [ ] **Mémoire épisodique** (Episodic Memory):
  - Historique des conversations
  - Décisions prises et rationale
  - Erreurs rencontrées et solutions

### 4.2 Résumé Automatique

- [ ] Détection du contexte qui dépasse la limite
- [ ] Résumé intelligent des conversations longues
- [ ] Préservation des informations critiques
- [ ] Compression des logs d'outils

### 4.3 Contexte de Projet

- [ ] Détection automatique du type de projet
- [ ] Chargement de conventions spécifiques
- [ ] Index des fichiers importants
- [ ] Graphe de dépendances en cache

---

## Phase 5: Interaction Intelligente (Q4 2025)

### 5.1 Mode Plan

**Priorité: HAUTE**

Implémenter un mode de planification:

- [ ] Entrée automatique pour tâches complexes
- [ ] Exploration de la codebase avant implémentation
- [ ] Génération de plan détaillé
- [ ] Validation utilisateur avant exécution
- [ ] Sortie du mode plan avec approbation

### 5.2 Questions à l'Utilisateur

- [ ] AskUserQuestion pour clarifications
- [ ] Support de questions multiples (1-4)
- [ ] Support multi-select
- [ ] Recommandations dans les options
- [ ] Validation des réponses

### 5.3 Todo List Interactive

**Priorité: MOYENNE**

- [ ] Création automatique pour tâches complexes
- [ ] États: pending, in_progress, completed
- [ ] Mise à jour en temps réel
- [ ] Affichage dans le terminal
- [ ] Persistance entre sessions

### 5.4 Streaming des Réponses

- [ ] Affichage progressif des réponses
- [ ] Indicateurs de progression pour outils
- [ ] Annulation de tâches en cours
- [ ] Feedback en temps réel

---

## Phase 7: Intelligence Avancée

### 7.1 Apprentissage et Adaptation

- [ ] Apprentissage des préférences utilisateur
- [ ] Adaptation au style de code du projet
- [ ] Suggestion proactive d'améliorations
- [ ] Détection de patterns récurrents

### 7.2 Multi-Agent Orchestration

**Priorité: MOYENNE**

- [ ] Coordination de plusieurs agents en parallèle
- [ ] Swarm d'agents pour tâches complexes
- [ ] Communication inter-agents
- [ ] Résolution de conflits entre agents

### 7.3 Analyse Prédictive

- [ ] Prédiction de bugs potentiels
- [ ] Suggestion de refactoring préventif
- [ ] Détection de code smell
- [ ] Estimation de complexité

### 7.4 Génération de Tests Intelligente

- [ ] Tests unitaires automatiques
- [ ] Tests d'intégration
- [ ] Tests de régression
- [ ] Property-based testing

---
