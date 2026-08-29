# Infrastructure

Terraform for the Discord agent Lambda. Decisions: [ADR-001](../docs/adr/ADR-001-compute-platform.md)
(Lambda), [ADR-003](../docs/adr/ADR-003-lambda-packaging.md) (zip),
[ADR-004](../docs/adr/ADR-004-terraform-state-and-deploy.md) (local state, manual apply),
[ADR-005](../docs/adr/ADR-005-public-ingress.md) (API Gateway ingress).

Provisions: Lambda function, IAM role (CloudWatch Logs + self-invoke for engine
mode), a log group, and an API Gateway HTTP API (fronting the function) with its
invoke permission.

## One-time deploy

Prerequisites: Terraform ≥ 1.6, AWS CLI configured with credentials, a Neon
`DATABASE_URL`, and a Discord application (see the top-level README).

```bash
# 1. Build the deployment zip (creates ../function.zip)
bash ../scripts/build.sh

# 2. Configure variables
cp terraform.tfvars.example terraform.tfvars   # fill in — gitignored, holds secrets

# 3. Provision
terraform init
terraform apply

# 4. Note the output
terraform output interactions_endpoint_url   # → set as the Interactions Endpoint URL in Discord
terraform output function_name               # → use as the LAMBDA_FUNCTION_NAME CI secret
```

Then register the command (`python -m examples.research_agent.register_command`) and,
if you self-host Postgres, initialize the database (`python db/init_db.py`). On Neon
the `conversations` table already exists from the database-setup step — skip
`init_db.py`, whose `CREATE DATABASE` fails on the pooled endpoint. See
[`docs/setup/deploy.md`](../docs/setup/deploy.md) for the full walkthrough.

## State

State is **local** (`terraform.tfstate`), gitignored because it contains secrets in
plaintext. Back it up manually; don't commit it. See ADR-004 for the rationale and
when to move to a remote backend.

## Ongoing deploys

Code changes deploy via CI (`.github/workflows/deploy.yml`) — `terraform apply` is
only needed when infra (this directory) changes.
