# ADR-002: Database — Neon serverless Postgres

_Status: accepted_
_Date: 2026-08-27_

**We will persist conversations in Postgres, hosted on Neon's serverless free tier,
because it is free forever and speaks standard Postgres — so the existing
`psycopg2` + JSONB persistence works unchanged and the design's free-hosting goal
is met permanently.**

## Context

The agent stores each conversation as a JSONB `messages` array so follow-up turns
can reload history (`db/schema.sql`, `persistence.py`). We need a managed database
that a beginner can provision for free and keep free — matching the same
free-forever + all-skill-levels goals that drove [ADR-001](ADR-001-compute-platform.md).

Because the agent runs on Lambda, the store must be reachable over the public
internet and tolerate short-lived, per-invocation connections.

## Decision

Use **Neon** (serverless managed Postgres) on its free tier. Connect with the
standard `DATABASE_URL`; use Neon's pooled connection string for the Lambda runtime.

## Consequences

**Positive**
- Free forever (no 12-month expiry); scales to zero when idle.
- Standard Postgres wire protocol — no code changes to `persistence.py`.
- Managed: no server to run, matching the serverless posture of ADR-001.

**Negative / costs**
- Scale-to-zero adds a cold-start latency spike on the first query after idle.
- Free-tier connection limits mean Lambda should use Neon's pooled endpoint.
- One more external account for the user to create (documented setup step).

## Alternatives considered

Judged first on **free forever**, then on **fit** (works with our Postgres/JSONB
code and Lambda's connection model).

| Option | Free forever? | Fit |
|---|---|---|
| **Neon** | **Yes** — free tier, scale-to-zero | **Best** — standard Postgres, pooled endpoint for serverless, no code change |
| **Supabase** | Yes, but free projects **pause after ~1 week idle** | Good — Postgres too, but auto-pause can stall an idle bot |
| **AWS RDS** | **No** — free tier is 750 hrs/mo for **12 months only** | Good technically, but fails the free-forever goal |
| **DynamoDB** | Yes — always-free (25 GB) | Poor — not Postgres; would require rewriting `persistence.py` and the schema |

**Why Neon:** it's free-forever Postgres that drops into the existing code with a
pooled connection string. Supabase's idle-pause is a reliability risk for a
low-traffic bot; RDS isn't free-forever; DynamoDB would mean a persistence rewrite.

> Free-tier terms (storage caps, idle-pause windows) should be re-verified against
> current provider docs before this ADR is treated as final — they change frequently.
