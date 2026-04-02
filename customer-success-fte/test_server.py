#!/usr/bin/env python3
"""
Minimal test server - no external dependencies required
"""
import sys
sys.path.insert(0, '/mnt/d/The Agent Factory Architecture/The Agent Factory Architecture/customer-success-fte')

from fastapi import FastAPI
from app.skills import initialize_skills, get_registry

app = FastAPI(title="Agent Factory - Test Server")

@app.on_event("startup")
async def startup():
    initialize_skills()
    print("✓ Skills initialized")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-factory"}

@app.get("/api/skills")
async def list_skills():
    registry = get_registry()
    return {"skills": registry.list_skills(), "total": len(registry.skills)}

@app.get("/api/a2a/health")
async def a2a_health():
    return {"status": "healthy", "protocol": "A2A v1.0"}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("AGENT FACTORY TEST SERVER")
    print("=" * 60)
    print("Starting on http://127.0.0.1:8000")
    print("Endpoints:")
    print("  - Health: http://127.0.0.1:8000/health")
    print("  - Skills: http://127.0.0.1:8000/api/skills")
    print("  - A2A:    http://127.0.0.1:8000/api/a2a/health")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
