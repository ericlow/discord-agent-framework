# ADR-001: Compute platform — AWS Lambda

_Status: accepted_
_Date: 2026-08-27_

**We will host the framework on AWS Lambda (Function URL, one function serving both
the interactions front-half and the engine) because its free tier — 1M requests per
month — covers expected load at no cost, and its serverless model fits the
webhook/defer/engine pattern the code already uses.**

## Context

We need to host a Discord interactions endpoint: an HTTPS URL that verifies the
Ed25519 signature, answers the PING, and runs an agent tool-use loop that far
exceeds Discord's 3-second reply window. Design goals require **free hosting** and
**all-skill-level** accessibility.

This shapes the platform requirements: run **Python** with binary deps
(`psycopg2`, `PyNaCl`); support **long-running** work (tens of seconds to minutes);
and allow a **deferred + background** execution model (reply fast, finish the loop
asynchronously). The code is already built this way — one function, two roles.

## Decision

Use **AWS Lambda** as the compute platform, exposed via a Lambda **Function URL**,
with one function serving both the interactions front-half and the engine (invoked
asynchronously in `mode: "engine"`).

## Consequences

**Positive**
- Generous free tier; no always-on cost.
- Serverless matches the webhook/defer/engine pattern the code already uses.
- Consistent with the existing implementation — minimal rework.

**Negative / costs**
- Setup friction (AWS account, IAM, Function URL, self-invoke permission) works
  against the "all skill levels" goal; must be mitigated with IaC + docs.
- Binary dependencies (`psycopg2`, `PyNaCl`) require Linux-compatible packaging.
- The function needs IAM permission to invoke itself for engine mode.

## Alternatives considered

Evaluated against our three needs — Python + binary deps, long-running work, and a
deferred/background model — plus the free tier and setup friction.

| Platform | Free tier | Max exec time | Python + binary deps | Fit for our model |
|---|---|---|---|---|
| **AWS Lambda** | 1M req/mo + 400k GB-s | 15 min | Yes (zip/layer, manylinux wheels) | Native: async self-invoke for engine mode |
| **Cloudflare Workers** | ~100k req/day | 30s CPU (paid); tight on free | Python is beta (Pyodide/WASM); C-extensions like `psycopg2` not supported | Background via `waitUntil`/Queues, but Python+binary story is the blocker |
| **Vercel** | Hobby (non-commercial only) | 10s default, up to 60s on Hobby | Python functions supported; binary deps workable | Long agent loops risk the duration cap; Hobby ToS bars commercial use |
| **Deno Deploy** | Generous free tier | ~short per-request | **JS/TS runtime — no Python** | Would require a full rewrite |

**Why AWS wins for now:** it's the only option that runs our existing Python +
binary-dep code unchanged, comfortably exceeds the runtime our tool loop needs, and
has a first-class async invocation for the deferred engine. Workers' Python/WASM
can't load `psycopg2`; Vercel's Hobby duration cap and non-commercial ToS are
risks; Deno is the wrong language. The cost is setup friction (IAM, packaging),
mitigated by IaC + docs.

> Free-tier limits and duration caps above should be re-verified against current
> provider docs before this ADR is treated as final — they change frequently.
