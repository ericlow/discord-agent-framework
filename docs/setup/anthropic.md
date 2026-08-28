# Setting up Anthropic (the AI)

The agent calls Claude for its reasoning and tool use. You need an Anthropic API key.

> **Cost note:** the *hosting* is free (Lambda, Neon), but Claude API usage is **not**
> — Anthropic bills per token. You must add a small amount of credit for the key to
> work. This is the one part of the stack that costs money; usage for a personal bot
> is typically cents per interaction.

## 1. Create an API key

1. Sign up / sign in to the **Claude Developer Platform** at
   <https://platform.claude.com> (the console formerly at `console.anthropic.com`).
2. Add credit under **Billing** (a few dollars is plenty to start) — without it, API
   calls fail with an insufficient-credit error.
3. Go to **Settings → API Keys** (keys live under a workspace, e.g. `default`), click
   **Create Key**, name it, and copy the value (`sk-ant-...`). You see it only once.

> On the keys/settings pages you may notice **Identity Federation** — that's an
> enterprise SSO feature (log in via your own identity provider). It's optional and
> **not needed** for a personal API key; you can ignore it.

## 2. Save the key

It **is a secret**. Save it in both gitignored files — never commit it:

- `infra/terraform.tfvars` → `anthropic_api_key = "sk-ant-..."` (Terraform sets the
  Lambda env)
- `.env` at the repo root → `ANTHROPIC_API_KEY=sk-ant-...` (for local testing)

## Model & cost

The agent defaults to `claude-opus-4-8` (`discord_agent/agent.py`, `DEFAULT_MODEL`).
Opus is the most capable and most expensive model. To reduce cost, set a cheaper
model (e.g. a Sonnet or Haiku model id) when constructing the `Agent` in your
agent's `config.py`.
