"""
Backend Mock API.

Mock implementation of LLM API for testing and development.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent

load_dotenv(backend_dir / ".env")

sys.path.insert(0, str(project_root))
from core.logger import logger

from backendMock.utils import get_env_variable
from backendMock.routes import tests
from backendMock.routes import auth
from backendMock.routes import chat
from backendMock.routes import tests_iterative
from backendMock.routes import completion
from backendMock.routes import models
from backendMock.routes import embedding
from backendMock.routes import ollama
from backendMock.routes import health


app = FastAPI(
    title="Backend Mock API",
    description="Mock LLM API for testing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(tests.router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(tests_iterative.router)
app.include_router(completion.router)
app.include_router(models.router)
app.include_router(embedding.router)
app.include_router(ollama.router)
app.include_router(health.router)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Backend Mock API running",
        "version": "1.0.0",
        "endpoints": {
            "health": [
                "GET  /health",
                "GET  /"
            ],
            "openai_compatible": [
                "POST /v1/chat/completions",
                "GET  /v1/models"
            ],
            "local_api_global": [
                "GET  /api/v1/models",
                "POST /api/v1/chat/completions",
                "POST /api/v1/completions"
            ],
            "local_api_chat": [
                "GET  /chat/v1/models",
                "POST /chat/v1/chat/completions",
                "POST /chat/v1/completions"
            ],
            "local_api_code": [
                "GET  /code/v1/models",
                "POST /code/v1/chat/completions",
                "POST /code/v1/completions"
            ],
            "ollama": [
                "GET  /ollama/api/tags",
                "POST /ollama/api/generate",
                "POST /ollama/api/embed"
            ],
            "embedding": [
                "GET  /embed/v1/models",
                "POST /embed/v1/embeddings"
            ],
            "tests": [
                "POST /tests"
            ],
            "iterative": [
                "POST /tests/iterative"
            ]
        }
    }


@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    host = get_env_variable("BACKEND_MOCK_HOST", "127.0.0.1")
    port = get_env_variable("BACKEND_MOCK_PORT", "8000")
    logger.info("BACKEND_MOCK", "Server started", {"url": f"http://{host}:{port}"})


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    logger.info("BACKEND_MOCK", "Server stopped", {
        # "total_requests": backend_mock_instance.request_count # Cannot access request_count
    })


if __name__ == "__main__":
    import uvicorn

    host = get_env_variable("BACKEND_MOCK_HOST", "127.0.0.1")
    port = int(get_env_variable("BACKEND_MOCK_PORT", "8000"))
    log_level = get_env_variable("BACKEND_MOCK_LOG_LEVEL", "warning")

    uvicorn.run(app, host=host, port=port, log_level=log_level)