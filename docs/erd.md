# MedDocs — Data Model (ERD)

> **Status: FIRST DRAFT (ENG-12, in progress).** Captures the core entities decided in the design
> session. Secondary tables and index review still to do — see "Open / next" at the bottom.
> This is the **target** schema for the multi-tenant platform. The current `backend/app/models.py`
> is the OLD single-user schema (User, Document, ChatSession, ChatMessage) — do not reuse it; M2 implements this.

## The one rule: multi-tenancy at the schema level

Every table that holds a tenant's data carries an **`organization_id`** column. That column is what
guarantees org A can never read org B's rows. **The single exception is `users`** — a user is a
**global identity** (one login), tied to organizations through `memberships`, so it has no `organization_id`.

## Core ERD

```mermaid
erDiagram
    organizations ||--o{ memberships   : "has members"
    users         ||--o{ memberships   : "belongs via"
    organizations ||--o{ patients      : "owns"
    organizations ||--o{ documents     : "owns"
    patients      ||--o{ documents     : "is subject of"
    users         ||--o{ documents     : "assigned to"
    documents     ||--o{ document_events: "has history"
    users         ||--o{ document_events: "actor"
    organizations ||--o{ audit_log     : "scoped to"
    users         ||--o{ audit_log     : "actor"

    organizations {
        int id PK
        string name
        timestamp created_at
    }
    users {
        int id PK
        string email UK
        string hashed_password
        string full_name
        timestamp created_at
    }
    memberships {
        int id PK
        int user_id FK
        int organization_id FK
        string role "org_admin | physician | assistant | auditor"
        timestamp created_at
    }
    patients {
        int id PK
        int organization_id FK
        string full_name
        date date_of_birth
        timestamp created_at
    }
    documents {
        int id PK
        int organization_id FK
        int patient_id FK
        int assigned_user_id FK "nullable — null while in the shared pool"
        string filename
        string storage_key "PDF lives in object storage, not the DB"
        string doc_type "referral | lab | letter | discharge"
        string urgency
        string status "received | triaged | assigned | in_review | approved | rejected | archived"
        text summary
        timestamp created_at
    }
    document_events {
        int id PK
        int organization_id FK
        int document_id FK
        int actor_user_id FK
        string from_status
        string to_status
        text note
        timestamp created_at
    }
    audit_log {
        int id PK
        int organization_id FK
        int actor_user_id FK
        string action "e.g. document.viewed, document.approved, user.invited"
        string entity_type
        int entity_id
        json metadata
        timestamp created_at
    }
```

## Two decisions worth defending in an interview

**1. `memberships` is a join table — `role` is NOT a column on `users`.**
`users` ↔ `organizations` is **many-to-many** (a user can belong to several orgs; an org has many users).
A many-to-many is always resolved with a **join table**, and the **role is data about the link**, so it
lives on `memberships`. This lets one person be a *physician at Clinic A and an auditor at Clinic B* —
impossible if `role` sat on the `users` row.

**2. `document_events` and `audit_log` are two different tables.**
- `document_events` = *what happened to the document* — one row per **state change** (`from_status → to_status`). Powers the timeline.
- `audit_log` = *who touched what, everywhere* — one row per **sensitive action, including reads**. Append-only, for the auditor (DSGVO).
- The proof they're different: a physician **opening** a document changes no state → **nothing** in `document_events` → but it **must** appear in `audit_log`. Written at event time ("record it when it happens").

## Indexes we already know we'll need

- `documents (organization_id, status)` — the work-queue query ("open docs of this status in my org").
- `memberships (user_id)` and `memberships (organization_id)` — resolve who's in what.
- `audit_log (organization_id, created_at)` — the auditor's filtered time-range reads.
- `document_events (document_id, created_at)` — a document's timeline.

## Open / next (decisions still Mohamad's to make)

- **Secondary tables not yet designed:** `comments` (physician notes), `lab_values` (structured trends),
  `notifications`, and the chat tables (`chat_sessions`, `chat_messages`) carried over from the old schema.
- **PK type:** `int` autoincrement vs `uuid` — has a real multi-tenant security angle (guessable IDs). Decide with an ADR.
- **Cardinality review:** confirm every relationship line and its nullability.
- Then: `/commit` on the `ENG-12-erd` branch → PR → **set the correct squash title at merge**.
