# Research agent (example)

A minimal Discord agent built on `discord_agent`. It exposes a `/research`
slash command that investigates a question or URL with `search_web` + `fetch_url`
and posts a sourced answer, streaming progress to the channel as it works.

This example shows the whole pattern in three small files:

- `config.py` — the agent-specific bits: system prompt, model, tools, and the
  slash-command definition.
- `handler.py` — the Lambda entry point. `engine_handler` loads/creates the
  conversation, runs the `Agent`, and delivers the result; the top-level
  `handler` is built by `discord_agent.interactions.make_handler`.
- `register_command.py` — one-time slash-command registration.

## Prerequisites

- A Discord application + bot (Developer Portal), invited to a test server.
- An Anthropic API key and a Jina API key (for the built-in web tools).
- A Postgres database with the `conversations` table (see `db/` at the repo root).

## Environment

Set these (see `.env.example` at the repo root):

```
DISCORD_PUBLIC_KEY=...
DISCORD_APPLICATION_ID=...
DISCORD_BOT_TOKEN=...
DISCORD_GUILD_ID=...          # optional; instant registration to one server
ANTHROPIC_API_KEY=...
JINA_API_KEY=...
DATABASE_URL=postgresql://user:pass@host:5432/discord_agent
AWS_LAMBDA_FUNCTION_NAME=...  # this function's own name (for engine self-invoke)
```

## Deploy

1. Initialize the database: `python db/init_db.py`
2. Register the command: `python -m examples.research_agent.register_command`
3. Deploy `examples/research_agent/handler.py` as a Lambda function with the
   `handler` entry point (`examples.research_agent.handler.handler`), behind a
   Function URL or API Gateway. Give the function `lambda:InvokeFunction` on
   itself so it can self-invoke in engine mode.
4. Set the Function URL as the **Interactions Endpoint URL** in the Developer
   Portal. Discord will send a PING to verify.

Then type `/research <your question>` in your server.
