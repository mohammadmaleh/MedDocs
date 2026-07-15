# Architecture Decision Records (ADRs)

An **ADR** captures *one* significant decision: the context that forced it, what we chose, what we
rejected, and what it costs us. It exists so a future engineer (or interviewer, or future-you) can see
**why**, not just **what** — and so a decision is made **once**, on purpose, instead of drifting.

**Template** (every ADR below follows it):

> **Status** · **Context** (the forces) → **Decision** (what we chose) → **Alternatives considered**
> (and why not) → **Consequences** (good *and* bad) → **Revisit when** (the trigger that reopens it).

| ADR | Decision | Status |
|---|---|---|
| [ADR-001](./ADR-001-monolith.md) | Modular **monolith** over microservices | Accepted |
| [ADR-002](./ADR-002-multi-tenancy.md) | **Shared DB, `organization_id` on every row** (RLS as the strong form) | Accepted |
| [ADR-003](./ADR-003-auth.md) | **Stateless JWT** (authN) + **RBAC read from the DB** (authz) | Accepted |
| [ADR-004](./ADR-004-feature-flags.md) | **Build** a small DB-backed flag service, not buy | Accepted |
| [ADR-005](./ADR-005-file-storage.md) | **Object storage** + API-minted **short-lived presigned URLs** | Accepted |

> An ADR is **immutable once accepted.** If a decision changes, you write a *new* ADR that supersedes the
> old one — you don't edit history. That's the whole point of a *record*.
