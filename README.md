# Agent Factory Architecture - Implementation

**Production-ready Digital FTEs (Full-Time Equivalents) powered by agents, specs, skills, MCP, A2A, and cloud-native technologies.**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Implemented Components](#implemented-components)
- [Quick Start](#quick-start)
- [Digital FTEs](#digital-ftes)
- [Infrastructure](#infrastructure)
- [MCP Servers](#mcp-servers)
- [Guardrails](#guardrails)
- [A2A Protocol](#a2a-protocol)
- [Agent Evals](#agent-evals)
- [Deployment](#deployment)
- [Development](#development)
- [Resources](#resources)

---

## Overview

The Agent Factory is a system where **General Agents** (like Claude Code) use **Spec-Driven Development** to manufacture **Custom Agents** (Digital FTEs) — autonomous digital employees that work 24/7 performing specialized business tasks with enterprise-grade reliability.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **General Agent** | The BUILDER — figures out HOW to solve problems (e.g., Claude Code) |
| **Custom Agent (Digital FTE)** | The PRODUCT — performs specific tasks perfectly every time |
| **Agent Spec** | The blueprint — describes what the FTE should do |
| **Agent Skills** | The "how-to" — procedural knowledge in SKILL.md files |
| **MCP** | The "with-what" — connects FTEs to tools and data |
| **A2A Protocol** | The "who to talk to" — enables inter-FTE collaboration |

---

## Architecture

The architecture follows a **hybrid multi-SDK model** with 8 layers:

```
┌─────────────────────────────────────────────────────────────────┐
│  L7: A2A Protocol (Inter-FTE Collaboration)                     │
├─────────────────────────────────────────────────────────────────┤
│  L6: Runtime Skills + MCP (Domain Knowledge + Tools)            │
├─────────────────────────────────────────────────────────────────┤
│  L5: Claude Agent SDK (Agentic Execution Engine)                │
├─────────────────────────────────────────────────────────────────┤
│  L4: OpenAI Agents SDK (Orchestration, Guardrails, Handoffs)    │
├─────────────────────────────────────────────────────────────────┤
│  L3: FastAPI (HTTP Interface, Webhooks, A2A Endpoints)          │
├─────────────────────────────────────────────────────────────────┤
│  L2: Dapr Workflows (Durable Execution, State, Pub/Sub)         │
├─────────────────────────────────────────────────────────────────┤
│  L1: Apache Kafka (Event Backbone, Audit Trail)                 │
├─────────────────────────────────────────────────────────────────┤
│  L0: Agent Sandbox (gVisor) — Secure Execution                  │
└─────────────────────────────────────────────────────────────────┘
```

**Total Infrastructure Licensing Cost: $0** (only pay for LLM API tokens)

---

## Project Structure

```
agent-factory/
├── specs/                           # FTE Specifications (Blueprints)
│   ├── customer-success-fte.md     # Customer Success FTE spec
│   ├── sales-support-fte.md        # Sales Support FTE spec
│   ├── technical-support-fte.md    # Technical Support FTE spec
│   └── invoice-processor-fte.md    # Invoice Processor FTE spec
│
├── agent-factory-backend/           # Backend API (FastAPI)
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration and settings
│   │   ├── guardrails.py           # PII, budget, jailbreak guardrails
│   │   ├── routers/
│   │   │   ├── a2a.py             # A2A protocol endpoints
│   │   │   ├── ftes.py            # FTE registry CRUD
│   │   │   ├── metrics.py         # Metrics aggregation
│   │   │   ├── notifications.py   # Notification system
│   │   │   └── skills.py          # Skills management
│   │   └── services/
│   │       └── fte_registry.py    # FTE registration service
│   └── requirements.txt
│
├── agent-factory-dashboard/         # Web Dashboard (Next.js)
│   ├── app/
│   │   ├── notifications/          # Notifications page
│   │   └── ...                     # Other pages
│   ├── components/
│   │   ├── NotificationPanel.tsx   # Notification dropdown
│   │   └── Header.tsx              # Header with notification bell
│   └── lib/
│       └── api.ts                  # API client for backend
│
├── mcp-servers/                     # MCP Server Implementations
│   ├── slack_mcp.py                # Slack integration
│   ├── postgresql_mcp.py           # Database queries
│   ├── web_search_mcp.py           # Web research & news
│   └── README.md
│
├── infrastructure/                  # Infrastructure Configuration
│   ├── dapr/
│   │   ├── components/
│   │   │   ├── pubsub-kafka.yaml   # Kafka pub/sub component
│   │   │   ├── state-redis.yaml    # Redis state store
│   │   │   └── workflow.yaml       # Dapr workflows
│   │   └── configurations/
│   │       └── config.yaml         # Dapr sidecar config
│   ├── kafka/
│   │   ├── topics.yaml             # Kafka topic definitions
│   │   └── docker-compose.yml      # Local Kafka (dev)
│   ├── kubernetes/
│   │   ├── deployments/
│   │   │   └── digital-ftes.yaml   # FTE deployment manifests
│   │   └── services/
│   │       └── fte-services.yaml   # Service definitions
│   └── docker/
│       └── Dockerfile.fte          # Digital FTE Docker image
│
├── evals/                           # Agent Evals (Golden Dataset)
│   └── customer-success-golden-dataset.md
│
└── .github/workflows/
    └── digital-fte-ci.yml          # CI/CD pipeline
```

---

## Implemented Components

### ✅ Core Infrastructure

| Component | Status | Location |
|-----------|--------|----------|
| **FastAPI Backend** | ✅ Complete | `agent-factory-backend/` |
| - Health/Ready endpoints | ✅ | `/health`, `/ready` |
| - Metrics dashboard | ✅ | `/metrics/dashboard` |
| - SLA breaches | ✅ | `/metrics/sla-breaches` |
| - FTE registry (CRUD) | ✅ | `/api/a2a/ftes` |
| - Notifications API | ✅ | `/api/notifications` |
| - Guardrails | ✅ | `app/guardrails.py` |
| **Next.js Dashboard** | ✅ Complete | `agent-factory-dashboard/` |
| - Notification system | ✅ | `NotificationPanel.tsx` + `/notifications` page |
| - Dark mode | ✅ | Toggle with localStorage persistence |
| - Real-time metrics | ✅ | Auto-refresh every 30s |

### ✅ Protocol Implementation

| Component | Status | Location |
|-----------|--------|----------|
| **A2A Protocol** | ✅ Complete | `agent-factory-backend/app/routers/a2a.py` |
| - Agent Card discovery | ✅ | `GET /.well-known/agent.json` |
| - Task delegation | ✅ | `POST /tasks/send` |
| - Task status tracking | ✅ | `POST /tasks/status` |
| - SSE streaming | ✅ | `GET /tasks/{id}/stream` |
| - FTE registry | ✅ | `GET /a2a/ftes` |
| **MCP Servers** | ✅ Complete | `mcp-servers/` |
| - Slack MCP | ✅ | `slack_mcp.py` |
| - PostgreSQL MCP | ✅ | `postgresql_mcp.py` |
| - Web Search MCP | ✅ | `web_search_mcp.py` |

### ✅ Infrastructure & DevOps

| Component | Status | Location |
|-----------|--------|----------|
| **Dapr Components** | ✅ Complete | `infrastructure/dapr/` |
| - Kafka pub/sub | ✅ | `pubsub-kafka.yaml` |
| - Redis state store | ✅ | `state-redis.yaml` |
| - Workflow component | ✅ | `workflow.yaml` |
| **Kafka Configuration** | ✅ Complete | `infrastructure/kafka/` |
| - Topic definitions | ✅ | `topics.yaml` (8 topics) |
| - Local dev docker-compose | ✅ | `docker-compose.yml` |
| **Kubernetes Manifests** | ✅ Complete | `infrastructure/kubernetes/` |
| - FTE deployments | ✅ | `digital-ftes.yaml` |
| - Service definitions | ✅ | `fte-services.yaml` |
| **CI/CD Pipeline** | ✅ Complete | `.github/workflows/digital-fte-ci.yml` |
| - Unit tests | ✅ | pytest with coverage |
| - Agent Evals | ✅ | Golden dataset validation |
| - Docker build & push | ✅ | GitHub Container Registry |
| - Staging/Production deploy | ✅ | Blue-green deployment |

### ✅ Specifications & Evals

| Component | Status | Location |
|-----------|--------|----------|
| **FTE Specifications** | ✅ Complete | `specs/` |
| - Customer Success FTE | ✅ | `customer-success-fte.md` |
| - Sales Support FTE | ✅ | `sales-support-fte.md` |
| - Technical Support FTE | ✅ | `technical-support-fte.md` |
| **Agent Evals** | ✅ Complete | `evals/` |
| - Customer Success Golden Dataset | ✅ | `customer-success-golden-dataset.md` |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker Desktop (for local infrastructure)

### 1. Start Local Infrastructure

```bash
cd infrastructure/kafka
docker-compose up -d
```

This starts:
- Kafka (port 9092)
- Redis (port 6379)
- Kafka UI (port 8080)
- Dapr Placement (port 50005)
- Zipkin (port 9411)

### 2. Start Backend

```bash
cd agent-factory-backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

Backend available at:
- **API**: http://localhost:8003
- **Docs**: http://localhost:8003/docs
- **Health**: http://localhost:8003/health

### 3. Start Dashboard

```bash
cd agent-factory-dashboard
npm install
npm run dev
```

Dashboard available at: http://localhost:3000

---

## Digital FTEs

### Customer Success FTE

**Role**: Senior Customer Success Specialist
**Availability**: 24/7 (168 hours/week)
**Cost**: $500-2,000/month (vs $4,000-8,000 human)

**Capabilities**:
- Ticket triage and response
- SLA monitoring and breach prevention
- Sentiment analysis and escalation
- Multi-channel support (email, chat, Slack)

**Spec**: [`specs/customer-success-fte.md`](specs/customer-success-fte.md)

### Sales Support FTE

**Role**: Senior Sales Development Representative
**Availability**: 24/7
**Cost**: $500-2,000/month

**Capabilities**:
- Lead qualification (BANT framework)
- ROI calculation and proposal generation
- Objection handling
- CRM integration

**Spec**: [`specs/sales-support-fte.md`](specs/sales-support-fte.md)

### Technical Support FTE

**Role**: Senior Technical Support Engineer (Tier 2/3)
**Availability**: 24/7
**Cost**: $500-2,000/month

**Capabilities**:
- Systematic debugging and log analysis
- API troubleshooting and infrastructure diagnostics
- Database query and data validation
- Engineering escalation with detailed reproduction steps

**Spec**: [`specs/technical-support-fte.md`](specs/technical-support-fte.md)

---

## Infrastructure

### Dapr Components

Dapr provides the unified infrastructure layer:

- **Pub/Sub**: Kafka integration for event-driven communication
- **State Store**: Redis for persistent workflow state
- **Workflows**: Durable execution that survives crashes
- **Secrets**: Secure credential management

### Kafka Topics

| Topic | Purpose | Retention |
|-------|---------|-----------|
| `fte.triggers.inbound` | New task requests | 7 days |
| `fte.sandbox.lifecycle` | Sandbox events | 30 days |
| `fte.status.updates` | Progress events | 30 days |
| `fte.results.completed` | Task results | 90 days |
| `fte.audit.actions` | Immutable audit log | 7 years |

---

## MCP Servers

MCP (Model Context Protocol) servers connect Digital FTEs to external systems.

### Slack MCP

**Tools**:
- `send_message`: Send messages to channels/threads
- `get_channel_messages`: Retrieve recent messages
- `post_alert`: Post formatted alerts with severity
- `get_user_info`: Get user details
- `list_channels`: List available channels

**Setup**:
```bash
export SLACK_BOT_TOKEN=xoxb-your-token
python mcp-servers/slack_mcp.py
```

### PostgreSQL MCP

**Tools**:
- `execute_query`: Run read-only SQL queries
- `get_schema`: Inspect database schema
- `get_table_stats`: Get row counts and sizes
- `run_explain`: Analyze query execution plans
- `validate_data`: Check data integrity

**Security**: Read-only access, max 1000 rows per query

**Setup**:
```bash
export DATABASE_URL=postgresql://user:pass@localhost/dbname
python mcp-servers/postgresql_mcp.py
```

### Web Search MCP

**Tools**:
- `web_search`: General web search
- `search_news`: Recent news articles
- `fetch_url_content`: Extract content from URLs
- `search_wikipedia`: Wikipedia summaries

**Setup**:
```bash
export SEARCH_API_KEY=your-api-key
export SEARCH_ENGINE_ID=your-engine-id
python mcp-servers/web_search_mcp.py
```

---

## Guardrails

Guardrails ensure Digital FTEs operate safely and reliably.

### Implemented Guardrails

| Guardrail | Purpose | Implementation |
|-----------|---------|----------------|
| **PII Detection** | Detect and mask sensitive data | Regex-based pattern matching for email, SSN, credit cards, phone, API keys |
| **Budget Enforcement** | Prevent excessive token usage | Token tracking with configurable limits |
| **Jailbreak Detection** | Block prompt injection attempts | Pattern matching for common jailbreak techniques |
| **Output Validation** | Ensure responses match schema | Pydantic model validation |
| **Compliance Checks** | Flag regulated data | HIPAA, GDPR, PCI-DSS, SOX pattern detection |

### Usage Example

```python
from app.guardrails import GuardrailPipeline, TokenBudget

pipeline = GuardrailPipeline()
result = await pipeline.run(
    input_text=user_input,
    budget=TokenBudget(max_tokens=10000),
)

if not result["passed"]:
    raise ValueError(f"Guardrail failed: {result['critical_failures']}")
```

---

## A2A Protocol

A2A (Agent-to-Agent) protocol enables inter-FTE discovery and collaboration.

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/.well-known/agent.json` | GET | Agent Card for discovery |
| `/a2a/ftes` | GET | List known FTEs |
| `/a2a/tasks/send` | POST | Delegate task to FTE |
| `/a2a/tasks/status` | POST | Check task status |
| `/a2a/tasks/{id}/stream` | GET | SSE stream of task updates |

### Example: Delegate Task

```python
import httpx

async def delegate_task():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/a2a/tasks/send",
            json={
                "jsonrpc": "2.0",
                "id": "request-123",
                "method": "tasks/send",
                "params": {
                    "message": "Analyze customer sentiment for last week",
                    "skill": "sentiment-analysis",
                    "from": "sales-support-fte",
                }
            }
        )
        return response.json()
```

---

## Agent Evals

Agent Evals test Digital FTEs against a **Golden Dataset** of 50+ real-world scenarios before deployment.

### Running Evals

```bash
python evals/run_evals.py --fte customer-success --min-accuracy 0.85
```

### Scoring Rubric

| Score | Meaning | Action |
|-------|---------|--------|
| 0.95+ | Excellent | Deploy with confidence |
| 0.85-0.94 | Good | Review failures, minor fixes |
| 0.75-0.84 | Acceptable | Significant improvements needed |
| < 0.75 | Poor | Do not deploy, retrain required |

---

## Deployment

### Local Development

```bash
# Start infrastructure
cd infrastructure/kafka
docker-compose up -d

# Start backend
cd agent-factory-backend
uvicorn app.main:app --reload

# Start dashboard
cd agent-factory-dashboard
npm run dev
```

### Production (Kubernetes)

```bash
# Apply infrastructure
kubectl apply -f infrastructure/dapr/
kubectl apply -f infrastructure/kafka/topics.yaml

# Deploy FTEs
kubectl apply -f infrastructure/kubernetes/deployments/
kubectl apply -f infrastructure/kubernetes/services/

# Monitor rollout
kubectl rollout status deployment/customer-success-fte --namespace=agent-factory
```

---

## Development

### Adding a New FTE

1. **Write Spec**: Create `specs/<name>-fte.md` following the 6-section blueprint
2. **Create Skills**: Add runtime skills to `skills/<skill-name>/SKILL.md`
3. **Configure MCP**: Add required MCP server integrations
4. **Add Evals**: Create golden dataset in `evals/<name>-golden-dataset.md`
5. **Deploy**: Add Kubernetes manifest to `infrastructure/kubernetes/deployments/`

### Adding a New MCP Server

1. Create `<name>_mcp.py` in `mcp-servers/`
2. Define tools using `@mcp.tool()` decorator
3. Document with clear Args and Returns
4. Update `mcp-servers/README.md`

---

## Resources

- **Architecture Document**: [The Agent Factory Architecture_ Building Digital FTEs v1.md](The%20Agent%20Factory%20Architecture_%20Building%20Digital%20FTEs%20v1.md)
- **Agent Skills**: https://agentskills.io
- **MCP Protocol**: https://modelcontextprotocol.io
- **A2A Protocol**: https://github.com/a2aproject/A2A
- **Dapr**: https://docs.dapr.io
- **OpenAI Agents SDK**: https://openai.github.io/openai-agents-python/
- **Claude Agent SDK**: https://docs.anthropic.com/en/docs/agents-and-tools/claude-agent-sdk

---

## License

Zero-Cost Open-Source Licensing. All infrastructure components are built on open standards with no licensing fees. Only pay-per-token for LLM API calls.

---

**Built with ❤️ for the Panaversity Agent Factory Development Curriculum**
