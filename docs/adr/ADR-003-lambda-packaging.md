# ADR-003: Lambda packaging — CI-built zip

_Status: accepted_
_Date: 2026-08-27_

**We will package the Lambda as a zip built in CI, not a container image, because
zip needs no registry (Amazon ECR is not free forever) and is the simpler pipeline
— while our small dependency set fits comfortably under the zip size limit.**

## Context

The Lambda from [ADR-001](ADR-001-compute-platform.md) must be shipped as a
deployable artifact. Lambda accepts two formats: a **zip** (≤250 MB unzipped) or a
**container image** (≤10 GB, stored in Amazon ECR). Our dependencies —
`anthropic`, `psycopg2-binary`, `PyNaCl`, `beautifulsoup4`, `lxml`, `requests` —
are well under the zip limit (`boto3` is provided by the runtime). The binary deps
(`psycopg2-binary`, `PyNaCl`) ship manylinux wheels, so they install cleanly when
the artifact is built on a Linux runner.

## Decision

Build a **zip** in CI on an Ubuntu runner (native manylinux wheels), excluding
`boto3`, and upload it with `aws lambda update-function-code`.

## Consequences

**Positive**
- No registry: nothing to provision, and nothing that leaves the free-forever tier.
- Simplest pipeline — install, zip, upload; fewer concepts for a beginner.
- Faster cold starts than a container image.

**Negative / costs**
- Build must run on Linux to resolve manylinux wheels (CI already is).
- 250 MB unzipped ceiling — fine now, but heavy future deps could force a revisit.
- Less local/prod parity than a pinned image (acceptable at this size).

## Alternatives considered

Judged on **free forever** and **simplicity/fit**.

| Option | Free forever? | Fit |
|---|---|---|
| **CI-built zip** | **Yes** — no registry | **Best** — small deps, fewest moving parts, fast cold start |
| **Container image (Docker + ECR)** | **No** — ECR private storage is free for 12 months only, then paid | Better reproducibility/parity, but needs an ECR repo, registry auth, and image cleanup |

**Why zip:** the container route's only real wins (reproducibility, parity, headroom)
don't matter at our size, while it adds ECR — extra infrastructure that is not
free forever. Zip keeps the whole stack free and simple.

