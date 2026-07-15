# ADR-005 — Object storage for PDFs + API-minted short-lived presigned URLs

**Status:** Accepted · M1 · *(resolves the ENG-14 sanity-pass finding B)*

## Context
Documents are PDFs — binary blobs, some large. They must **not** live in Postgres (bloats the DB, slows
backups, wrong tool). And they are **medical data**: every access must be authorised through the four gates
and **logged in `audit_log`**. So the real question is not just *where the bytes live* but *how the browser
is allowed to fetch them*.

## Decision
- **Object storage** (Cloudflare **R2** in prod, **MinIO** in dev — both speak the **S3 API**). The DB
  stores only a **`storage_key`**; the bytes live in the bucket. The bucket is **private** — never public.
- **Access via API-minted, short-lived presigned URLs.** The browser asks the API for a document; the API
  runs the four gates, **writes the `audit_log` read event**, then returns a **presigned URL scoped to that
  one object with a short TTL** (minutes). The browser fetches the bytes directly from storage using it.
- **This is the caveat to "the frontend talks only to the API"** (`architecture.md`): the browser *does*
  fetch bytes from storage — but only via a capability the **API authorised and minted**. The API stays the
  single authority; it just doesn't proxy the bytes.

## Alternatives considered
- **PDFs in Postgres (`bytea`).** Rejected — DB bloat, slow backups, memory pressure.
- **API proxies every byte** (stream through the app). Safe and simple, keeps the "only talks to the API"
  claim literally true, but the app carries all transfer load. Reasonable fallback; rejected as default for
  scalability.
- **Public bucket / permanent public URLs.** Rejected outright — unauthenticated access to patient data.
- **Long-lived presigned URLs.** Rejected — a leaked URL is a long-lived bearer capability. Short TTL keeps
  the exposure small.

## Consequences
**Good:** the app never streams large blobs (scales); the API keeps authority and audits every read; dev/prod
parity via the S3 API.
**Bad:** a presigned URL is, for its TTL, a **bearer capability** — anyone holding it can fetch that one
object until it expires (mitigate: short TTL, per-object scope, and log the mint). Slightly more moving parts
than proxying.

## Revisit when
Compliance demands that no bytes ever leave via a client-fetchable URL — then switch the default to
API-proxied streaming (the fallback above).
