# Testing Guide — Customer Success Digital FTE

## Overview

| Layer | Tool | Requires |
|-------|------|----------|
| Unit tests | pytest | Nothing — all deps mocked |
| Integration tests | pytest + httpx | Nothing — DB/Kafka/OpenAI mocked |
| Load tests | Locust | Running app (`docker compose up`) |
| Golden dataset evals | Custom runner | Running app + real `OPENAI_API_KEY` |

---

## Setup

```bash
# From the customer-success-fte/ directory
pip install -r requirements.txt -r requirements-test.txt
```

---

## Unit Tests

Test the repository layer, agent tools, and guardrails in complete isolation.

```bash
# Run all unit tests
pytest tests/unit/

# Run a specific file
pytest tests/unit/test_guardrails.py -v

# Run a specific test class
pytest tests/unit/test_repositories.py::TestTicketRepository -v

# Run a specific test
pytest tests/unit/test_tools.py::TestCreateTicket::test_creates_ticket_and_returns_id -v
```

**What's covered:**
- `test_repositories.py` — BaseRepository CRUD, CustomerRepository, TicketRepository, ConversationRepository, KnowledgeBaseRepository, MessageRepository, AgentMetricRepository, CustomerIdentifierRepository
- `test_tools.py` — All 6 agent tools: `create_ticket`, `search_knowledge_base`, `get_customer_history`, `escalate_to_human`, `send_response`, `resolve_ticket`
- `test_guardrails.py` — PII detection/masking, escalation keyword matching, sentiment scoring, all three InputGuardrail functions

---

## Integration Tests

Test the full HTTP layer and Kafka processing pipeline with mocked external services.

```bash
# Run all integration tests
pytest tests/integration/

# Run only API tests
pytest tests/integration/test_api.py -v

# Run only worker tests
pytest tests/integration/test_worker.py -v

# Run only agent flow tests
pytest tests/integration/test_agent.py -v
```

**What's covered:**
- `test_api.py` — All endpoints: `/health`, `/ready`, `POST /web/support`, `GET/POST /whatsapp`, `GET/POST /gmail`, `GET /metrics`, `GET /metrics/dashboard`
- `test_worker.py` — Kafka message processing, retry logic, DLQ routing, survey detection, response handler delivery
- `test_agent.py` — End-to-end agent runs, guardrail triggering (PII, keyword, sentiment), tool invocations, error handling, multi-turn conversations

---

## Run All Tests with Coverage

```bash
pytest tests/unit/ tests/integration/ \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-fail-under=80
```

Coverage report is written to `htmlcov/index.html`.

---

## Load Tests

Requires the application stack running. Start it with Docker Compose:

```bash
cp .env.example .env
# Fill in OPENAI_API_KEY, SECRET_KEY, INTERNAL_API_KEY in .env
docker compose up --build -d
```

### Interactive mode (browser UI at http://localhost:8089)

```bash
locust -f tests/load/locustfile.py --host http://localhost:8000
```

Then open `http://localhost:8089`, set **100 users**, **10 spawn rate**, and click Start.

### Headless mode (CI)

```bash
locust -f tests/load/locustfile.py \
  --host http://localhost:8000 \
  --headless \
  -u 100 \
  -r 10 \
  --run-time 5m \
  --html tests/load/report.html \
  --csv tests/load/results
```

Results are saved to:
- `tests/load/report.html` — visual report
- `tests/load/results_stats.csv` — per-endpoint stats
- `tests/load/results_failures.csv` — failure log

**Target SLOs:**

| Metric | Target |
|--------|--------|
| p50 response time | < 500ms |
| p95 response time | < 3000ms |
| Error rate | < 1% |
| Throughput | ≥ 50 req/s at 100 users |

---

## Golden Dataset Evaluations

Evaluates agent quality against 25 labelled scenarios in `tests/evals/golden_dataset.yaml`.

### CI mode (mock agent — no real API calls)

```bash
# Uses mock responses when OPENAI_API_KEY=sk-test-key
OPENAI_API_KEY=sk-test-key \
python tests/evals/run_evals.py --min-pass-rate 0.80
```

### Full evaluation (real OpenAI API)

```bash
# Requires a running PostgreSQL (or docker compose up postgres)
OPENAI_API_KEY=sk-...  \
DATABASE_URL=postgresql+asyncpg://postgres:changeme@localhost:5432/customer_success \
python tests/evals/run_evals.py --output tests/evals/results.json
```

### Filter by category

```bash
# Run only escalation scenarios
python tests/evals/run_evals.py --tag escalation

# Run only billing scenarios
python tests/evals/run_evals.py --tag billing

# Run a single scenario
python tests/evals/run_evals.py --id EVAL-013
```

**Available tags:** `shipping` | `billing` | `account` | `technical` | `escalation` | `general`

**Pass/fail criteria per scenario:**
- `should_escalate` — agent escalated (or did not) as expected
- `should_create_ticket` — ticket was created (or not) as expected
- `response_contains` — all required phrases appear in the reply
- `response_must_not_contain` — forbidden phrases are absent

---

## Pytest Markers

```bash
# Run only marked tests
pytest -m unit
pytest -m integration

# Exclude slow tests during development
pytest -m "not integration"
```

---

## CI Pipeline (example)

```yaml
# .github/workflows/test.yml (reference)
- name: Unit tests
  run: pytest tests/unit/ --cov=app --cov-fail-under=80

- name: Integration tests
  run: pytest tests/integration/

- name: Eval smoke test
  run: |
    OPENAI_API_KEY=sk-test-key \
    python tests/evals/run_evals.py --min-pass-rate 0.80
```

---

## Test File Structure

```
tests/
├── conftest.py                  # Shared fixtures (mock_session, client, agent_context, …)
├── unit/
│   ├── test_repositories.py     # Repository CRUD & domain queries
│   ├── test_tools.py            # Agent @function_tool functions
│   └── test_guardrails.py       # PII, keyword, sentiment guardrails
├── integration/
│   ├── test_api.py              # FastAPI endpoints (all routes)
│   ├── test_worker.py           # Kafka worker pipeline
│   └── test_agent.py           # End-to-end agent conversation flow
├── load/
│   └── locustfile.py            # Locust load test (100 users, 3-channel mix)
└── evals/
    ├── golden_dataset.yaml      # 25 labelled test scenarios
    └── run_evals.py             # Evaluation runner with reporting
```
