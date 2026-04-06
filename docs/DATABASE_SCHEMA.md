# Database Schema Documentation

Our backend leverages **PostgreSQL** configured via SQLAlchemy ORM.

## High-Level Entity Relationship Diagram

```mermaid
erDiagram
    COMPANY ||--o{ TRIAL_BALANCE_LINE : has
    COMPANY ||--o{ BUDGET : has
    COMPANY ||--o{ BANK_STATEMENT : has
    COMPANY ||--o{ ACCRUAL_SCHEDULE : has
    COMPANY ||--o{ INTERCOMPANY_TRANSACTION : "participates (buy/sell)"
    COMPANY ||--o{ NOTIFICATION : triggers

    COMPANY {
        string id PK
        string name
        string industry
        float revenue_annual
        string close_status
    }

    TRIAL_BALANCE_LINE {
        int account_code PK
        string company_id FK
        string period PK
        string account_name
        float debit
        float credit
        float balance
    }

    BUDGET {
        int id PK
        string company_id FK
        int year
        int month
        int account_code
        float budget_amount
    }

    INTERCOMPANY_TRANSACTION {
        string transaction_id PK
        string selling_entity_id FK
        string buying_entity_id FK
        float amount
    }
```

## Core Models
- **Company**: Stores entity metadata, overall operational flags, and standard PE reporting characteristics.
- **TrialBalanceLine**: Holds the canonical records for financial accounts on a per-period basis.
- **Budget**: Master storage for annualized forecasts partitioned by code and month.
- **IntercompanyTransaction**: Log of all activities executing across the boundary of Apex Capital Partners nested entities.
