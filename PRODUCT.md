# MedDocs — Product Definition

> Who uses MedDocs, what they are trying to get done, and the main paths they take through it.
> This is the source of truth for every design doc that follows (architecture, ERD, permissions, workflow).

## The problem

A clinic or hospital department receives a constant stream of medical documents — referrals
(*Überweisungen*), lab results (*Laborbefunde*), doctor's letters (*Arztbriefe*), and discharge
letters (*Entlassungsbriefe*). In Germany many still arrive by **fax** or secure medical email
(**KIM**). Today they are sorted by hand, urgent findings can sit unseen, and there is no reliable
record of who read what — a problem under **DSGVO** (GDPR), which governs patient data.

MedDocs ingests these documents, classifies and summarizes them with AI, routes them through a
review workflow, and keeps a tamper-proof record of every access — scoped per organization.

---

## Personas

### 1. Assistant — *Medizinische Fachangestellte (MFA)*  · role: `assistant`
- **Who they are:** the medical assistant at the front desk. First point of contact for incoming documents.
- **What they need to do:** receive/scan documents, let the system classify type and urgency, correct
  it when wrong, and route each document to the right physician. High volume, needs to move fast.
- **What frustrates them today:** manual sorting, no way to flag urgency reliably, documents getting lost.
- **Hard limit:** **cannot make medical decisions** — they triage, they do not approve.
- **Design implication:** a fast **inbox/queue** screen; classification they can override; a one-click assign.

### 2. Physician — *Arzt*  · role: `physician`
- **Who they are:** the doctor responsible for the medical content of a document.
- **What they need to do:** read the document (with a plain-language summary and flagged critical values),
  ask questions grounded in the source, add notes, decide the next step, and **approve or reject** it.
  May request a **second opinion** from another physician.
- **What frustrates them today:** long documents, buried critical lab values, no fast way to ask "what does this say about X".
- **Design implication:** the **document workspace** — PDF viewer, citation-grounded Q&A, lab-value trends,
  and the approve/reject/second-opinion controls.

### 3. Organization Admin — *Praxismanager*  · role: `org_admin`
- **Who they are:** runs the practice/department operationally.
- **What they need to do:** invite and manage users and their roles, configure the organization, monitor
  throughput and workload, manage feature flags.
- **What frustrates them today:** no visibility into who is overloaded, onboarding staff by hand.
- **Hard limit:** operational power, **not a medical role** — does not approve documents.
- **Design implication:** an **admin area** — member management, role assignment, org settings, analytics.

### 4. Auditor — *Datenschutz / Compliance*  · role: `auditor`
- **Who they are:** the data-protection / compliance officer (*Datenschutzbeauftragter*).
- **What they need to do:** inspect the **append-only audit log** — who accessed which patient data and when,
  whether the workflow was followed — and **raise a compliance flag** when something is wrong.
- **Hard limit:** **read-only.** Approves nothing, edits nothing, touches no medical work. *Watches the
  watchers* — separation of duties.
- **Design implication:** a read-only **audit viewer**; every sensitive read must already be logged for them to see.

---

## Core user journeys

> The three main paths through the product, one per primary persona. Document states shown in `code`.

### Journey 1 — Intake & triage  *(Assistant / MFA)*

The document lifecycle's intake half. States shown in `code`.

1. A document arrives — by fax, KIM (secure medical email), or direct upload.
2. The MFA uploads/scans it into MedDocs. → `received`
3. The system extracts the text and classifies **type + urgency** (AI). → `received`
4. The MFA confirms/corrects the classification **and** the patient it belongs to. → `triaged`
5. The MFA routes it: by **default into the shared queue** for its type/urgency (any on-duty
   physician can pull it); **optionally assigned directly** to a specific physician for continuity
   (a returning patient's own doctor). → `assigned`

**Design decision (routing):** pool is the default; direct assignment is an available option.
Availability/capacity/offboarding logic is deliberately deferred — see LATER.

### Journey 2 — Review & sign-off  *(Physician)*

The lifecycle's review half. MedDocs owns the *document's* journey to a recorded decision — the
appointment, exam, and treatment happen outside the system.

1. The physician opens an assigned document from their queue. → `in_review`
2. Reviews it in the **workspace**: AI summary, flagged critical values, citation-grounded Q&A, lab trends.
3. Adds **notes** (their assessment) on the document.
4. Decides — one of:
   - **Approve** → reviewed and medically signed off. → `approved`
   - **Reject** → not actionable / misfiled / wrong patient → returned to triage. → `rejected`
   - **Request second opinion** → another physician reviews before the decision is final.
5. **Reassign** (optional, any time before deciding): if this isn't the right physician, send it back to
   the **pool** or to a **named colleague** — never back to the front desk for a medical reason.
6. Acting on the outcome (appointment, referral, treatment) happens **outside MedDocs**.

### Journey 3 — Oversight & audit  *(Auditor)*

Read-only compliance oversight. Runs **orthogonal** to the document lifecycle — the auditor changes
no document's state. They read the access **trail**, never the medical content (*Datenminimierung*).

1. The auditor opens the **audit viewer** (read-only).
2. Filters the append-only **audit log** — by patient, document, user, action, or time range.
3. Reviews the trail: who accessed which patient's data and when, which workflow transitions occurred
   and by whom, whether SLAs were met, whether any access fell outside a role's scope.
4. On a problem (unauthorized access, illegal/skipped transition, SLA breach) → **raises a compliance
   flag** (recorded; notifies the admin). Fixes nothing directly.
5. If clean → records the review. Nothing in the system changes.

**Design note:** the audit log is **append-only** and written as a *side effect of every sensitive
action* during Journeys 1 & 2. A December review can only see July's activity because it was logged in
July — the same "record it when it happens, read it later" pattern as keyword flagging at upload.

---

## Scope — in vs. LATER

> What the portfolio build includes, what it deliberately is not, and what is explicitly deferred.

**Non-goals — what MedDocs is deliberately NOT:**
- **Not a full EHR / clinic-management system.** No appointments, scheduling, billing (*Abrechnung*),
  insurance, prescriptions, or treatment records.
- MedDocs owns the **document's** journey (arrival → reviewed decision), **not** the patient's clinical care.
- *Rationale:* a focused, finished, deployable slice demonstrates the hard engineering (multi-tenancy,
  workflow state machine, RBAC, async AI pipeline, audit log) better than a sprawling unfinished system —
  and it ships in time to matter. Scope discipline is the point, not a limitation.

**In scope (the portfolio build):**
- **Multi-tenancy** — organizations with proven data isolation (org A cannot see org B's data).
- **Roles & RBAC** — `org_admin`, `physician`, `assistant`, `auditor`; permission matrix; invitations.
- **Intake & AI pipeline** — upload/scan → classify type + urgency → plain-language summary →
  critical-value / keyword flagging → per-page embeddings.
- **Patients** — first-class entity (`organization → patient → documents`); **fake data only**.
- **Review workflow** — guarded state machine (`received → triaged → assigned → in_review →
  approved | rejected → archived`), second opinion, reassignment.
- **Work queues** — shared pool (claim the next one) + optional direct assignment.
- **Document workspace** — PDF viewer, citation-grounded Q&A, notes/annotations, lab-value trends.
- **Audit & compliance** — append-only audit log written automatically at access time; read-only
  auditor viewer; DSGVO story.
- **SLA & notifications** — deadlines + escalation; real-time notifications.
- **Feature flags** — per-tenant, incl. percentage rollout of new AI prompt versions.
- **Admin area** — member management, role assignment, department analytics.

**LATER (explicitly deferred — captured on purpose, not built):**
- **Physician availability** (vacation / out-of-office) and auto-reassignment of their queue.
- **Workload / capacity limits** ("overbooked") and load-balancing rules for the pool.
- **Staff offboarding** — deactivating a physician who retired/left and reassigning their open documents.
- _(These are production/operational concerns — revisit no earlier than M3 when the workflow engine exists.)_
