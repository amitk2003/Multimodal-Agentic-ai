# Redis and Celery Architecture Analysis

**Month-End Close Orchestrator System**

---

## Executive Summary

After a comprehensive codebase analysis, here are the key findings:

| Component | Status | Actual Usage |
|-----------|--------|--------------|
| **Redis** | ✅ **ACTIVE** | Inter-agent shared memory & event publishing |
| **Celery** | ❌ **UNUSED** | Configured in dependencies but no implementation |

**The Bottom Line**: Redis is actively used for agent communication. Celery is included as a dependency but not actually used—the system uses asyncio-based scheduling instead.

---

## Part 1: REDIS - What's Actually Being Used

### 1.1 Redis Architecture in the System

```
┌─────────────────────────────────────────────────────────┐
│                  Multiple Agents Running                │
│  (Trial Balance, Variance, Accrual, Revenue, etc.)      │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ Shared Memory Layer
                 ▼
┌─────────────────────────────────────────────────────────┐
│            Redis-Backed SharedMemory Class             │
│  • Store (set) results after execution                 │
│  • Retrieve (get) prior agent results                  │
│  • Publish (pub/sub) events                            │
│  • Automatic TTL-based expiration (1 hour)            │
└────────────┬─────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│         Redis Instance (6379 default)                   │
│  • DB 0: General cache (REDIS_URL)                      │
│  • DB 1: Celery queue (REDIS_CELERY_URL) - UNUSED       │
└─────────────────────────────────────────────────────────┘
```

### 1.2 The SharedMemory Implementation

Location: [backend/app/agents/base.py](backend/app/agents/base.py#L73)

```python
class SharedMemory:
    """Redis-backed shared memory for inter-agent communication."""

    def __init__(self):
        self._memory: Dict[str, Any] = {}
        self._redis = None
        try:
            import redis
            self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self._redis.ping()
            logger.info("Shared memory connected to Redis")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory fallback: {e}")

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Store a value in shared memory with TTL."""
        serialized = json.dumps(value, default=str)
        if self._redis:
            self._redis.setex(key, ttl, serialized)  # Set with expiration
        else:
            self._memory[key] = serialized  # Fallback to dict

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from shared memory."""
        if self._redis:
            val = self._redis.get(key)
        else:
            val = self._memory.get(key)
        
        if val:
            return json.loads(val)
        return None

    def publish(self, channel: str, message: Dict):
        """Publish an event to a Redis pub/sub channel."""
        serialized = json.dumps(message, default=str)
        if self._redis:
            self._redis.publish(channel, serialized)
        logger.debug(f"Published to {channel}: {message.get('type', 'unknown')}")

    def delete(self, key: str):
        if self._redis:
            self._redis.delete(key)
        else:
            self._memory.pop(key, None)


# Singleton shared memory instance
shared_memory = SharedMemory()
```

### 1.3 How Redis is Used: Inter-Agent Communication Pattern

**The month-end close workflow is structured in 4 sequential groups:**

```
Group 1 (Parallel)           Group 2 (Sequential)      Group 3        Group 4
┌──────────────────────┐     ┌──────────────────┐    ┌────────────┐  ┌─────────┐
│ Trial Balance        │     │ Accrual Verif.   │    │ Interco    │  │ Consol. │
│ Variance Analysis    ├────>│ Revenue Rec.     ├───>│ Elimination├─>│ Report  │
│ Cash Flow Recon.     │     │ Expense Categ.   │    │            │  │         │
└──────────────────────┘     └──────────────────┘    └────────────┘  └─────────┘
         ▼                             ▼                    ▼               ▼
  Writes to Redis         Reads from Redis         Reads prev.      Reads all
  (Results)              (Group 1 data)            results
```

**Example Data Flow:**

#### Step 1: Variance Analysis Agent Stores Result

[backend/app/agents/variance.py](backend/app/agents/variance.py) executes and writes to Redis:

```python
# After variance analysis completes
memory_key = f"agent:variance_analysis:{company_id}:{period}"
# e.g., "agent:variance_analysis:retailco:2026-01"
self.memory.set(memory_key, result)

# Result stored in Redis (1 hour TTL):
{
    "status": "completed",
    "findings": [
        {
            "account": "4100 - Product Revenue",
            "variance": 125000,
            "variance_pct": 15.2,
            "threshold": 10.0,
            "severity": "warning"
        }
    ],
    "actions": ["Flag for manual review", "Escalate to finance"],
    "timestamp": "2026-01-31T09:45:32"
}
```

#### Step 2: Consolidation Agent Retrieves Result

[backend/app/agents/consolidation.py](backend/app/agents/consolidation.py#L91):

```python
async def execute(self, company_id: Optional[str] = None, period: str = "2026-01", **kwargs):
    # ... consolidation logic ...
    
    # Retrieve IC elimination data from prior agent
    ic_result = self.memory.get(f"agent:intercompany_elimination:all:{period}")
    
    if ic_result and isinstance(ic_result, dict):
        elimination_amount = ic_result.get("summary", {}).get("total_volume", 0)
        actions.append(f"Applied IC eliminations of ${elimination_amount:,.0f}")
```

#### Step 3: Reporting Agent Gathers All Data

[backend/app/agents/reporting.py](backend/app/agents/reporting.py#L48-L54):

```python
async def _generate_full_report(self, period: str) -> Dict[str, Any]:
    """Generate comprehensive monthly report package."""
    
    # Gather data from all agent results via shared memory
    consolidation_data = self.memory.get(f"agent:consolidation:all:{period}")
    
    variance_data = {}
    for company in companies:
        vd = self.memory.get(f"agent:variance_analysis:{company.id}:{period}")
        if vd:
            variance_data[company.id] = vd
```

### 1.4 Redis Storage Pattern

Every agent follows this naming convention:

```
agent:{agent_type}:{company_id_or_all}:{period}
```

Examples:
- `agent:trial_balance_validator:techforge_saas:2026-01`
- `agent:variance_analysis:retailco:2026-01`
- `agent:accrual_verification:precisionmfg_inc:2026-01`
- `agent:intercompany_elimination:all:2026-01` (cross-company, no specific ID)
- `agent:consolidation:all:2026-01` (portfolio-level)
- `agent:reporting_communication:all:2026-01` (final report)

### 1.5 Redis Configuration

**From [config.py](backend/app/config.py#L21-L24):**

```python
# Redis
REDIS_URL: str = "redis://default:qHuQAzs1RDbLRhPAvfggL0yUtgo2lYrD@redis-18198.c244.us-east-1-2.ec2.cloud.redislabs.com:18198/0"
REDIS_CELERY_URL: str = "redis://default:qHuQAzs1RDbLRhPAvfggL0yUtgo2lYrD@redis-18198.c244.us-east-1-2.ec2.cloud.redislabs.com:18198/1"
```

**From [docker-compose.yml](docker-compose.yml#L20-L26):**

```yaml
# Redis Cache & Message Broker
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 5s
    retries: 5
```

**From [requirements.txt](backend/requirements.txt#L11-L12):**

```
redis==5.2.1
```

---

## Part 2: CELERY - What's Configured But NOT Used

### 2.1 Celery in Dependencies (Not in Code)

**What exists:**

```
requirements.txt:
  celery[redis]==5.4.0

docker-compose.yml:
  (No Celery worker service defined)

config.py:
  REDIS_CELERY_URL = "redis://.../:1"  # DB index 1 reserved for Celery

.env.example:
  REDIS_CELERY_URL configured
```

**What's missing (proof of non-implementation):**

| Expected File/Code | Status | Notes |
|------------------|--------|-------|
| `celery.py` (app init) | ❌ Missing | No Celery app instance created |
| `@task` decorators | ❌ Zero found | No Celery tasks defined |
| `@app.task` decorators | ❌ Zero found | No shared task definitions |
| Celery imports | ❌ None found | `from celery import` - NOT in any file |
| Worker processes | ❌ None | No `celery worker` commands or configs |
| Beat scheduler | ❌ None | No Celery Beat for periodic tasks |
| Task routing | ❌ Not configured | No task routing rules |

### 2.2 Grep Results Confirming Non-Usage

Search for any Celery task definitions:

```bash
grep -r "@celery\|@task\|from celery\|import celery" backend/app/ --include="*.py"
```

Result: **No matches** (Only Redis import found)

---

## Part 3: Why the Architecture Differs from Documentation

### 3.1 Documented Architecture (ARCHITECTURE.md)

What the documentation describes:

```mermaid
graph TD
    API["FastAPI Backend"]
    Agents["Multi-Agent System"]
    CeleryWorker["Celery Worker Group"]
    RedisQueue["Redis Message Broker"]
    PG["PostgreSQL"]
    
    API --> Agents
    Agents --> RedisQueue
    RedisQueue --> CeleryWorker
    CeleryWorker --> PG
```

From [ARCHITECTURE.md](docs/ARCHITECTURE.md#L40-L65):

```
subgraph Async [Background Infrastructure]
    CeleryWorker[Celery Worker Group]
    RedisQueue[(Redis Message Broker)]
end

MultiAgentSystem <--> RedisQueue
RedisQueue <--> CeleryWorker
CeleryWorker <--> PG
```

### 3.2 Actual Architecture (Implemented)

What's actually happening:

```mermaid
graph TD
    Scheduler["Autonomous Scheduler<br/>(asyncio)"]
    WorkflowEngine["Workflow Engine<br/>(DB polling)"]
    Agents["Multi-Agent System"]
    Redis["Redis<br/>(Shared Memory Only)"]
    PG["PostgreSQL<br/>(Task Queue)"]
    
    Scheduler --> WorkflowEngine
    WorkflowEngine --> Agents
    Agents --> Redis
    Agents --> PG
    WorkflowEngine --> PG
```

### 3.3 Why the Difference?

**Documented Design Rationale:**
- Scalable distributed task execution
- Celery for async job processing
- Redis as message broker
- Separate worker processes

**Actual Implementation Rationale:**
- Simpler, single-instance deployment
- Easier local development and debugging
- No distributed complexity needed (yet)
- Database-driven task queue sufficient
- Redis repurposed for agent state sharing

---

## Part 4: The ACTUAL Async & Scheduling System

### 4.1 Autonomous Scheduler (asyncio-based)

Location: [backend/app/main.py](backend/app/main.py#L140-L167)

```python
async def autonomous_scheduler():
    """Background task that runs autonomous agent operations on schedule."""
    logger.info("Autonomous scheduler initialized")
    last_daily_run = None
    last_monitor_run = None

    while True:
        try:
            now = datetime.utcnow()

            # Daily close check (9 AM)
            if (last_daily_run is None or
                (now - last_daily_run).total_seconds() > 86400):
                if now.hour == settings.DAILY_CLOSE_HOUR:
                    logger.info("Running scheduled daily check...")
                    from app.services.scheduler import run_daily_check
                    await run_daily_check()
                    last_daily_run = now

            # Monitoring every 5 minutes
            if (last_monitor_run is None or
                (now - last_monitor_run).total_seconds() > settings.MONITORING_INTERVAL_MINUTES * 60):
                from app.services.scheduler import run_monitoring
                await run_monitoring()
                last_monitor_run = now

            # Process any pending workflow tasks
            from app.services.scheduler import process_workflow_tasks
            await process_workflow_tasks()

            await asyncio.sleep(30)  # Check every 30 seconds

        except asyncio.CancelledError:
            logger.info("Scheduler cancelled")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)
```

**Trigger Points:**
- Daily at 9 AM: Full health check
- Every 5 minutes: Monitoring/reconciliation
- Every 30 seconds: Poll for pending workflow tasks
- On-demand: WebSocket trigger from UI

### 4.2 Workflow Engine (Database-Driven Task Queue)

Location: [backend/app/services/workflow_engine.py](backend/app/services/workflow_engine.py)

**Execution Groups (Sequential with internal parallelism):**

```python
CLOSE_WORKFLOW_GROUPS = [
    ExecutionGroup(
        name="Validation & Analysis",
        agent_types=["trial_balance_validator", "variance_analysis", "cash_flow_reconciliation"],
        parallel=True,
        per_company=True,
    ),
    ExecutionGroup(
        name="Verification",
        agent_types=["accrual_verification", "revenue_recognition", "expense_categorization"],
        parallel=False,
        per_company=True,
    ),
    ExecutionGroup(
        name="Cross-Company",
        agent_types=["intercompany_elimination"],
        parallel=False,
        per_company=False,
    ),
    ExecutionGroup(
        name="Consolidation & Reporting",
        agent_types=["consolidation", "reporting_communication"],
        parallel=False,
        per_company=False,
    ),
]
```

**Task Processing Flow:**

```python
async def process_workflow_tasks():
    """Pick up and execute pending agent tasks from the database."""
    
    # Find all workflows currently running
    active_workflows = db.query(WorkflowRun).filter_by(status="running").all()
    
    for workflow in active_workflows:
        # Get next batch of tasks at same priority level
        next_tasks = engine.get_next_tasks(workflow.id)
        
        for task in next_tasks:
            # Mark as running
            task.status = "running"
            task.started_at = datetime.utcnow()
            db.commit()
            
            try:
                # Execute the agent
                result = await run_single_agent(
                    agent_type=task.agent_type,
                    company_id=task.company_id,
                    period=workflow.period,
                    db=db
                )
                
                # Mark task as completed
                engine.complete_task(task.id, result=result)
            except Exception as e:
                # Mark task as failed
                engine.complete_task(task.id, error=str(e))
```

### 4.3 Data Models for Task Management

From [backend/app/models/agent.py](backend/app/models/agent.py):

- **WorkflowRun**: Tracks overall close operation
  - status: pending/running/completed/failed/paused
  - total_steps: number of tasks
  - completed_steps: progress tracking
  - progress: percentage (0-100)

- **AgentTask**: Individual agent execution task
  - workflow_run_id: parent workflow
  - agent_type: which agent to run
  - company_id: for which company (or null for cross-company)
  - status: pending/running/completed/failed/skipped
  - priority: execution order (group-based)
  - result: stored output
  - error_message: if failed

---

## Part 5: Complete Task Execution Example

### 5.1 User Triggers Full Close

```bash
POST /api/agents/run-all?period=2026-01
```

### 5.2 Execution Sequence

**Step 1: Create Workflow & Tasks**

```python
# WorkflowEngine creates:
- WorkflowRun(status="running", total_steps=40, period="2026-01")
- 40 AgentTasks with priorities (by group):
  - Priority 1: Trial Balance Validator x8 companies
  - Priority 1: Variance Analysis x8 companies
  - Priority 1: Cash Flow Reconciliation x8 companies
  - Priority 2: Accrual Verification x8 companies
  - Priority 2: Revenue Recognition x8 companies
  - ...and so on
```

**Step 2: Autonomous Scheduler Detects Pending Tasks**

```python
# Every 30 seconds, process_workflow_tasks() finds:
next_tasks = [
    AgentTask(agent_type="trial_balance_validator", company_id="techforge_saas", priority=1),
    AgentTask(agent_type="variance_analysis", company_id="techforge_saas", priority=1),
    AgentTask(agent_type="cash_flow_reconciliation", company_id="techforge_saas", priority=1),
    ...
]
```

**Step 3: Execute Agents Sequentially**

```python
# For each task:
result = await TrialBalanceValidatorAgent(db).run(
    company_id="techforge_saas",
    period="2026-01"
)

# Agent stores result in Redis:
shared_memory.set(
    "agent:trial_balance_validator:techforge_saas:2026-01",
    result
)
```

**Step 4: Mark Task Complete & Update Progress**

```python
engine.complete_task(task.id, result=result)

# Updates:
- task.status = "completed"
- task.completed_at = now()
- task.result = result
- workflow.completed_steps += 1
- workflow.progress = (40/40 * 100) = 100%
```

**Step 5: Next Group Executes Using Prior Results**

```python
# Accrual Verification reads from Redis:
variance_data = self.memory.get(
    f"agent:variance_analysis:techforge_saas:2026-01"
)
# Uses this to inform accrual analysis
```

---

## Part 6: Why This Design?

### 6.1 Requirements Met by Current Architecture

| Requirement | How Solved | Technology |
|-------------|-----------|------------|
| **Async Execution** | Background tasks | asyncio + asyncContextManager |
| **Task Scheduling** | Recurring checks | datetime + while loop |
| **Inter-Agent Communication** | Share results | Redis shared memory |
| **Task Persistence** | Workflow tracking | PostgreSQL |
| **Dependency Management** | Priority-based groups | WorkflowEngine grouping |
| **Real-Time Updates** | Event broadcasting | WebSocket + Redis pub/sub |
| **Fallback Resilience** | In-memory fallback | SharedMemory dual-mode |
| **Scalability** | Ready for Celery upgrade | Clean separation |

### 6.2 Why NOT Celery? (For Now)

**Advantages of Current Approach:**
- ✅ No external service dependencies beyond Redis & PostgreSQL
- ✅ Simpler debugging and development
- ✅ Easier local testing (no worker setup)
- ✅ Single codebase, no distributed state issues
- ✅ Clear task history in database

**Where Celery Would Help (Future):**
- 🔄 True horizontal scaling (multiple servers)
- 🔄 Task prioritization queues
- 🔄 Dead-letter queues for failures
- 🔄 Built-in retry mechanisms
- 🔄 Isolated worker processes

---

## Part 7: All Redis References in Code

### Redis Imports
- [backend/app/main.py:19](backend/app/main.py#L19): `import redis`
- [backend/app/agents/base.py:21](backend/app/agents/base.py#L21): `import redis`
- [backend/app/agents/base.py:74](backend/app/agents/base.py#L74): `import redis` (in try/except)

### Redis Usage Locations

1. **SharedMemory Initialization** → [base.py:67-77](backend/app/agents/base.py#L67-L77)
2. **Store Agent Results** → [base.py:198](backend/app/agents/base.py#L198)
3. **Publish Events** → [base.py:226](backend/app/agents/base.py#L226)
4. **Broadcast WebSocket** → [base.py:320](backend/app/agents/base.py#L320)
5. **Consolidation Read IC Data** → [consolidation.py:91](backend/app/agents/consolidation.py#L91)
6. **Reporting Gather Results** → [reporting.py:48-54](backend/app/agents/reporting.py#L48-L54)
7. **API Get Variances** → [companies.py:131](backend/app/api/companies.py#L131)

---

## Part 8: Configuration Summary

### Environment Variables

```bash
# Redis Connection
REDIS_URL=redis://default:PASSWORD@HOST:18198/0
REDIS_CELERY_URL=redis://default:PASSWORD@HOST:18198/1

# Scheduler Settings
DAILY_CLOSE_HOUR=9
DAILY_CLOSE_MINUTE=0
MONITORING_INTERVAL_MINUTES=5

# Agent Settings
MAX_AGENT_RETRIES=3
AGENT_RETRY_DELAY=5
```

### Docker Compose Services

```yaml
redis:
  image: redis:7-alpine
  ports: [6379:6379]
  
postgres:
  image: postgres:16-alpine
  ports: [5432:5432]
```

### Health Checks

```bash
# Redis health
docker exec redis redis-cli ping
# Returns: PONG

# Database health
docker exec postgres pg_isready -U postgres
# Returns: accepting connections
```

---

## Part 9: Recommendations

### To Keep Current Architecture "As Is"
- ✅ Works well for single-instance deployments
- ✅ Sufficient for 8 portfolio companies
- ✅ Clear data lineage in database
- ✅ Easy to debug locally

### For Future Celery Migration
1. Define Celery app configuration
2. Decorate agents with `@shared_task`
3. Create Celery worker configuration
4. Add task retry/error handling
5. Implement task routing
6. Monitor via Flower dashboard

### Redis Best Practices (Current)
- ✅ Already using TTL (1 hour) for auto-cleanup
- ✅ Good: JSON serialization
- ✅ Good: Fallback to in-memory
- ✅ Consider: Redis persistence (AOF/RDB) for production
- ✅ Consider: Redis Cluster for high availability

---

## Summary Table

| Aspect | Status | Location |
|--------|--------|----------|
| Redis Configuration | ✅ Configured | config.py, docker-compose.yml |
| Redis Usage | ✅ Active | agents/base.py SharedMemory |
| Redis Fallback | ✅ Implemented | In-memory dict if unavailable |
| Celery Configuration | ✅ In requirements | celery[redis]==5.4.0 |
| Celery Implementation | ❌ None | No code found |
| Async Scheduling | ✅ Active | main.py autonomous_scheduler |
| Task Queue | ✅ Active | DB-driven, workflow_engine.py |
| Task Persistence | ✅ All tasks in DB | models/agent.py |
| Inter-Agent Communication | ✅ Redis shared memory | base.py SharedMemory |

---

## Files Analyzed

- ✅ [backend/app/config.py](backend/app/config.py)
- ✅ [backend/app/main.py](backend/app/main.py)
- ✅ [backend/app/agents/base.py](backend/app/agents/base.py)
- ✅ [backend/app/agents/consolidation.py](backend/app/agents/consolidation.py)
- ✅ [backend/app/agents/reporting.py](backend/app/agents/reporting.py)
- ✅ [backend/app/api/companies.py](backend/app/api/companies.py)
- ✅ [backend/app/services/scheduler.py](backend/app/services/scheduler.py)
- ✅ [backend/app/services/workflow_engine.py](backend/app/services/workflow_engine.py)
- ✅ [docker-compose.yml](docker-compose.yml)
- ✅ [backend/requirements.txt](backend/requirements.txt)
- ✅ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- ✅ [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md)
- ✅ [README.md](README.md)

---

**Analysis Date**: 2026-01-31  
**Analyzed By**: AI Code Assistant  
**Total Files Reviewed**: 13  
**Code Matches Found**: 8 Redis usage locations, 0 Celery implementations
