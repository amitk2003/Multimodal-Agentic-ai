# API Documentation

The Month-End Close Orchestrator provides a standard REST API documented dynamically via extending OpenAPI/Swagger.
You can view the interactive exploration UI directly by navigating to `http://localhost:8000/docs` while the backend is online.

## Key Concept Endpoints

### Entities & Ledgers
* `GET /api/companies` - Lists all 8 sub-entities with progress flags
* `GET /api/companies/{id}` - Details specific portfolio entity parameters
* `GET /api/companies/{id}/financials` - Responds with Income Statement & Balance Sheet arrays for a requested period

### Orchestrator Controls
* `POST /api/agents/run-all?period=2026-01` - Triggers the overarching master orchestration thread. Spawns tasks across Celest queues and broadcast via WS.
* `POST /api/seed` - Dev endpoint to drop existing DB frames and seed freshly parsed data from the `/data` dir.

### Logging & Exports
* `GET /api/agents/logs` - Provides historic execution traces.
* `GET /api/reports` - Aggregates generated artifact references.
* `GET /api/notifications` - Lists anomalies caught by continuous polling engines.
