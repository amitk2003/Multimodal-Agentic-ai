# Month-End Close Orchestrator

> Autonomous AI-powered month-end close orchestration platform for **Apex Capital Partners** — a Private Equity firm managing 8 portfolio companies with aggregate revenue of $615M+.

![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-violet)
![Stack](https://img.shields.io/badge/Stack-LangChain%20%2B%20Langflow%20%2B%20Redis-blue)
![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014%20%2B%20TypeScript-green)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python%203.12-orange)
![PDF Report](https://img.shields.io/badge/PDF%20Report-ReportLab%20Engine-red)
![Deployment](https://img.shields.io/badge/Deployment-Docker%20%2B%20Render-blueviolet)

---

## 📌 Table of Contents

- [Overview](#overview)
- [Quick Start (< 15 Minutes)](#quick-start--15-minutes)
- [System Architecture](#system-architecture)
- [10 Specialized AI Agents](#10-specialized-ai-agents)
- [PDF Executive Report Generation](#pdf-executive-report-generation)
- [Redis & Communication Architecture](#redis--communication-architecture)
- [Deployment (Render & Docker)](#deployment-render--docker)
- [Portfolio Companies](#portfolio-companies)
- [Documentation & Deep Dives](#documentation--deep-dives)
- [Technology Stack](#technology-stack)
- [Project Roadmap & Status](#project-roadmap--status)

---

## 🌟 Overview

The **Month-End Close Orchestrator** automates complex financial close operations across multiple portfolio companies. Built on a modular **Multi-Agent Architecture**, it replaces manual spreadsheet reconciliations with autonomous detection of debit/credit imbalances, ASC 606 revenue timing errors, stale accruals, intercompany match mismatches, and budget variances.

### Key Capabilities
- 🤖 **10 Autonomous Agents**: Fully domain-specialized agents executing trial balance, accruals, intercompany, revenue recognition, cash flow, and consolidation tasks.
- ⚡ **Real-Time WebSockets**: Live progress streaming, execution logs, and anomaly events pushed directly to the Next.js dashboard via Socket.IO.
- 🧠 **Redis Shared Memory**: Persistent cross-agent context, event pub/sub, and automatic execution result caching.
- 📄 **Executive PDF Generation**: Built-in ReportLab engine generating publication-ready architecture & audit reports.
- 📊 **Executive Dashboard**: Interactive Next.js 14 UI with real-time financial metrics, anomaly counters, and workflow triggers.

---

## 🚀 Quick Start (< 15 minutes)

### Prerequisites
- **Docker & Docker Compose** (Recommended)
- **Node.js 20+** (For local frontend development)
- **Python 3.12+** (For local backend development)

---

### Option 1: Docker (Recommended)

```bash
# Clone the repository and enter directory
git clone <repo-url>
cd Agentix_apex

# Copy environment template
cp .env.example .env
# Edit .env and configure your ANTHROPIC_API_KEY / DATABASE_URL

# Launch all microservices
docker compose up -d

# Service Endpoints:
# 🖥️  Frontend:  http://localhost:3000
# ⚙️  Backend:   http://localhost:8000
# ⚡  Langflow:  http://localhost:7860
# 📖  API Docs:  http://localhost:8000/docs
```

---

### Option 2: Local Development

#### Backend Setup
```bash
cd backend

# Create & activate virtual environment (optional)
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis and PostgreSQL via Docker
docker compose up postgres redis -d

# Option A: Local Development (Uvicorn with auto-reload)
uvicorn app.main:socket_app --reload --port 8000

# Option B: Production Server (Gunicorn with multi-worker UvicornWorker)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:socket_app --bind 0.0.0.0:8000
```

#### Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js Development Server
npm run dev
```

---

### Seeding Data & Triggering Workflow

```bash
# 1. Seed sample portfolio financial data via API
curl -X POST http://localhost:8000/api/seed

# 2. Trigger full month-end close workflow across all agents
curl -X POST "http://localhost:8000/api/agents/run-all?period=2026-01"

# Alternatively, use the interactive buttons on the Next.js Dashboard at http://localhost:3000
```

---

## 📐 System Architecture

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
                ┌────────┘  ┌───┘   ┌──┘   ┌──┘
                ▼            ▼       ▼      ▼
           ┌─────────┐  ┌────────┐ ┌──────┐ ┌──────────┐
           │PostgreSQL│  │ Redis  │ │Report│ │ Langflow │
           │  (5432)  │  │ (6379) │ │ Lab  │ │  (7860)  │
           └─────────┘  └────────┘ └──────┘ └──────────┘
```

---

## 🤖 10 Specialized AI Agents

| # | Agent Name | Core Responsibilities & Rules |
|---|------------|-------------------------------|
| 1 | **Orchestrator** | Master execution pipeline manager, dependency tracking, multi-agent dispatching |
| 2 | **Trial Balance Validator** | Enforces Debit = Credit balance equations, flags unmapped accounts and balance anomalies |
| 3 | **Variance Analysis** | Analyzes Budget vs. Actual vs. Prior Period variations with AI commentary |
| 4 | **Accrual Verification** | Identifies missing recurring accruals, stale balances, and prepaid amortization schedules |
| 5 | **Intercompany Elimination** | Matches bilateral IC transactions across portfolio entities & generates elimination entries |
| 6 | **Revenue Recognition** | Validates ASC 606 revenue timing compliance, unearned revenue, and contract milestones |
| 7 | **Expense Categorization** | Detects misclassified expenses between COGS and OpEx, flags policy threshold breaches |
| 8 | **Cash Flow Reconciliation** | Reconciles GL balances to bank statements, validates liquidity positions & unrecorded items |
| 9 | **Consolidation** | Aggregates multi-entity trial balances, applies foreign translation & elimination rules |
| 10 | **Reporting & Communication** | Generates executive financial summaries, exports PDF/CSV, sends email notifications |

---

## 📄 PDF Executive Report Generation

The platform includes a dedicated **ReportLab-powered PDF Engine** (`generate_report.py`) that renders two-pass, vector-styled architecture briefs and financial analysis reports.

```bash
# Generate the executive architecture report PDF
python generate_report.py
```

### PDF Engine Features
- **Dynamic Two-Pass Canvas**: Automatically computes total page count and renders standard running headers/footers with `NumberedCanvas`.
- **Publication-Grade Styling**: Built with custom color palettes (`#1e293b` Dark Slate, `#4f46e5` Indigo accent, `#059669` Emerald).
- **Structured Sections**: Includes executive summaries, system architecture diagrams, agent breakdowns, and security compliance matrix.
- **Output File**: Saves directly as [`Month_End_Close_Architecture_Analysis.pdf`](./Month_End_Close_Architecture_Analysis.pdf).

---

## 🔄 Redis & Communication Architecture

The platform leverages **Redis** as a dynamic shared memory layer and event bus:
- **Shared Context Storage**: Agents publish execution outputs into Redis with TTL key management, allowing downstream agents (e.g. Consolidation) to read results from upstream agents (e.g. Intercompany, Trial Balance).
- **Event Bus (Pub/Sub)**: Dispatches real-time state changes (`agent:started`, `agent:completed`, `anomaly:detected`) directly to FastAPI WebSocket handlers.
- **Detailed Evaluation**: See [`REDIS_CELERY_ANALYSIS.md`](./REDIS_CELERY_ANALYSIS.md) for an in-depth architectural breakdown of Redis state management vs. task queue evaluation.

---

## ☁️ Deployment (Render & Docker)

### Render Cloud Deployment
The repository includes a ready-to-use Render Blueprint configuration (`render.yaml`).

1. Connect your repository to **Render.com**.
2. Render automatically detects `render.yaml` and provisions the FastAPI Web Service.
3. Configure the following environment variables in the Render Dashboard:
   - `DATABASE_URL` (PostgreSQL instance connection string)
   - `REDIS_URL` (Redis instance connection string)
   - `ANTHROPIC_API_KEY` (Anthropic API Key for LLM execution)

---

## 🏢 Portfolio Companies

The platform currently manages financial close operations across **8 Apex Capital Partners portfolio companies**:

| Company | Aggregate Revenue | Primary Industry |
|---------|-------------------|------------------|
| **TechForge SaaS** | $45M | B2B SaaS |
| **PrecisionMfg Inc** | $120M | High-Tech Manufacturing |
| **RetailCo** | $200M | Omnichannel Retail |
| **HealthServices Plus** | $35M | Healthcare Provider |
| **LogisticsPro** | $80M | Freight & Logistics |
| **IndustrialSupply Co** | $150M | B2B Distribution |
| **DataAnalytics Corp** | $25M | AI & Data Services |
| **EcoPackaging Ltd** | $60M | Sustainable Packaging |
| **TOTAL PE PORTFOLIO** | **$615M** | **8 Active Operating Companies** |

---

## 📑 Documentation & Deep Dives

Detailed architectural documentation is available in the [`docs/`](./docs) directory and workspace analysis files:

- 🏗️ **[System Architecture Diagram](./docs/ARCHITECTURE.md)**: Visual sequence diagrams, component topologies, and data flow models.
- 🔄 **[Agent Execution Workflow](./docs/AGENT_WORKFLOW.md)**: Multi-agent execution cycles, state transitions, and retry logic.
- 🗄️ **[Database Schema Reference](./docs/DATABASE_SCHEMA.md)**: Relational schema models for Companies, Accounts, Journal Entries, Run Logs, and Anomalies.
- 🔌 **[API Specification Details](./docs/API_DOCS.md)**: Complete endpoint descriptions for REST endpoints and Socket.IO channels.
- 📊 **[Redis & Celery Analysis](./REDIS_CELERY_ANALYSIS.md)**: Architectural decision record evaluating Redis shared memory & event publishing.
- 📄 **[Technical Architecture PDF Brief](./generate_report.py)**: Python script for generating the publication-ready PDF report.

---

## 🛠️ Technology Stack

- **AI & Agent Infrastructure**: LangChain, Langflow, Custom Redis Shared Memory, Anthropic Claude API
- **Backend Core**: Python 3.12, FastAPI, SQLAlchemy (PostgreSQL / SQLite), Socket.IO Async Server, ReportLab
- **Frontend Dashboard**: Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Lucide Icons, Recharts
- **Database & Cache**: PostgreSQL 16, Redis 7 (Pub/Sub & Shared Memory)
- **Infrastructure & Deployment**: Docker, Docker Compose, Render Blueprint (`render.yaml`)

---

## ✅ Project Status & Resolved Roadmap

- [x] **10 Autonomous AI Agents**: Implemented with modular base handlers and domain validation rules.
- [x] **Real-Time Event Streaming**: WebSockets via Socket.IO streaming live agent execution to frontend.
- [x] **Executive PDF Report Generator**: Built-in ReportLab engine (`generate_report.py`) with custom dynamic canvas.
- [x] **Redis State & Pub/Sub Engine**: High-performance cross-agent memory with automatic TTL expiry.
- [x] **Cloud Deployment Spec**: Native `render.yaml` blueprint for one-click Render cloud hosting.
- [ ] **Multi-Tenant Role-Based Access Control (RBAC)**: Planned for enterprise PE multi-user permissions.
- [ ] **Direct ERP Integrations**: NetSuite & SAP ERP connector modules in active development.
