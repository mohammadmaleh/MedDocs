# ADR-004 — Build a small DB-backed feature-flag service (not buy)

**Status:** Accepted · M1

## Context
We need per-tenant control over features, and — the genuinely important use — to roll out a **new AI prompt/
model version to a small percentage of orgs** and compare it in Langfuse **before** a full rollout. Flags
tie the platform story to the AI story.

## Decision
Build a small **DB-backed** flag service: `evaluate(flag, org, user)` resolves in order **global default →
org override → user override → percentage rollout** (a **stable hash** of the user id, so the same user
stays consistently in-or-out of a rollout). An admin UI toggles them. First flags: `ai_triage`,
`ai_summaries`, `chat_assistant`, `lab_trends`, and a versioned `ai_prompt_v2` gate.

## Alternatives considered
- **Managed SaaS (LaunchDarkly) / OSS (Unleash, Flagsmith).** More features (targeting, dashboards) than we
  need, plus a dependency and (for SaaS) cost and another data processor to justify under DSGVO. Rejected —
  our needs are small and specific.
- **Environment-variable flags.** Can't do per-tenant or percentage rollout, and flipping one needs a
  redeploy. Rejected — the per-tenant % rollout is the whole point.
- **No flags.** Rejected — then there's no safe way to trial a new AI prompt on a subset and compare.

## Consequences
**Good:** full control; per-tenant + percentage rollout tied directly to a Langfuse comparison; a real,
non-trivial platform capability we can demo and explain; no external dependency.
**Bad:** we maintain it (evaluation, caching, the admin UI); it will lack the advanced targeting a mature
product has. Acceptable — **build-vs-buy tilts to build only because the scope is small and the learning +
the AI-rollout use justify it.**

## Revisit when
Flag logic grows complex (audiences, scheduling, dependencies) or the team grows — at which point a mature
tool earns its cost and we migrate.
