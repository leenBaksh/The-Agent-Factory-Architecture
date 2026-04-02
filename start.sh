#!/bin/bash
# Quick Start Script for Agent Factory Architecture

set -e

echo "=========================================="
echo "Agent Factory Architecture - Quick Start"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from correct directory
if [ ! -f "customer-success-fte/app/main.py" ]; then
    echo "Error: Please run this script from the root directory"
    exit 1
fi

echo -e "${YELLOW}Step 1: Setting up Python Backend${NC}"
cd customer-success-fte

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo -e "${GREEN}✓ Python backend ready${NC}"

cd ..

echo ""
echo -e "${YELLOW}Step 2: Setting up Dashboard${NC}"
cd agent-factory-dashboard

# Install npm dependencies
if [ ! -d "node_modules" ] || [ ! -f "node_modules/.package-lock.json" ]; then
    echo "Installing npm dependencies (this may take a few minutes)..."
    npm install
fi

echo -e "${GREEN}✓ Dashboard ready${NC}"

cd ..

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "To start the applications:"
echo ""
echo "1. Backend (Customer Success FTE):"
echo "   cd customer-success-fte"
echo "   source .venv/bin/activate"
echo "   python -m uvicorn app.main:app --reload"
echo "   # Access: http://localhost:8000"
echo "   # API Docs: http://localhost:8000/docs"
echo ""
echo "2. Dashboard:"
echo "   cd agent-factory-dashboard"
echo "   npm run dev"
echo "   # Access: http://localhost:3000"
echo ""
echo "3. Or use Docker Compose:"
echo "   cd customer-success-fte"
echo "   docker compose up --build"
echo ""
echo "=========================================="
