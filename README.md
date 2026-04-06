# Month-End Close Orchestrator

> Autonomous AI-powered month-end close orchestration platform for Apex Capital Partners - a PE firm managing 8 portfolio companies.

![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-violet)
![Stack](https://img.shields.io/badge/Stack-LangChain%20%2B%20Langflow%20%2B%20PaperclipAI-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%20%2B%20TypeScript-green)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-orange)

## Quick Start (< 15 minutes)

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local dev)
- Python 3.12+ (for local dev)

### Option 1: Docker (Recommended)

```bash
# Clone and navigate
git clone <repo-url>
cd month-end-close

# Copy environment file
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start all services
docker compose up -d

# Access the application
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# Langflow:  http://localhost:7860
# API Docs:  http://localhost:8000/docs
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Start PostgreSQL and Redis (Docker or local)
docker compose up postgres redis -d
# Run backend
uvicorn app.main:socket_app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Seed the Database
```bash
# Via API endpoint
curl -X POST http://localhost:8000/api/seed

# Or via the Dashboard "Seed Data" button
```

### Run the Close Workflow
```bash
# Via API
curl -X POST "http://localhost:8000/api/agents/run-all?period=2026-01"

# Or via the Dashboard "Run Full Close" button
```

## Documentation & Diagrams

We have prepared comprehensive documentation for the platform architecture, agent behavior, data models, and API interfaces:

- [System Architecture (Mermaid Diagrams)](./docs/ARCHITECTURE.md)
- [Multi-Agent Execution Workflows](./docs/AGENT_WORKFLOW.md)
- [Database Schema Models](./docs/DATABASE_SCHEMA.md)
- [API Reference Details](./docs/API_DOCS.md)

## High-Level Architecture

```
                  ┌──────────────────────────────────┐
                  │      Next.js Frontend (3000)      │
                  │  React + TypeScript + Tailwind     │
                  │  Recharts + Socket.IO Client       │
                  └──────────┬───────────────┬────────┘
                        REST │          WS   │
                  ┌──────────┴───────────────┴────────┐
                  │      FastAPI Backend (8000)         │
                  │  API + WebSocket + Scheduler        │
                  └──────┬──────┬──────┬──────┬───────┘
                         │      │      │      │
               ┌─────────┘  ┌───┘   ┌──┘   ┌──┘
               ▼            ▼       ▼      ▼
          ┌─────────┐  ┌────────┐ ┌──────┐ ┌──────────┐
          │PostgreSQL│  │ Redis  │ │Celery│ │ Langflow │
          │  (5432)  │  │ (6379) │ │Worker│ │  (7860)  │
          └─────────┘  └────────┘ └──────┘ └──────────┘
```

## 10 AI Agents

| # | Agent | Function |
|---|-------|----------|
| 1 | **Orchestrator** | Master controller, workflow coordination |
| 2 | **Trial Balance Validator** | Debit=Credit checks, unusual balances |
| 3 | **Variance Analysis** | Budget vs actual, AI commentary |
| 4 | **Accrual Verification** | Missing/stale accruals, amortization |
| 5 | **Intercompany Elimination** | IC matching, elimination journal entries |
| 6 | **Revenue Recognition** | ASC 606 compliance, timing validation |
| 7 | **Expense Categorization** | Misclassification detection, COGS/OpEx |
| 8 | **Cash Flow Reconciliation** | GL-to-bank reconciliation, liquidity |
| 9 | **Consolidation** | Multi-entity aggregation, GAAP rules |
| 10 | **Reporting & Communication** | Executive reports, automated emails |

## Autonomous Operation

- **Scheduled**: Daily close check at 9 AM, hourly monitoring during close week
- **Event-driven**: Data changes trigger agent workflows automatically
- **Proactive**: Agents detect issues and send email alerts without prompting
- **Self-healing**: Retry logic with exponential backoff, dead letter queue

## Technology Stack

- **AI**: LangChain + Langflow + PaperclipAI + Claude API
- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Celery
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, Recharts
- **Database**: PostgreSQL 16, Redis 7
- **Email**: Resend API + Jinja2 templates
- **Infrastructure**: Docker Compose

## Portfolio Companies

| Company | Revenue | Industry |
|---------|---------|----------|
| TechForge SaaS | $45M | SaaS |
| PrecisionMfg Inc | $120M | Manufacturing |
| RetailCo | $200M | Retail |
| HealthServices Plus | $35M | Healthcare |
| LogisticsPro | $80M | Transportation |
| IndustrialSupply Co | $150M | Distribution |
| DataAnalytics Corp | $25M | Professional Services |
| EcoPackaging Ltd | $60M | Manufacturing |

## API Documentation

Interactive API docs available at `http://localhost:8000/docs` when running.

## Video Demo

[Link to demo video - YouTube/Loom]

## Known Limitations & Future Improvements

1. **LLM Costs**: Agents use Claude API calls; consider caching for repeated analyses
2. **Langflow Flows**: Visual flow definitions should be expanded for complex workflows
3. **Tests**: Unit test coverage should be expanded for financial calculation edge cases
4. **PDF Export**: Currently CSV only; PDF generation with ReportLab planned
5. **Authentication**: Single-user mode; would need RBAC for production PE fund use
