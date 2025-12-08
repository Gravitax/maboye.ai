# Development Roadmap

Complete step-by-step plan to build a Claude Code-like agent system.

---

implementer l'enumType {
    lambda,
    code,
    function,
    text_analyse
}
dans agent query return type lambda par defaut

modifier la gestion de la memoire pour respecter ce format {
    memoryType, enumType, id, rawString, embedString
}

trouver une fonction pour embed sans passer par un llm pour reduire le cout en token

associer des mots clefs au type pour faire une comparaison vectorielle avec les chunks de memoire

implementer la recherche en memoire: comparer les elements du meme type vectoriellement avec la query et selectionner uniquement les meilleurs chunks

creer le contexte avec la query + la memoire

ameliorer l'archi de l'orchestrator en mettant une enumAgent en place avec tout les agents dedans, toutes les init ce feront sur une loop de cette enum

implementer une classe PromptManager qui gerera des fichiers de prompt (format texte) et les associera avec des ID issus des enum des types et des agents
PM.get(enumID) => prompt: string
PM.get(list of enumID) => dict[enumID, string]
PM.set(enumID, prompt: string)
PM.set(dict[enumID, prompt: string])

dans un dossiers prompts/prompt_manager.py
on stockera les prompts dans le meme fichier dans un dict hors du scope
