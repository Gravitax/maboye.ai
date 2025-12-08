# Development Roadmap

Complete step-by-step plan to build a Claude Code-like agent system.

---

il faut creer orchestrator.py

la classe orchestrator est une classe qui manage l'utilisation de different agents

elle prend un input issu de la classe terminal, le fait traiter par plusieurs agents, et sort un resultat a output sur le terminal


il prend la query user en input
{
    il la fait reformater par agents/agent_queries.py
}

il utilise l'agent_context.py pour creer un context a envoyer au llm
{
    l'agent utilisera la memory et la query pour creer le contexte
}

il utilise l'agent_code.py pour executer la liste d'instructions recu du llm
{
    le llm envoit une liste de commandes a executer et c'est cet agent qui va le faire
}

il utilise la classe memory.py pour stocker:
- les queries
- les contexts
- les etapes d'executions
- les resultats d'executions
{
    cette classe permet de gerer un historique sur plusieurs elements
    il faut une classe mere
    et des enfants qui en herite pour chaque type de memoire (queries, context, etc...) (tout dans memory.py)
    la classe gere le stockage des data aux bons endroits et renvoit l'historique demander

    il faut utiliser une enum pour les query d'historique :
    get(enumID)
    set(enumID, data)
}
