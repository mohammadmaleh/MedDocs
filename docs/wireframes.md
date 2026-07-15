# MedDocs — Wireframes (lo-fi)

> **Status: complete for M1.** Lo-fi wireframes for the two core screens — **boxes and flows, not pixels.**
> No colour, no polish; the design system is M5. Their job is to prove the screens can *express* the model
> we designed: [`permissions.md`](./permissions.md) (what each role may see/do), [`workflow.md`](./workflow.md)
> (states, guards, SLA), and [`erd.md`](./erd.md) (the data on screen).
>
> **The rule that drives both screens:** the UI *decorates* (hides/disables what you can't do) using the
> `permissions[]` array from `GET /me`; the **backend still enforces** every action. A hidden button is a
> courtesy, not a control (`permissions.md` §7.4).

---

## Screen 1 — Inbox / Work Queues

**Primary users:** `assistant` (routes intake), `physician` (works their queue). `org_admin` sees the same
list but **metadata only**; `auditor` doesn't use this screen (they have the audit viewer).

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ MedDocs        Klinik Nord ▾            🔔 3   Dr. Schmidt (physician) ▾   [⎋]  │
├────────────┬──────────────────────────────────────────────────────────────────┤
│ VIEWS      │  Filters:  Type[all ▾]  Urgency[all ▾]  Status[all ▾]   🔍search   │
│ ▸ Shared   │ ┌──────────────────────────────────────────────────────────────┐ │
│   pool (12)│ │ ⚠ URG │ Patient  │ Type     │ Status      │ Assignee │ SLA    │ │
│ ▸ My queue │ ├──────────────────────────────────────────────────────────────┤ │
│   (4)      │ │ 🔴crit │ P-10421  │ lab      │ received•   │ —        │ ⏱ 08:12│ │  ← pool SLA ticking
│ ▸ Awaiting │ │ 🟠urg  │ P-09980  │ referral │ triaged     │ —        │ ⏱ 41:59│ │  [Claim]
│   2nd op(1)│ │ ⚪rout │ P-10233  │ letter   │ assigned    │ Dr. S    │ ✓ ok   │ │  [Open]
│            │ │ 🔴crit │ P-10422  │ lab      │ in_review   │ Dr. S    │ 🔺BREACH│ │  ← review SLA breached
│ ─────────  │ │ ⚪rout │ P-10111  │ discharge│ awaiting_2nd│ Dr. S    │ ⏸ paused│ │  ← consult timer
│ Analytics  │ └──────────────────────────────────────────────────────────────┘ │
│ (admin)    │           « 1 2 3 »        limit 20 · showing 1–20 of 137          │
└────────────┴──────────────────────────────────────────────────────────────────┘
        • "received•" with a dot = pipeline done, needs human triage (§3.1 workflow)
```

**Annotations (each ties to a decision):**
- **Rows show `read_metadata` only** — urgency, patient *ref*, type, status, assignee, SLA. **No diagnosis,
  no PDF** on this screen. That's why `org_admin` can see the list but not open content (`permissions.md`
  §5.3 — envelope vs letter).
- **Two SLA signals** per row (`workflow.md` §7): a **pool** clock on unassigned rows (`received`/`triaged`),
  a **review** clock on `assigned`/`in_review`; `awaiting_second_opinion` shows **paused**. Breaches turn
  red and float up.
- **`[Claim]`** appears on shared-pool rows only; claiming is `triaged → assigned` with
  `FOR UPDATE SKIP LOCKED` under the hood (M3) so two people can't grab the same row.
- **`[Open]`** appears on rows assigned to *me* → goes to Screen 2.
- **`received•`** (dot) = the `(status=received, pipeline_status=done)` human-triage case — a real, visible
  queue, not a hidden state (`workflow.md` §3.1).
- **Filters** map 1:1 to query params: `?type=&urgency=&status=` (`api-conventions.md` §4).

---

## Screen 2 — Document Workspace

**Primary user:** `physician` (review + decide). This is the "letter", so it requires `read_content`.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ ‹ Queue   P-10422 · Laborbefund · 🔴 critical           Status: in_review      │
├───────────────────────────────────────┬───────────────────────────────────────┤
│                                        │  [Summary] [Findings] [Trends] [Q&A]  │  ← right-panel tabs
│         PDF VIEWER                      │ ┌───────────────────────────────────┐ │
│   ┌─────────────────────────┐          │ │ AI SUMMARY (plain German)         │ │
│   │                         │          │ │ "Kalium stark erhöht (6.8)…"      │ │
│   │   page 2 of 4           │          │ ├───────────────────────────────────┤ │
│   │   [highlighted region]  │◀─────────┼─│ ⚠ CRITICAL FINDINGS               │ │
│   │                         │  citation│ │  • Kalium 6.8 mmol/L  [p.2] ◀──────┼─┼ click → jumps + highlights
│   └─────────────────────────┘   jump   │ │  • eGFR 22            [p.3]        │ │
│   ◀ ▉ ▉ ▉ ▉ ▶   zoom − +                │ ├───────────────────────────────────┤ │
│                                        │ │ Q&A  "What is the K+ trend?"      │ │
│   ── Notes / annotations ──            │ │  ↳ "Rising since May [p.2]"       │ │  ← grounded, cited
│   [ + add note ]                       │ └───────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────┤
│  ACTION BAR (permission + state driven):   [Approve] [Reject] [2nd opinion] [Reassign] │
└────────────────────────────────────────────────────────────────────────────────┘
```

**Annotations:**
- **The action bar is the state machine made visible.** Which buttons render depends on **current state ×
  my permission × am-I-the-assignee** (`workflow.md` §5):
  - `assigned` & mine → **[Start review]** only.
  - `in_review` & mine → **[Approve] [Reject] [Request 2nd opinion] [Reassign]**.
  - not mine, or wrong state → buttons **hidden/disabled** (decorate) — and the **server still returns 409/403**
    if called anyway (enforce).
- **Citations are clickable and grounded** — each finding/answer carries `[p.N]`; clicking scrolls the PDF to
  that page and highlights the region (the real page numbers from D1's fix, not arithmetic).
- **`read_content` gate** — reaching this screen at all requires `document:read_content`, so `org_admin`
  never lands here (`permissions.md`). Every open is written to `audit_log` (§ the read is a sensitive action).
- **Reject** opens a required **reason** field (guard: reason mandatory, `workflow.md` row 10).
- **Request 2nd opinion** → picks a colleague, moves to `awaiting_second_opinion`, notifies them; **I stay
  the assignee and the only approver.**
- **Trends tab** = `lab_values` for this patient over time with reference bands (`erd.md`).

---

## Two flows (how a document moves through the screens)

```
INTAKE (assistant)      Screen 1 ── claim/assign ──▶ (routes to a physician's queue)
                        received• → triaged → assigned

REVIEW (physician)      Screen 1 [Open] ──▶ Screen 2 ── Start review ──▶ in_review
                        ── Approve / Reject ──▶ archived
                        └─ Request 2nd opinion ──▶ awaiting_second_opinion ──▶ back to in_review
```

## Deliberately not designed here (M5)
Colour, type scale, spacing, components, empty/loading/error states, responsive/mobile, WCAG AA — all M5,
where the design system is built for real. These wireframes commit only to **layout and flow**.
