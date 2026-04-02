# Agent Factory Backend

Central backend API for the Agent Factory Dashboard.

## Quick Start

```bash
# Start the backend
./start.sh
```

## Architecture

The backend aggregates metrics and data from all Digital FTE instances:

- **Customer Success FTE** - Handles customer support tickets
- **Future FTEs** - Billing, Technical Support, Sales, etc.

## API Endpoints

### Metrics

- `GET /metrics/dashboard` - Aggregated dashboard metrics
- `GET /metrics/sla-breaches` - SLA breach information

### FTE Management

- `GET /api/a2a/ftes` - List all FTE instances
- `POST /api/a2a/ftes` - Create new FTE
- `GET /api/a2a/ftes/{id}` - Get specific FTE
- `DELETE /api/a2a/ftes/{id}` - Delete FTE

### Skills

- `GET /api/skills` - List all skills
- `GET /api/skills/{id}` - Get specific skill

### Health

- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## Development

```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000
```
