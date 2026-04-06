# System Architecture

## Overview
The Month-End Close Orchestrator is built using a modern, scalable technical stack to ensure reliable execution of complex multi-agent reasoning tasks, robust storage, and real-time frontend updates.

## Architecture Diagram

```mermaid
graph TD
    %% Frontend
    subgraph Frontend [Next.js Frontend]
        UI[React UI Components]
        Dashboard[Dashboard & Visualizations]
        WSClient[Socket.IO Client]
        RC[React Query]
    end

    %% Backend Services
    subgraph Backend [FastAPI Backend Server]
        API[REST API Endpoints]
        WSServer[Socket.IO Server]
        Auth[Auth/Context]
        Scheduler[Autonomous Task Scheduler]
        
        %% Agents
        subgraph MultiAgentSystem [Agent Framework]
            Orchestrator((Orchestrator Agent))
            Specialized[9 Specialized Agents]
            Memory[Shared Memory Manager]
            LLMConnector[LLM API Integration]
            
            Orchestrator --> Specialized
            Specialized <--> Memory
            Specialized <--> LLMConnector
        end
    end

    %% Async Task Queue
    subgraph Async [Background Infrastructure]
        CeleryWorker[Celery Worker Group]
        RedisQueue[(Redis Message Broker)]
    end

    %% Data Storage
    subgraph DatabaseLayer [Persistence]
        PG[(PostgreSQL Database)]
        PG_Company(Companies)
        PG_TB(Trial Balances)
        PG_Budget(Budgets)
    end

    %% External Connections
    LLM[Anthropic Claude API]
    Email[Resend Email API]

    %% Interactions
    UI <-->|HTTP/REST| API
    WSClient <-->|WebSockets| WSServer
    
    API <--> MultiAgentSystem
    WSServer <--> MultiAgentSystem
    Scheduler --> MultiAgentSystem
    
    MultiAgentSystem <--> RedisQueue
    RedisQueue <--> CeleryWorker
    
    MultiAgentSystem <--> PG
    CeleryWorker <--> PG
    
    LLMConnector <-->|API Calls| LLM
    MultiAgentSystem -->|Alerts| Email
```

## Component Details
1. **Frontend**: Next.js 14 App Router, styled with Tailwind CSS and shadcn/ui. Uses Recharts for financial aggregations and Socket.IO for real-time agent tracking.
2. **Backend Engine**: FastAPI handles synchronous REST requests and concurrent async agent orchestration.
3. **Database Layer**: PostgreSQL stores financial datasets, entity hierarchies, budgets, and agent interaction logs.
4. **LLM Engine**: LangChain constructs chains that are powered by Anthropic's Claude to resolve complex accounting compliance checks and discrepancies.
