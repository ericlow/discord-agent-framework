# ADR-001: Compute platform — AWS Lambda

_Status: accepted_
_Date: 2026-08-27_

**We will host the framework on AWS Lambda, exposed via a Function URL, with one
function serving both the Discord interactions front-half and the agent engine.**

## Context

The framework's blessed deployment path needs to host a Discord **interactions
endpoint**: an HTTPS URL that verifies Discord's Ed25519 signature, answers the
verification PING, and runs an agent tool-use loop that can take far longer than
Discord's 3-second reply window. Design goals require the path to run on **free
cloud hosting** and be **approachable for all skill levels**.

The request/response, bursty nature of a webhook agent fits a serverless model
well (no always-on server). The existing codebase is already structured around
this shape: a single function serving two roles (front-half defer + engine
self-invoke).

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

- **Cloudflare Workers / Vercel / Deno Deploy** — lower setup friction and a better
  fit for the beginner/free goals, but a larger port away from the Lambda-shaped
  code. Rejected for now: the decision is to continue on AWS.
