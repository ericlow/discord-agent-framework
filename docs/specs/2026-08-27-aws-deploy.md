# AWS Lambda deployment — Feature Spec

_Status: draft_
_Last updated: 2026-08-27_

## Background

The framework and example agent exist and are unit-tested, but there is **no way to
deploy them**: no IaC, no packaging for Lambda's runtime, no CI. Nothing has run
end to end against real Discord/Anthropic. Per policy, infra must be IaC (Terraform)
and deploys must run through CI (GitHub Actions) — no console click-ops. This spec
defines the deploy pipeline for the `research_agent` example as the reference agent.

Decided in [ADR-001](../adr/ADR-001-compute-platform.md): host is AWS Lambda +
Function URL, one function, two roles.

## User story

As a developer, I want to deploy the example agent to AWS with `terraform apply` +
a CI push, so that the `/research` command works in my Discord server without any
manual console setup.

## Acceptance criteria

1. `terraform apply` provisions the Lambda, Function URL, IAM role, and log group.
2. A GitHub Actions workflow builds a Linux-compatible package and updates the
   function on push to `main`.
3. The function can invoke itself (engine mode).
4. Secrets are supplied as env vars, never committed.
5. After deploy + command registration, `/research` returns a sourced answer in
   Discord.

## Technical design

### Components (Terraform)
- `aws_lambda_function` (Python 3.12), handler `examples.research_agent.handler.handler`.
- `aws_lambda_function_url` (auth `NONE`) → the Discord Interactions Endpoint URL.
- `aws_iam_role` + policy: CloudWatch Logs + `lambda:InvokeFunction` on itself.
- `aws_cloudwatch_log_group`.
- Env vars: `DISCORD_PUBLIC_KEY`, `DISCORD_APPLICATION_ID`, `DISCORD_BOT_TOKEN`,
  `ANTHROPIC_API_KEY`, `JINA_API_KEY`, `DATABASE_URL`, `AWS_LAMBDA_FUNCTION_NAME`.

### Packaging
Build the zip in CI on an Ubuntu runner so `psycopg2-binary` and `PyNaCl` resolve to
manylinux wheels natively (`boto3` is provided by the runtime and excluded). No
container image or separate layer needed.

### CI (GitHub Actions)
On push to `main`: install deps into a build dir, zip with the package, and
`aws lambda update-function-code`. AWS creds and app secrets come from GitHub
Secrets. Terraform runs manually (or a separate plan/apply workflow) — TBD.

### Database
Postgres via **Neon** (external free tier). `DATABASE_URL` is a secret; `conversations`
table created by `db/init_db.py` (manual one-time step, documented).

## Behavioral specs (Gherkin)

```gherkin
Scenario: Discord verifies the endpoint
  Given a deployed Function URL set as the Interactions Endpoint
  When Discord sends a PING with a valid signature
  Then the function responds 200 with a PONG

Scenario: Slash command runs the agent
  Given the /research command is registered
  When a user runs "/research <question>"
  Then the reply is deferred within 3s
  And the engine posts progress and a final sourced answer
```

## Decisions

| Question | Decision (proposed) | Rationale |
|---|---|---|
| Postgres host | **Neon** (external, not in IaC) | Free tier; keeps RDS cost/complexity out; fits design goals |
| Packaging | **CI-built zip** (Ubuntu, manylinux wheels) | Simplest reliable path for binary deps; no container/layer |
| Terraform state | TBD | local vs remote (S3) backend — decide before apply |
| Terraform in CI | TBD | manual apply vs automated plan/apply workflow |

## Out of scope

- Multi-agent / multiple functions.
- Custom domain for the Function URL.
- Automated DB migrations (init is a documented one-time step).
