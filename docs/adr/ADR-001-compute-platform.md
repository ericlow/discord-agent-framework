# ADR-001: Compute platform — AWS Lambda

_Status: accepted_
_Date: 2026-08-27_

**We will host the framework on AWS Lambda (Function URL, one function serving both
the interactions front-half and the engine) because its *always-free* tier — 1M
requests/month with no 12-month expiry — meets the free-hosting goal permanently,
and its serverless model fits the Discord webhook/defer/engine pattern.**

## Context

We need to host a Discord interactions endpoint: an HTTPS URL that verifies the
Ed25519 signature, answers the PING, and runs an agent tool-use loop that far
exceeds Discord's 3-second reply window. Design goals require **free hosting** and
**all-skill-level** accessibility.

This shapes the platform requirements: run **Python** with binary deps
(`psycopg2`, `PyNaCl`); support **long-running** work (tens of seconds to minutes);
and allow a **deferred + background** execution model (reply fast, finish the loop
asynchronously).

## Decision

Use **AWS Lambda** as the compute platform, exposed via a Lambda **Function URL**,
with one function serving both the interactions front-half and the engine (invoked
asynchronously in `mode: "engine"`).

## Consequences

**Positive**
- Always-free tier; no always-on cost.
- Serverless natively supports the webhook/defer/engine pattern (async self-invoke).
- Runs Python with binary deps, so the agent can be built directly against it.

**Negative / costs**
- Setup friction (AWS account, IAM, Function URL, self-invoke permission) works
  against the "all skill levels" goal; must be mitigated with IaC + docs.
- Binary dependencies (`psycopg2`, `PyNaCl`) require Linux-compatible packaging.
- The function needs IAM permission to invoke itself for engine mode.

## Alternatives considered

Judged primarily on the two design goals: **free forever** (not just a trial), and
**fits the Discord interaction model** (an HTTPS endpoint that can defer and then
finish the loop asynchronously).

| Platform | Free forever? | Fits the interaction model? |
|---|---|---|
| **AWS Lambda** | **Yes** — always-free 1M req/mo, no expiry | **Yes** — Function URL + async self-invoke for the deferred engine |
| **AWS EC2** | **No** — free tier is 750 hrs/mo for **12 months only**, then paid | Yes — an always-on server could host it |
| **Cloudflare Workers** | Yes — ~100k req/day | Partial — webhook works, but Python is WASM/Pyodide and can't load `psycopg2` |
| **Vercel** | Partial — Hobby is free but **non-commercial only** | Risky — function duration caps (10–60s) vs a long tool loop |
| **Deno Deploy** | Yes | No — **JS/TS runtime, not Python**; full rewrite |

**Why AWS Lambda:** it's the only option that is free with no time limit *and*
natively fits the defer/async model while running Python with binary deps. EC2 fails
the free-forever goal (12-month trial). Workers, Vercel, and Deno each break on
Python, duration, or licensing.

> Free-tier terms above should be re-verified against current provider docs before
> this ADR is treated as final — they change frequently.
