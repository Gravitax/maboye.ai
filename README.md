# maboye.ai

AI agent system with LLM backend integration.

---

## Quick Start

```bash
./start.sh
```

The script can be run from anywhere - it automatically handles directory changes.

---

## What It Does

The start script will:
1. Create Python virtual environment (if needed)
2. Upgrade pip
3. Install all dependencies
4. Start the mock LLM backend server
5. Launch the main application
6. Return to your original directory on exit

---

## Project Structure

```
maboye.ai/
├── start.sh              # Start script
├── main.py               # Main application
├── LLM/                  # LLM wrapper
│   ├── llm.py
│   └── README.md
├── agents/               # Agent system
│   ├── agent.py
│   ├── config.py
│   ├── types.py
│   ├── example_agent.py
│   └── README.md
├── backend/              # Mock LLM API
│   ├── main.py
│   ├── .env
│   └── README.md
├── tools/                # Shared utilities
│   └── logger.py
└── documentations/       # Documentation
    └── ARCHITECTURE.md
```

---

## Components

### LLM Wrapper
OpenAI-compatible API client with retry logic and error handling.

**Location:** `LLM/`
**Documentation:** `LLM/README.md`

### Agent System
Base agent class for building LLM-powered workflows.

**Location:** `agents/`
**Documentation:** `agents/README.md`

### Mock Backend
FastAPI server simulating OpenAI API for testing.

**Location:** `backend/`
**Documentation:** `backend/README.md`

### Logger
Unified logging system with file rotation and configuration.

**Location:** `tools/logger.py`

---

## Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install -r agents/requirements.txt

# Start backend (in separate terminal)
cd backend
python main.py

# Run main application
python main.py
```

---

## Configuration

Backend configuration in `backend/.env`:
- Server settings (host, port)
- Logging configuration
- CORS settings

See `backend/.env.example` for all options.

---

## Development

### Running Examples

```bash
# Activate venv
source venv/bin/activate

# Run agent examples
python agents/example_agent.py
```

### Creating Custom Agents

```python
from LLM import LLM, LLMConfig
from agents import Agent, AgentConfig

# Setup
llm = LLM(LLMConfig(base_url="http://127.0.0.1:8000"))
agent = Agent(llm, AgentConfig(name="CustomAgent"))

# Use
output = agent.run("Your prompt here")
print(output.response)
```

---

## API Endpoints

Backend exposes OpenAI-compatible endpoints:

- `POST /v1/chat/completions` - Chat completion
- `POST /v1/completions` - Text completion
- `GET /v1/models` - List models
- `GET /health` - Health check

See `backend/README.md` for detailed API documentation.

---

## Documentation

- **Architecture:** `documentations/ARCHITECTURE.md`
- **LLM Wrapper:** `LLM/README.md`
- **Agent System:** `agents/README.md`
- **API Routes:** `backend/README.md`

---

## Requirements

- Python 3.8+
- pip
- bash (for start.sh)

---

## Features

- Clean architecture with separation of concerns
- Professional code with best practices
- Comprehensive error handling
- Configurable logging system
- Type hints and validation
- Extensible agent framework
- Mock LLM backend for testing

---

## License

Proprietary
