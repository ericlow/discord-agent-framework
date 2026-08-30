# Deploy

Take the agent from code to a live `/research` command in your Discord server. This
walkthrough reflects a real end-to-end deploy.

**Prerequisites** — finish the earlier setup steps so `infra/terraform.tfvars` and
`.env` are filled in: [Discord](discord.md), [Database](database.md),
[Anthropic](anthropic.md), [Jina](jina.md) (if using web tools), and
[AWS](aws.md). You also need, locally:

- **Terraform ≥ 1.6** and the **AWS CLI**, with `aws sts get-caller-identity` succeeding.
- **Python 3.9+** with the project installed (`pip install -e ".[dev]"`) for the
  build, database, and command-registration steps.

No Docker required.

## 1. Build the deployment zip

```bash
bash scripts/build.sh        # → function.zip at the repo root
```

This downloads the Linux `x86_64` wheels for the compiled dependencies (via pip's
`--platform`/`--only-binary` flags) and bundles the pure-Python source, so it
produces a correct Lambda package **on any OS, including macOS, without Docker**
([ADR-003](../adr/ADR-003-lambda-packaging.md)). The zip is ~16 MB — well under
Lambda's 50 MB direct-upload limit.

## 2. Provision the infrastructure

```bash
cd infra
terraform init              # first time only
terraform apply             # review the plan, then type: yes
```

This creates (~10 resources): the Lambda function + its IAM role (CloudWatch Logs
and self-invoke for engine mode), a log group, and an **API Gateway HTTP API**
(api, integration, route `POST /`, `$default` stage) that fronts the function.

> **Why API Gateway and not a Lambda Function URL?** If your AWS account has *Lambda
> Block Public Access* enabled, Function URLs return `403` no matter what — so we use
> API Gateway, which keeps the function private and the account guardrail on. See
> [ADR-005](../adr/ADR-005-public-ingress.md).

## 3. Read the outputs

```bash
terraform output interactions_endpoint_url   # → Discord Interactions Endpoint URL (step 6)
terraform output function_name               # → LAMBDA_FUNCTION_NAME for CI (step 7)
```

The endpoint looks like `https://xxxxxxxx.execute-api.<region>.amazonaws.com/`.

## 4. Initialize the database

**Using Neon (the blessed path)?** The `conversations` table was already created
during the [Database](database.md) step — **skip this step.** Do *not* run
`db/init_db.py` against Neon's **pooled** endpoint: it issues `CREATE DATABASE`,
which PgBouncer rejects.

**Using your own/local Postgres?**

```bash
python db/init_db.py         # creates the database (from DATABASE_URL) + conversations table
```

## 5. Register the slash command

```bash
python -m examples.research_agent.register_command
```

Reads `DISCORD_APPLICATION_ID` / `DISCORD_BOT_TOKEN` / `DISCORD_GUILD_ID` from `.env`.
With `DISCORD_GUILD_ID` set it registers to that server (**instant**); without it,
registration is **global** (~1 hour to propagate). A `201`/`200` response means success.

## 6. Set the Interactions Endpoint URL in Discord

1. [Discord Developer Portal](https://discord.com/developers/applications) → your app
   → **General Information**.
2. Paste the `interactions_endpoint_url` from step 3 into **Interactions Endpoint URL**.
3. **Save Changes.**

On save, Discord sends **two** signed test requests — one **valid** PING (your handler
must answer with a PONG) and one **deliberately invalid** (your handler must reject it).
If both pass, it saves with a green confirmation. You can confirm from the logs:

```bash
aws logs tail /aws/lambda/$(cd infra && terraform output -raw function_name) --since 10m
```

You should see two invocations — one clean, one logging `invalid signature`.

## 7. Test it

In your server, run the command:

```
/research what is the capital of France and one interesting fact about it
```

Expected: an instant "thinking…" reply (the deferred response), then live progress
edits (`Running: search_web(...)`), then a final answer with a **Sources** line. The
conversation is persisted for follow-up turns.

## 8. (Optional) Ongoing deploys via CI

`terraform apply` deploys both infra and code, so it's all you need. For automatic
**code** deploys on push, set these **GitHub Actions secrets** and let
`.github/workflows/deploy.yml` run `aws lambda update-function-code`:

- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` — the deploy user's keys
- `LAMBDA_FUNCTION_NAME` — from `terraform output function_name`

Until these are set, the workflow **skips itself** on push (it logs a notice and
exits green), so you won't see failed CI runs while using the local `terraform
apply` path.

Infra changes (the `infra/` directory) are still applied manually with Terraform
([ADR-004](../adr/ADR-004-terraform-state-and-deploy.md)).

## Troubleshooting

- **Discord: "interactions endpoint could not be verified."** Tail the logs
  (command above). *No log lines at all* → the request isn't reaching the function
  (an ingress/permission problem). *`invalid signature` on the valid PING too* →
  `DISCORD_PUBLIC_KEY` in `terraform.tfvars` doesn't match the app's Public Key in
  the portal.
- **`curl` to the endpoint returns 404.** Expected for `GET` — the route is `POST /`
  only. Discord uses `POST`.
- **Function URL returns 403 (`AccessDeniedException`) with zero invocations.** The
  account has Lambda Block Public Access enabled; this is exactly why the blessed
  path uses API Gateway ([ADR-005](../adr/ADR-005-public-ingress.md)).
- **First invocation is slow (~2.6 s).** Cold start; warm invocations run in a few ms.
