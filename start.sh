#!/bin/bash

# Start script for maboye.ai project
# Creates venv, installs dependencies, and launches services
# Can be run from anywhere - saves original directory

set -e # Exit on error

# --- Configuration URLs ---
URL_TO_SET_LOCAL="http://127.0.0.1:8000"
URL_TO_SET_ONLINE="https://api.deepseek.com" # Or "https://192.168.239.20" for local Mistral/vLLM
# --------------------------

# --- Argument Parsing ---
START_BACKEND=false
for arg in "$@"; do
  if [ "$arg" == "--backend" ]; then
    START_BACKEND=true
    echo "Backend startup requested."
  fi
done
# ------------------------

# Save original directory
ORIGINAL_DIR="$(pwd)"

# Get script directory and change to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/venv"
BACKEND_DIR="$PROJECT_DIR/backendMock"
ENV_FILE="$BACKEND_DIR/.env"

echo "=========================================="
echo "Starting maboye.ai"
echo "Working directory: $PROJECT_DIR"
echo "=========================================="

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
  echo "Virtual environment created"
else
  echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install agents requirements
if [ -f "$PROJECT_DIR/agents/requirements.txt" ]; then
  echo "Installing agents requirements..."
  pip install -r "$PROJECT_DIR/agents/requirements.txt" --quiet
fi

# --- Conditional Backend Setup & Start ---
if [ "$START_BACKEND" = true ]; then
  URL_TO_SET="$URL_TO_SET_LOCAL"

  # Install backend requirements
  if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo "Installing backend requirements..."
    pip install -r "$BACKEND_DIR/requirements.txt" --quiet
  fi

  echo "=========================================="
  echo "Backend Dependencies installed"
  echo "=========================================="

  # Check if port 8000 is in use and kill existing process
  PORT=8000
  PID_ON_PORT=$(lsof -ti:$PORT 2>/dev/null || true)
  if [ ! -z "$PID_ON_PORT" ]; then
    echo "Port $PORT is in use by PID $PID_ON_PORT"
    echo "Killing existing process..."
    kill -9 $PID_ON_PORT 2>/dev/null || true
    sleep 1
  fi

  # Start backend server in background
  echo "Starting backend server..."
  cd "$BACKEND_DIR"
  nohup python main.py >/dev/null 2>&1 &
  BACKEND_PID=$!
  echo "Backend server started (PID: $BACKEND_PID)"
  echo "Backend logs: $BACKEND_DIR/Logs/"

  # Wait for backend to be ready
  echo "Waiting for backend to start..."
  sleep 3

  # Check if backend is running
  if ! ps -p $BACKEND_PID >/dev/null 2>&1; then
    echo "Error: Backend server failed to start"
    echo "Check logs in $BACKEND_DIR/Logs/ for details"
    exit 1
  fi
else
  URL_TO_SET="$URL_TO_SET_ONLINE"
  echo "Skipping backend startup. Use './start.sh --backend' to start it."
fi
# ------------------------------------------

# --- Update .env file ---
echo "Configuring LLM_BASE_URL..."
# Create .env from .env.example if it doesn't exist
if [ ! -f "$ENV_FILE" ] && [ -f "$ENV_FILE.example" ]; then
    echo "Creating .env from .env.example..."
    cp "$ENV_FILE.example" "$ENV_FILE"
fi

# Delete all existing LLM_BASE_URL lines (commented or not)
if [ ! -z "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    sed -i '/^#\? *LLM_BASE_URL=/d' "$ENV_FILE"
fi

# Add the correct LLM_BASE_URL line to the end of the file
echo "LLM_BASE_URL=$URL_TO_SET" >> "$ENV_FILE"
echo "LLM_BASE_URL set to $URL_TO_SET in $ENV_FILE"
# ---------------------------

# Start main application
echo "=========================================="
echo "Starting main application..."
cd "$PROJECT_DIR"
python main.py

# Cleanup function
cleanup() {
  echo ""
  echo "Stopping services..."

  # Kill backend if still running
  if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID >/dev/null 2>&1; then
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    sleep 1

    # Force kill if still alive
    if ps -p $BACKEND_PID >/dev/null 2>&1; then
      kill -9 $BACKEND_PID 2>/dev/null || true
    F
