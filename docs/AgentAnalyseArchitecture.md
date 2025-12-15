Voici le plan détaillé du cycle de vie de l’agent lors de l'analyse d'architecture.

1. Démarrage (Bootstrapping)
La boucle commence immédiatement après la réception de la commande utilisateur.

Déclencheur : Prompt utilisateur (ex: "Analyse l'architecture").

Query LLM Initial (T=0) :

Data envoyée : System Prompt (définitions des outils ls, read_file, grep, etc.) + Prompt Utilisateur.

Décision du LLM : Le modèle ne peut pas encore répondre. Il génère un appel d'outil (Tool Call) pour explorer, généralement une commande de listage (ls -R).

2. La Boucle d'Action (The Agent Loop)
Le processus est itératif. Chaque itération suit strictement les étapes suivantes :

A. Exécution de l'Outil (Environment Interaction)
Action : L'agent exécute la commande demandée par le LLM à l'étape précédente (ex: lecture de package.json).

Capture : L'agent récupère le résultat brut (stdout) ou l'erreur (stderr).

B. Construction du Contexte
Action : L'agent ajoute le résultat de l'exécution à l'historique de la conversation (History Chain).

Data accumulée :

Instructions initiales.

Historique des actions précédentes (ce qui a déjà été lu).

Dernier résultat obtenu (le contenu du fichier lu ou l'arborescence).

C. Query LLM (Prise de Décision)
Quand : Une fois le résultat de l'outil disponible.

Data envoyée au LLM : L'historique complet (ou tronqué/résumé si dépassement de la fenêtre de contexte).

Raisonnement du LLM (Interne) :

Analyse : "J'ai lu le main.py, je vois un import de utils/db.py."

Décision : "Je dois maintenant lire utils/db.py pour comprendre la couche de données."

Sortie du LLM : Un nouveau Tool Call (ex: read_file path="utils/db.py").

(Retour à l'étape A avec la nouvelle commande)

3. Terminaison (Arrêt de la boucle)
La boucle se termine lors de la phase Query LLM (C), selon deux cas de figure :

Condition de Succès (Convergence) :

Le LLM évalue que les informations accumulées dans le contexte sont suffisantes pour satisfaire la demande (compréhension globale de l'architecture).

Action : Au lieu de renvoyer un Tool Call, le LLM renvoie une réponse textuelle finale (le rapport d'analyse).

Conditions d'Échec ou de Sécurité :

Max Iterations : Le nombre de boucles prédéfini (ex: 30 étapes) est atteint.

Token Limit : Le contexte est saturé et aucune stratégie de compression ne permet de continuer.

Stagnation : Le LLM répète la même commande erronée plusieurs fois.