#!/bin/bash

# Start script for maboye.ai project
# Creates venv, installs dependencies, and launches services
# Can be run from anywhere - saves original directory

set -e  # Exit on error

# Save original directory
ORIGINAL_DIR="$(pwd)"

# Get script directory and change to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PROJECT_DIR="$SCRIPT_DIR"
VENV_DIR="$PROJECT_DIR/venv"
BACKEND_DIR="$PROJECT_DIR/backendMock"

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

# Install backend requirements
if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    echo "Installing backend requirements..."
    pip install -r "$BACKEND_DIR/requirements.txt" --quiet
fi

# Install agents requirements
if [ -f "$PROJECT_DIR/agents/requirements.txt" ]; then
    echo "Installing agents requirements..."
    pip install -r "$PROJECT_DIR/agents/requirements.txt" --quiet
fi

# Check if .env exists in backendMock
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "Warning: .env not found in backendMock"
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    fi
fi

echo "=========================================="
echo "Dependencies installed"
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
nohup python main.py > /dev/null 2>&1 &
BACKEND_PID=$!
echo "Backend server started (PID: $BACKEND_PID)"
echo "Backend logs: $BACKEND_DIR/Logs/"

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 3

# Check if backend is running
if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "Error: Backend server failed to start"
    echo "Check logs in $BACKEND_DIR/Logs/ for details"
    exit 1
fi

# Start main application
echo "Starting main application..."
cd "$PROJECT_DIR"
python main.py

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping services..."

    # Kill backend if still running
    if [ ! -z "$BACKEND_PID" ] && ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        sleep 1

        # Force kill if still alive
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi
    fi

    # Return to original directory
    cd "$ORIGINAL_DIR"
    echo "Returned to: $(pwd)"
}

# Register cleanup on exit
trap cleanup EXIT INT TERM
