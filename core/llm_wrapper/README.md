# LLM Wrapper

Wrapper Python pour interagir avec l'API LLM backend. Fournit une abstraction simple pour les appels d'API avec gestion automatique de l'authentification et des erreurs.

## Configuration

```python
from core.llm_wrapper.llm_wrapper import LLMWrapper, LLMWrapperConfig

# Configuration par défaut (depuis variables d'environnement)
wrapper = LLMWrapper()

# Configuration personnalisée
config = LLMWrapperConfig(
    base_url="https://192.168.239.20",
    api_service="api/v1",        # Service pour chat/completions
    embed_service="embed/v1",     # Service pour embeddings
    model="Mistral-Small",
    temperature=0.7,
    max_tokens=1000,
    timeout=30,
    email="user@example.com",     # Pour authentification JWT
    password="password"
)
wrapper = LLMWrapper(config=config)
```

## Méthodes publiques

### `chat(messages: List[LLMMessage], verbose: bool = False) -> Union[str, LLMChatResponse]`

Génère une complétion de chat.

**Paramètres:**
- `messages`: Liste de messages de conversation (LLMMessage)
- `verbose`: Si `False`, retourne le contenu du message (str). Si `True`, retourne la réponse complète (LLMChatResponse)

**Retour:**
- `str` si `verbose=False`
- `LLMChatResponse` si `verbose=True`

**Exemple:**
```python
from core.llm_wrapper.llm_types import LLMMessage

messages = [
    LLMMessage(role="system", content="Tu es un assistant utile."),
    LLMMessage(role="user", content="Explique Python en une phrase.")
]

# Retour simple (string)
response = wrapper.chat(messages)
print(response)  # "Python est un langage de programmation..."

# Retour détaillé (objet)
response = wrapper.chat(messages, verbose=True)
print(response.model)        # "Mistral-Small"
print(response.choices[0].message.content)
```

---

### `embedding(input_texts: List[str]) -> LLMEmbeddingResponse`

Génère des embeddings pour une liste de textes.

**Paramètres:**
- `input_texts`: Liste de textes à encoder

**Retour:**
- `LLMEmbeddingResponse` contenant les vecteurs d'embeddings

**Exemple:**
```python
texts = ["Premier texte", "Deuxième texte"]
response = wrapper.embedding(texts)

for emb in response.data:
    print(f"Index {emb.index}: {len(emb.embedding)} dimensions")
    print(f"Vecteur: {emb.embedding[:5]}...")  # Affiche les 5 premiers éléments
```

---

### `list_models() -> LLMModelsResponse`

Liste les modèles disponibles pour chat/completions.

**Paramètres:** Aucun

**Retour:**
- `LLMModelsResponse` avec la liste des modèles

**Exemple:**
```python
response = wrapper.list_models()
for model in response.data:
    print(f"ID: {model.id}, Propriétaire: {model.owned_by}")
```

---

### `list_embedding_models() -> LLMModelsResponse`

Liste les modèles d'embedding disponibles.

**Paramètres:** Aucun

**Retour:**
- `LLMModelsResponse` avec la liste des modèles d'embedding

**Exemple:**
```python
response = wrapper.list_embedding_models()
for model in response.data:
    print(f"Modèle d'embedding: {model.id}")
```

---

### `close() -> None`

Ferme le wrapper et nettoie les ressources (actuellement no-op, les connexions sont gérées automatiquement).

**Paramètres:** Aucun

**Retour:** Aucun

---

## Types de données

### LLMMessage
```python
class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[LLMToolCall]] = None
    tool_call_id: Optional[str] = None
```

### LLMChatResponse
```python
class LLMChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[LLMChatChoice]
    usage: LLMUsage
```

### LLMEmbeddingResponse
```python
class LLMEmbeddingResponse(BaseModel):
    object: str
    data: List[LLMEmbeddingData]  # Liste d'embeddings
    model: str
    usage: Optional[LLMUsage]
```

### LLMModelsResponse
```python
class LLMModelsResponse(BaseModel):
    object: str
    data: List[LLMModel]  # Liste de modèles disponibles
```

---

## Gestion des erreurs

Toutes les méthodes peuvent lever `LLMWrapperError` en cas d'échec:
- Erreur de connexion
- Timeout
- Erreur HTTP (4xx, 5xx)
- Échec d'authentification

**Exemple:**
```python
from core.llm_wrapper.llm_wrapper import LLMWrapperError

try:
    response = wrapper.chat(messages)
except LLMWrapperError as e:
    print(f"Erreur LLM: {e}")
```

---

## Authentification

L'authentification JWT est gérée automatiquement lors du premier appel. Le token est réutilisé pour les appels suivants.

**Variables d'environnement:**
- `LLM_BASE_URL`: URL de base de l'API
- `LLM_MODEL`: Modèle par défaut
- `LLM_TEMPERATURE`: Température par défaut (0.0-2.0)
- `LLM_MAX_TOKENS`: Nombre maximum de tokens
- `LLM_TIMEOUT`: Timeout des requêtes (secondes)
- `API_EMAIL`: Email pour authentification
- `API_PASSWORD`: Mot de passe pour authentification
- `API_SERVICE`: Service API par défaut (api/v1, chat/v1, code/v1)
- `EMBED_SERVICE`: Service d'embedding (embed/v1)

---

## Exemple complet

```python
from core.llm_wrapper.llm_wrapper import LLMWrapper, LLMWrapperConfig
from core.llm_wrapper.llm_types import LLMMessage

# Configuration
config = LLMWrapperConfig(
    base_url="https://192.168.239.20",
    api_service="chat/v1"
)
wrapper = LLMWrapper(config=config)

# Récupérer les modèles disponibles
models = wrapper.list_models()
wrapper.config.model = models.data[0].id

# Chat
messages = [
    LLMMessage(role="system", content="Tu es un assistant Python."),
    LLMMessage(role="user", content="Qu'est-ce que le GIL?")
]
response = wrapper.chat(messages)
print(response)

# Embeddings
wrapper.config.embed_service = "embed/v1"
emb_models = wrapper.list_embedding_models()
wrapper.config.model = emb_models.data[0].id

embeddings = wrapper.embedding(["Texte à encoder"])
print(f"Dimensions: {len(embeddings.data[0].embedding)}")
```
