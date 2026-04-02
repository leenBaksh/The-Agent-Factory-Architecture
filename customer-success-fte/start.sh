#!/bin/bash
# Start the Customer Success FTE Backend

echo "=========================================="
echo "Starting Customer Success FTE Backend"
echo "=========================================="

cd "/mnt/d/The Agent Factory Architecture/The Agent Factory Architecture/customer-success-fte"

# Activate virtual environment
source .venv/bin/activate

# Start the server
echo "Starting uvicorn server on port 8000..."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
