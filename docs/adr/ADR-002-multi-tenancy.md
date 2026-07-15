# ADR-002 — Multi-tenancy: shared DB, `organization_id` on every row

**Status:** Accepted · M1

## Context
Multiple clinics share one deployment. Their data must be **hard-isolated** (a DSGVO requirement — Clinic A
must never see Clinic B's patients), while a solo operator keeps the ops burden low. IDs appear in URLs.

## Decision
- **One shared database, one shared schema.** Every tenant-owned table carries a **`NOT NULL
  organization_id`** column (`erd.md`) — the one exception is `users` (a global identity linked to orgs via
  `memberships`).
- Isolation is a **uniform filter** `WHERE organization_id = <caller's org>`, applied through a **base
  query helper** so it can't be forgotten per-endpoint. The caller's org comes from the JWT/membership,
  never from the URL.
- **Primary keys are `uuid`** (`gen_random_uuid()`) — non-enumerable, so URL IDs don't leak record count or
  identity. Obscurity is *not* the isolation mechanism; `organization_id` is.
- **Postgres Row-Level Security (RLS)** is the **strong form**: the database itself refuses other tenants'
  rows even if the app forgets the filter. Adopted as the belt-and-braces layer.

## Alternatives considered
- **Database-per-tenant.** Strongest isolation, but N databases to migrate/back up/monitor — ops cost that
  doesn't fit a solo team, and cross-tenant analytics become painful. Rejected at this scale.
- **Schema-per-tenant.** Middle ground; still multiplies migration surface by tenant count. Rejected.
- **Shared rows with only an app-level filter, no RLS.** One forgotten `WHERE` = a cross-tenant breach.
  Rejected as the *sole* mechanism — hence RLS underneath.

## Consequences
**Good:** one migration, one backup, cheap to run; trivial cross-tenant admin analytics; the uniform filter
+ RLS makes isolation **structural**, not per-endpoint discipline.
**Bad:** "noisy neighbour" — one tenant's load touches shared tables (mitigate with indexes/limits); a
single logical DB is a single blast radius (mitigate with RLS + backups).

## Revisit when
A tenant contractually demands physical isolation, or one tenant's scale/noise justifies its own database —
then peel *that* tenant out, keeping shared-rows for the rest.
