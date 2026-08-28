# ADR-004: Terraform state & deploy model — local state, manual apply, CI code deploys

_Status: accepted_
_Date: 2026-08-27_

**We will keep Terraform state local and run `terraform apply` manually for infra,
while CI is limited to code deploys (`aws lambda update-function-code`) — because
this stays fully free forever and simple, and still satisfies the IaC + CI-deploy
policy.**

## Context

We need to provision infra and deploy code. Policy requires infra as IaC (not
console) and code deploys through CI. Design goals require free forever and
simplicity. Two coupled questions: where Terraform state lives, and whether
Terraform runs in CI.

A code deploy (`update-function-code`) is just an AWS CLI call with the function
name — it needs **no** Terraform state. Only `terraform apply` needs state. So if
apply stays manual, state can be local and CI needs no access to it.

## Decision

- **Terraform state: local** (`terraform.tfstate` on disk, gitignored). Infra
  changes are applied manually with `terraform apply`.
- **CI: code deploys only** — on push to `main`, run `aws lambda
  update-function-code` with the CI-built zip. Terraform does not run in CI.

## Consequences

**Positive**
- Free forever — no S3 backend, no registry, nothing outside the always-free tier.
- Simplest possible setup; nothing to bootstrap.
- Still policy-compliant: infra is IaC (manual apply ≠ console), code deploys via CI.

**Negative / costs**
- State lives on one machine, with no locking — risk of loss or concurrent
  corruption. Mitigate: gitignore `*.tfstate*`, and back it up manually.
- State holds secrets in plaintext — must never be committed.
- Infra changes aren't gated by CI review; relies on manual discipline.
- Multi-maintainer collaboration would need revisiting (see alternative).

## Alternatives considered

Judged on **free forever** and **simplicity** (goals), given apply is manual.

| Option | Free forever? | Extra account? | Fit |
|---|---|---|---|
| **Local state + manual apply** | **Yes — truly $0** | No | **Best** — zero infra, simplest, enough for a solo maintainer |
| **Remote S3 backend** | No — state is tiny (~cents/yr) but not $0 | No (AWS already) | Durable, locking, CI-automatable; needs a bootstrap bucket |
| **Terraform Cloud free tier** | Yes | **Yes — HashiCorp account** | Free remote state + CI-run apply, but adds a third-party account and platform tie-in |

**Why local:** it's the only option that is *truly* $0 with no additional signups.
We accept the trade-off that it is not the "ideal" (no locking, no CI-run apply,
state on one machine) rather than pay even cents for S3 or add another account for
Terraform Cloud. Revisit if apply moves into CI or multiple maintainers join.
