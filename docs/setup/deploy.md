# Deploy

> **Stub — to be written while walking through a real deploy.**

Prerequisites: finished [Discord](discord.md), [Database](database.md),
[Anthropic](anthropic.md), and (if using web tools) [Jina](jina.md), so
`infra/terraform.tfvars` is filled in. Plus AWS CLI credentials configured locally
(`aws sts get-caller-identity` should succeed) and Terraform ≥ 1.6 installed.

Planned steps (see [`infra/README.md`](../../infra/README.md) for current detail):

1. Build the deployment zip — `bash scripts/build.sh`
2. Provision infra — `cd infra && terraform init && terraform apply`
3. Read outputs — `terraform output function_url` / `function_name`
4. Register the slash command — `python -m examples.research_agent.register_command`
5. Set the Function URL as the **Interactions Endpoint URL** in the Discord Developer
   Portal (Discord verifies with a signed PING)
6. Configure CI secrets (`AWS_*`, `LAMBDA_FUNCTION_NAME`) for ongoing code deploys
7. Test `/research` in your server

_TODO: flesh out each step with exact commands, screenshots of the Interactions URL
field, and troubleshooting, captured during the first real deploy._
