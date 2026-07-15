# ADR-003 — Authentication (stateless JWT) + Authorization (RBAC read from the DB)

**Status:** Accepted · M1

> **Two mechanisms, one ADR — kept explicitly separate** (`permissions.md` §1). **AuthN** = *are you who you
> say you are?* **AuthZ** = *what may you do?* Confusing them is the root of most access-control bugs.

## Context
A multi-tenant API with four roles per membership. It must scale horizontally (no sticky sessions), and a
demotion must take effect **immediately** — you cannot wait for a token to expire before revoking power.

## Decision
- **Authentication — stateless JWT.** The token is `header.payload.signature`. On each request the server
  **recomputes** the signature over the incoming `header.payload` using `SECRET_KEY` and compares it to the
  signature in the token. Match → genuine and untampered. **No database is touched** for authN; the
  `SECRET_KEY` is an *ingredient*, never a stored signature. Expiry is the `exp` claim in the payload.
- **Authorization — RBAC, role read from the DB per request.** The role lives on the **`membership`** row,
  not on `users` and **not in the token**. After authN yields a `user_id`, we load the membership for
  `(user_id, organization_id)` to get the **current** role, then check a **static `ROLE_PERMISSIONS` map**
  via a `require_permission()` dependency. Permissions attach to **roles only**, never to individual users.
- **The four gates, in order:** authN (401) → RBAC (403) → tenancy (404) → guard (409).
- **Refresh-token rotation** (M2) keeps access tokens short-lived so the revocation window is small.

## Alternatives considered
- **Server-side sessions.** Stateful, needs a shared session store, complicates horizontal scaling.
  Rejected — statelessness is the point.
- **Role baked into the JWT.** No per-request DB read, but the role goes **stale**: a demotion wouldn't take
  effect until expiry. Rejected — the one indexed membership lookup buys immediate revocation.
- **Per-user permission grants / DB-driven custom roles.** Rejected: four fixed clinical roles; a static,
  version-controlled, PR-reviewable map beats a role-builder nobody asked for (YAGNI). Per-user exceptions
  are how RBAC rots.
- **Third-party IdP (Auth0/Cognito).** Reasonable in production, but hides the fundamentals this project
  exists to demonstrate. Rejected for the portfolio build.

## Consequences
**Good:** stateless → scales horizontally; immediate revocation via the DB role read; authZ is one static
map, reviewable in a PR; the scope check (tenancy) is deliberately *not* in the permission string, so a
static string can never authorise a cross-tenant row.
**Bad:** a valid JWT can't be revoked *before* expiry (mitigate: short expiry + refresh rotation); one
indexed membership query per request (cheap, and it's what enables revocation).

## Revisit when
We need SSO / external identity, or org-configurable roles become a real customer requirement (then design
custom roles + audit them brutally — see `permissions.md` §8).
