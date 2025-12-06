"""
OpenAI Mock API - FastAPI Server
Mock implementation of OpenAI API that logs all parameters
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal
import logging
from datetime import datetime
import json
import time
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing logger
# Load from project root .env file
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

# Add parent directory to path for tools import
sys.path.insert(0, str(project_root))
from tools.logger import logger

# Suppress third-party logging noise
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("fastapi").setLevel(logging.WARNING)

# ============================================================================
# Pydantic Models - OpenAI API Compatible
# ============================================================================

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str]]
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class CompletionChoice(BaseModel):
    index: int
    text: str
    finish_reason: str
    logprobs: Optional[Any] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Usage


class CompletionResponse(BaseModel):
    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: List[CompletionChoice]
    usage: Usage


class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[Model]


# ============================================================================
# Mock LLM Class
# ============================================================================

class MockLLM:
    """
    Mock LLM that simulates a language model.
    Logs all received parameters for debugging.
    """

    def __init__(self):
        self.request_count = 0
        logger.info("MOCK_LLM", "MockLLM initialized")

    def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Simulate chat completion
        Logs all parameters and returns mock response
        """
        self.request_count += 1

        # Log detailed parameters
        logger.separator(f"CHAT COMPLETION REQUEST #{self.request_count}")

        params = {
            'model': request.model,
            'temperature': request.temperature,
            'top_p': request.top_p,
            'max_tokens': request.max_tokens,
            'stream': request.stream,
            'n': request.n,
            'presence_penalty': request.presence_penalty,
            'frequency_penalty': request.frequency_penalty,
            'stop': request.stop,
            'user': request.user
        }
        logger.info("CHAT_COMPLETION", "Request parameters", params)

        # Log messages
        messages_log = []
        for i, msg in enumerate(request.messages):
            content_preview = msg.content[:100] + ('...' if len(msg.content) > 100 else '')
            messages_log.append({
                'index': i,
                'role': msg.role,
                'content': content_preview
            })
        logger.info("CHAT_COMPLETION", "Messages", messages_log)
        logger.separator()

        # Generate mock response
        mock_response_text = f"Mock response to: {request.messages[-1].content[:50]}..."

        response = ChatCompletionResponse(
            id=f"chatcmpl-mock-{self.request_count}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(
                        role="assistant",
                        content=mock_response_text
                    ),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=sum(len(m.content.split()) for m in request.messages),
                completion_tokens=len(mock_response_text.split()),
                total_tokens=sum(len(m.content.split()) for m in request.messages) + len(mock_response_text.split())
            )
        )

        logger.info("CHAT_COMPLETION", "Response generated", {'response': mock_response_text})
        return response

    def completion(self, request: CompletionRequest) -> CompletionResponse:
        """
        Simulate simple completion
        Logs all parameters and returns mock response
        """
        self.request_count += 1

        # Log detailed parameters
        logger.separator(f"COMPLETION REQUEST #{self.request_count}")

        params = {
            'model': request.model,
            'temperature': request.temperature,
            'top_p': request.top_p,
            'max_tokens': request.max_tokens,
            'stream': request.stream,
            'n': request.n,
            'presence_penalty': request.presence_penalty,
            'frequency_penalty': request.frequency_penalty,
            'stop': request.stop,
            'user': request.user
        }
        logger.info("COMPLETION", "Request parameters", params)

        # Log prompt(s)
        if isinstance(request.prompt, str):
            prompt_preview = request.prompt[:200] + ('...' if len(request.prompt) > 200 else '')
            logger.info("COMPLETION", "Prompt", {'prompt': prompt_preview})
        else:
            prompts_log = []
            for i, prompt in enumerate(request.prompt[:5]):
                prompt_preview = prompt[:100] + ('...' if len(prompt) > 100 else '')
                prompts_log.append({'index': i, 'prompt': prompt_preview})
            logger.info("COMPLETION", f"Prompts ({len(request.prompt)} total)", prompts_log)
        logger.separator()

        # Generate mock response
        prompt_text = request.prompt if isinstance(request.prompt, str) else request.prompt[0]
        mock_response_text = f"Mock completion for: {prompt_text[:50]}..."

        response = CompletionResponse(
            id=f"cmpl-mock-{self.request_count}",
            created=int(time.time()),
            model=request.model,
            choices=[
                CompletionChoice(
                    index=0,
                    text=mock_response_text,
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=len(prompt_text.split()),
                completion_tokens=len(mock_response_text.split()),
                total_tokens=len(prompt_text.split()) + len(mock_response_text.split())
            )
        )

        logger.info("COMPLETION", "Response generated", {'response': mock_response_text})
        return response

    def list_models(self) -> ModelsResponse:
        """
        Return list of available models (mock)
        """
        logger.info("MODELS", "Models list requested")

        models = [
            Model(
                id="gpt-4",
                created=int(time.time()),
                owned_by="openai-mock"
            ),
            Model(
                id="gpt-3.5-turbo",
                created=int(time.time()),
                owned_by="openai-mock"
            ),
            Model(
                id="text-davinci-003",
                created=int(time.time()),
                owned_by="openai-mock"
            ),
        ]

        return ModelsResponse(data=models)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="OpenAI Mock API",
    description="Mock implementation of OpenAI API for testing",
    version="1.0.0"
)

# Initialize Mock LLM
mock_llm = MockLLM()

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Routes - OpenAI API Compatible
# ============================================================================

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "OpenAI Mock API is running",
        "version": "1.0.0",
        "endpoints": [
            "POST /v1/chat/completions",
            "POST /v1/completions",
            "GET  /v1/models",
        ]
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse, tags=["OpenAI"])
def chat_completions(request: ChatCompletionRequest):
    """
    Create a chat completion (OpenAI compatible)

    Request body matches OpenAI's API:
    {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    """
    try:
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="Streaming is not supported in this mock implementation"
            )

        response = mock_llm.chat_completion(request)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("CHAT_COMPLETION", "Chat completion error", {'error': str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions", response_model=CompletionResponse, tags=["OpenAI"])
def completions(request: CompletionRequest):
    """
    Create a completion (OpenAI compatible)

    Request body matches OpenAI's API:
    {
        "model": "text-davinci-003",
        "prompt": "Say this is a test",
        "temperature": 0.7,
        "max_tokens": 50
    }
    """
    try:
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="Streaming is not supported in this mock implementation"
            )

        response = mock_llm.completion(request)
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("COMPLETION", "Completion error", {'error': str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models", response_model=ModelsResponse, tags=["OpenAI"])
def list_models():
    """
    List available models (OpenAI compatible)

    Returns a list of available models
    """
    try:
        response = mock_llm.list_models()
        return response
    except Exception as e:
        logger.error("MODELS", "List models error", {'error': str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["Health"])
def health():
    """Health check with detailed status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "requests_processed": mock_llm.request_count
    }


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    logger.separator("OpenAI Mock API Starting")
    logger.info("STARTUP", "Server running", {
        'url': 'http://127.0.0.1:8000',
        'docs': 'http://127.0.0.1:8000/docs',
        'redoc': 'http://127.0.0.1:8000/redoc'
    })
    logger.separator()


@app.on_event("shutdown")
async def shutdown_event():
    logger.separator("OpenAI Mock API Shutting Down")
    logger.info("SHUTDOWN", "Server stopped", {
        'total_requests': mock_llm.request_count
    })
    logger.separator()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="warning"
    )
