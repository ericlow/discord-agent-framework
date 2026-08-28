# Setup

Go from nothing to a running Discord agent. Work through these in order — each
builds on the last, and the deploy step needs the credentials gathered earlier.

1. **[Discord](discord.md)** — create the server, application, and bot; invite it;
   grab the Application ID, Public Key, Bot Token, and Server ID.
2. **[Database](database.md)** — a free Neon Postgres project; get the pooled
   `DATABASE_URL` and create the `conversations` table.
3. **[Anthropic](anthropic.md)** — a Claude API key (and a little billing credit).
4. **[Jina](jina.md)** — a key for the built-in `search_web` / `fetch_url` tools
   (skip if your agent doesn't use them).
5. **[AWS](aws.md)** — an AWS account and deploy credentials for the AWS CLI.
6. **[Deploy](deploy.md)** — build the package, `terraform apply` the Lambda,
   register the slash command, and set the Interactions Endpoint URL in Discord.

## Where secrets go

- **`infra/terraform.tfvars`** — values Terraform pushes to the Lambda at deploy
  (all of the above). Gitignored.
- **`.env`** (repo root) — values for scripts you run locally (`db/init_db.py`,
  `register_command`). Gitignored.

Both are gitignored and must never be committed. Copy the `.example` files to start.
