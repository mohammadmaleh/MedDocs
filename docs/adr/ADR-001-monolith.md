# ADR-001 — A modular monolith, not microservices

**Status:** Accepted · M1

## Context
MedDocs is built by **one developer**, shipping to a moderate number of clinics. The modules
(`auth, orgs, documents, workflow, ai, flags, audit, notifications, analytics`) need clear internal
boundaries, but a workflow transition routinely touches several of them **inside one database
transaction** (update `documents`, write `document_events`, enqueue a `notification`) — and it must be
atomic.

## Decision
One **modular monolith**: a single FastAPI application, internally split into modules, plus (from M6) one
background worker, talking to one PostgreSQL. Deploy is one unit.

## Alternatives considered
- **Microservices (a service per module).** Rejected: microservices solve an **organisational/independent-
  scaling** problem — many teams, parts that scale very differently. We have neither. The cost is real and
  immediate: network calls between modules, **distributed transactions** (a workflow transition would span
  services), separate deploys, and observability overhead — all to solve a problem we don't have.
- **Serverless functions.** Rejected: cold starts and awkward long-lived connections (DB pools,
  WebSockets); splinters the transactional workflow.

## Consequences
**Good:** atomic multi-module transactions for free; one thing to deploy, debug, and reason about;
module boundaries can be refactored cheaply because they're just Python packages, not network contracts.
**Bad:** the whole app scales as one unit (fine at this scale); internal module discipline is on us —
nothing *physically* stops a cross-module shortcut, so boundaries need code review to stay honest.

## Revisit when
A module needs to scale independently, or separate teams own separate parts, **and** we've measured the
monolith as the actual bottleneck. Extract that one module then — not preemptively.
