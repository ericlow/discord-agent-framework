# ADR-003: Lambda packaging — zip artifact

_Status: accepted_
_Date: 2026-08-27_
_Amended: 2026-08-29 — build runs locally (cross-platform pip), not only in CI._

**We will package the Lambda as a zip, not a container image, because zip needs no
registry (Amazon ECR is not free forever) and is the simpler pipeline — while our
small dependency set fits comfortably under the zip size limit. The zip is built
locally as the happy path; CI is an optional convenience.**

## Context

The Lambda from [ADR-001](ADR-001-compute-platform.md) must be shipped as a
deployable artifact. Lambda accepts two formats: a **zip** (≤250 MB unzipped) or a
**container image** (≤10 GB, stored in Amazon ECR). Our dependencies —
`anthropic`, `psycopg2-binary`, `PyNaCl`, `beautifulsoup4`, `lxml`, `requests` —
are well under the zip limit (`boto3` is provided by the runtime). The binary deps
(`psycopg2-binary`, `PyNaCl`, `lxml`) ship prebuilt manylinux wheels, which pip can
download for the Lambda target from any host — `pip install --platform
manylinux2014_x86_64 --python-version 3.12 --only-binary :all:` — so the artifact
does **not** require a Linux build machine.

## Decision

Build a **zip** with `scripts/build.sh`, excluding `boto3`. The build fetches Linux
`x86_64` wheels via the cross-platform pip flags above and copies in the pure-Python
framework/example source, so it runs on any developer machine (including macOS)
without Docker. The happy path uploads it via `terraform apply` (Terraform owns both
the function and its code); CI (`aws lambda update-function-code`) remains available
as an optional convenience for auto-deploy on push.

## Consequences

**Positive**
- No registry: nothing to provision, and nothing that leaves the free-forever tier.
- Simplest pipeline — install, zip, upload; fewer concepts for a beginner.
- Faster cold starts than a container image.

**Negative / costs**
- Relies on every dependency shipping a manylinux `x86_64` wheel; a future pure-sdist
  dep with a C extension would break the cross-platform build and force a Linux/Docker
  build or a wheel-less workaround.
- 250 MB unzipped ceiling — fine now, but heavy future deps could force a revisit.
- Less local/prod parity than a pinned image (acceptable at this size).

## Alternatives considered

Judged on **free forever** and **simplicity/fit**.

| Option | Free forever? | Fit |
|---|---|---|
| **Zip artifact** | **Yes** — no registry | **Best** — small deps, fewest moving parts, fast cold start |
| **Container image (Docker + ECR)** | **No** — ECR private storage is free for 12 months only, then paid | Better reproducibility/parity, but needs an ECR repo, registry auth, and image cleanup |

**Why zip:** the container route's only real wins (reproducibility, parity, headroom)
don't matter at our size, while it adds ECR — extra infrastructure that is not
free forever. Zip keeps the whole stack free and simple.

