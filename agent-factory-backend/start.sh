#!/bin/bash
# Start the Agent Factory Backend

echo "=========================================="
echo "Starting Agent Factory Backend"
echo "=========================================="

cd "/mnt/d/The Agent Factory Architecture/The Agent Factory Architecture/agent-factory-backend"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Copy .env.example to .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Start the server
echo "Starting uvicorn server on port 8000..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
