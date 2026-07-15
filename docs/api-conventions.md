# MedDocs — API Conventions

> **Status: complete for M1.** The rules every endpoint from M2 onward follows, so the API is consistent
> and a new endpoint can be written from this doc **without guessing**. HTTP status codes and the four
> access gates come from [`permissions.md`](./permissions.md) §2; state-transition semantics come from
> [`workflow.md`](./workflow.md).

The API is **REST over JSON**. Every request and response body is `application/json` (the one exception is
file upload/download — see §7). All timestamps are **ISO-8601 in UTC** (`2026-07-15T13:20:00Z`). All IDs
are **UUIDs** (`erd.md`). Auth is a **bearer JWT**: `Authorization: Bearer <token>`.

---

## 1. Versioning

- **URL-path versioning:** every route is under `/api/v1/…`. The version is visible, cache-friendly, and
  trivial to route.
- **What does *not* bump the version — additive change is safe:** adding a new endpoint, a new *optional*
  request field, or a new field in a response. Clients must ignore unknown response fields, so growth
  doesn't break them.
- **What *does* require `/api/v2` — a breaking change:** removing/renaming a field, changing a field's
  type, making an optional field required, or changing an endpoint's meaning.
- **How v2 is introduced:** stand up `/api/v2` **alongside** `/api/v1`; run both during a published
  deprecation window; announce a sunset date. You never rewrite v1's contract in place — someone is
  depending on it.

> **Why in the URL and not a header?** A header (`Accept: application/vnd.meddocs.v2+json`) is "more
> RESTful" but invisible in a browser, a log, or a `curl`. For a portfolio/product API, an obvious
> `/api/v1` beats theoretical purity. (Trade-off worth stating in an interview.)

---

## 2. The error envelope

**One shape for every error in the whole API.** A client writes its error handling **once**.

```json
{
  "error": {
    "code": "illegal_transition",
    "message": "Cannot approve a document in status 'received'.",
    "details": { "from": "received", "action": "approve", "allowed_from": ["in_review"] }
  }
}
```

| Field | Role | For |
|---|---|---|
| `code` | **stable, machine-readable** slug (`illegal_transition`, `email_taken`) | client branching logic |
| `message` | human-readable, may be reworded or localized | developers, logs, toasts |
| `details` | optional structured context | client to render specifics (e.g. which fields failed) |

**Two levels, don't confuse them:** the **HTTP status** is the coarse category (and drives caching, retries,
and standard tooling); the **`code`** is the specific reason. Many different `code`s can share one status —
`409` covers `illegal_transition`, `email_taken`, and `version_conflict`. The status tells the client
*what kind*; the `code` tells it *exactly which*; the client should **never parse `message`** to decide
logic.

### Status codes we use, and when

| Status | Meaning here | Gate / cause | Example `code` |
|---|---|---|---|
| `400` Bad Request | malformed/nonsensical request the schema can't catch | — | `invalid_query_param` |
| `401` Unauthorized | not authenticated (missing/expired/forged JWT) | gate 1 · authN | `not_authenticated` |
| `403` Forbidden | authenticated, but your **role** can't do this | gate 2 · RBAC | `permission_denied` |
| `404` Not Found | resource doesn't exist **or isn't in your org** | gate 3 · tenancy | `not_found` |
| `409` Conflict | valid request, **wrong state** for the target | gate 4 · guard | `illegal_transition`, `email_taken` |
| `422` Unprocessable | body is well-formed JSON but **fails validation** (Pydantic) | schema | `validation_error` |
| `500` Internal | our bug — never leak internals to the client | — | `internal_error` |

- **`404` for cross-tenant, not `403`:** a `403` would confirm the row exists in another org — a leak.
  To an outsider, it does not exist (`permissions.md` §2).
- **`422` vs `400`:** `422` = valid JSON that breaks a *validation rule* (missing field, bad enum value) —
  FastAPI/Pydantic returns this automatically; we reshape it into the envelope. `400` = the request is
  malformed in a way schema validation doesn't cover (e.g. an un-parseable filter value).
- **`409` vs `422`:** `422` is about the *request*; `409` is about the *resource's state*. Approving a
  `received` doc is a perfectly valid request — the document is just in the wrong state → `409`.

---

## 3. Success responses & pagination

### Single resource
Return the object directly (already unambiguous). `200 OK` for reads/updates; `201 Created` + a `Location`
header for creates; `204 No Content` for a delete/soft-delete with nothing to return.

### Collections — always paginated, always enveloped
A list endpoint **never** returns a bare array. Bare arrays can't carry paging metadata and are a known
JSON-security footgun. Envelope:

```json
{
  "data": [ { "id": "…", "status": "in_review" }, … ],
  "pagination": { "limit": 20, "offset": 0, "total": 137 }
}
```

- **M1 convention: `limit` / `offset`.** Simple, maps directly to SQL `LIMIT/OFFSET`, supports jump-to-page,
  and is plenty for admin lists and queues at our scale. Defaults: `limit=20`, max `limit=100`,
  `offset=0`.
- **Known trade-off (documented, not hidden):** offset pagination **drifts** when rows are inserted/deleted
  between pages — you can see a row twice or skip one. For the **real-time work queue** (constant inserts)
  the correct upgrade is **keyset / cursor pagination** (`?after=<opaque_cursor>`), which is stable under
  writes but gives up random page access. **Decision:** offset now; cursor is a clean, additive upgrade
  (§1) for the queue endpoints when M3's real-time load makes drift real. This is a deliberate deferral,
  not an oversight.

---

## 4. Resource naming & paths

- **Plural nouns for collections:** `/documents`, `/patients`, `/organizations`, `/memberships`.
- **A specific resource by id:** `/documents/{document_id}`.
- **Nesting shows ownership, but stays shallow (≤ 2 levels):** `/documents/{id}/comments` is fine;
  deep-nest no further — link by id instead. Tenancy is **never** a path segment (no `/orgs/{org}/…`);
  the org is derived from the JWT, so it can't be spoofed in the URL.
- **State transitions are action sub-resources, not a `PATCH status`:**
  `POST /documents/{id}/approve`, `/assign`, `/start-review`, `/reject`.

  > **Why not `PATCH /documents/{id}` with `{ "status": "approved" }`?** Because a transition is a
  > **guarded operation**, not a field write. `PATCH status` implies any status is directly settable and
  > invites clients to skip states. A named action endpoint carries the guard, writes the `document_events`
  > row, and returns `409` on an illegal move — the machine from `workflow.md`, exposed honestly.

- **Filtering** = query params named after the field: `?status=in_review&doc_type=lab&urgency=critical`.
- **Sorting** = `?sort=` with `-` for descending: `?sort=-created_at`.
- **Verbs never appear in a path for CRUD** — the HTTP method is the verb. `GET /documents` (not
  `/getDocuments`). Action endpoints (§ above) are the deliberate, documented exception for transitions.

---

## 5. HTTP methods

| Method | Use | Body | Idempotent? |
|---|---|---|---|
| `GET` | read a resource / list | no | yes |
| `POST` | create, or trigger an action/transition | yes | no |
| `PATCH` | partial update of mutable fields | yes (only changed fields) | no |
| `DELETE` | soft-delete (`deleted_at`) — never a hard delete (`permissions.md` §5.7) | no | yes |

`PUT` (full replace) is not used — our updates are always partial.

---

## 6. Worked example

**Request** — a physician lists their in-review queue:

```http
GET /api/v1/documents?status=in_review&limit=20&sort=-created_at
Authorization: Bearer <jwt>
```

**Success — `200 OK`:**

```json
{
  "data": [
    { "id": "0f1c…", "patient_id": "9ab2…", "doc_type": "lab", "urgency": "critical",
      "status": "in_review", "assigned_user_id": "77de…", "created_at": "2026-07-15T09:12:00Z" }
  ],
  "pagination": { "limit": 20, "offset": 0, "total": 3 }
}
```

**Error — same physician calls `POST /api/v1/documents/999/approve` on a `received` doc:**

```http
HTTP/1.1 409 Conflict
```
```json
{
  "error": {
    "code": "illegal_transition",
    "message": "Cannot approve a document in status 'received'.",
    "details": { "from": "received", "action": "approve", "allowed_from": ["in_review"] }
  }
}
```

**Error — a `422` from validation** (`limit=nine` is not an integer):

```json
{
  "error": {
    "code": "validation_error",
    "message": "Query parameter 'limit' must be an integer.",
    "details": { "field": "limit", "given": "nine" }
  }
}
```

---

## 7. A few more rules that keep endpoints consistent

- **File upload/download is the only non-JSON path:** upload is `multipart/form-data`; the PDF itself is
  fetched via a short-lived storage URL, not streamed as JSON. (Access model — proxy vs presigned — is an
  open ADR-005 decision; see the note pinned on ENG-16.)
- **Auth on every protected route** via the `require_permission(...)` dependency (`permissions.md` §7.3);
  the four gates run in order and map to the codes in §2.
- **Never leak internals:** a `500` returns `{ "error": { "code": "internal_error", "message": "…" } }` and
  logs the stack trace server-side — stack traces and SQL never reach the client.
- **`GET /me`** returns the caller's `{ user_id, org_id, role, permissions[] }` so the frontend can
  decorate UI (`permissions.md` §7.4) — read-only, never an input to a server decision.

---

## 8. Deferred

| Item | Decision | Why |
|---|---|---|
| **Cursor/keyset pagination** | offset now, cursor later | Needed when the real-time queue's insert rate makes offset drift real (M3). Additive, non-breaking. |
| **Rate limiting & the `429` code** | M6 (security pass) | Belongs with the hardening milestone; the envelope already has room for a `rate_limited` code. |
| **Idempotency keys for `POST`** | not in M1 | Relevant if we expose retryable client-driven creates; document if/when. |
| **Field selection (`?fields=`) / sparse responses** | not built | YAGNI until a real payload-size problem appears. |
