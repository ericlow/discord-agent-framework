# discord-agent-framework

A small, open-source framework for building **Discord AI agents** on Claude's
tool-use loop. You define an agent — a system prompt, a model, and a set of
tools — and the framework handles the Discord plumbing: signature verification,
the 3-second deferred-response dance, streaming progress back to the channel,
and persisting conversations for follow-up turns.

## How it works

Discord requires a response to a slash command within 3 seconds, but an agent
run takes much longer. The framework uses the standard AWS Lambda split:

1. **Interactions handler** verifies Discord's Ed25519 signature, answers the
   verification PING, and for a slash command sends a *deferred* response
   immediately — then asynchronously self-invokes the same Lambda in "engine
   mode".
2. **Engine** loads or creates the conversation, runs the `Agent` tool-use loop
   (posting live progress like "Running: search_web(...)" to the channel), then
   posts the final answer and persists the conversation.

A single Lambda function serves both roles.

## Core concepts

```python
from discord_agent import Agent, Tool

weather = Tool(
    name="get_weather",
    description="Get the weather for a city.",
    handler=lambda inp: call_weather_api(inp["city"]),
    input_schema={"type": "object",
                  "properties": {"city": {"type": "string"}},
                  "required": ["city"]},
)

agent = Agent(system_prompt="You are a helpful assistant.", tools=[weather])
answer = agent.run(messages, progress_hook=print)  # messages is the Anthropic format
```

- **`Tool`** bundles the Anthropic schema and the Python handler together, so
  they can't drift apart. **`ToolRegistry`** builds both the `tools=[...]` array
  and the dispatch map from the same objects.
- **`Agent`** runs the tool-use loop. It's transport-agnostic: it reports
  progress through a `progress_hook` callback, so the same loop backs a Discord
  bot, a CLI, or a test.
- Two built-in tools ship in `discord_agent.builtins`: `search_web` and
  `fetch_url` (both use the Jina API).

## Layout

```
discord_agent/          the framework package
  agent.py              the Agent tool-use loop
  tools.py              Tool + ToolRegistry
  interactions.py       Discord interactions handler (make_handler)
  discord_io.py         channel posts, deferred reply, 2000-char split
  register.py           slash-command registration
  persistence.py        Postgres conversation CRUD
  builtins/             search_web, fetch_url
db/                     schema.sql (conversations) + init_db.py
examples/research_agent one runnable agent end to end
tests/                  unit tests
```

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # fill in your keys
python db/init_db.py          # create the conversations table
pytest                        # run the tests
```

See [`examples/research_agent/`](examples/research_agent/) for a complete,
deployable agent (a `/research` command that searches the web and answers with
sources).

## Requirements

- Python 3.9+
- An Anthropic API key
- Postgres (for conversation persistence)
- A Discord application + bot
- A Jina API key (only if you use the built-in web tools)

## Setup

Full step-by-step guides live in [`docs/setup/`](docs/setup/) — start with the
[setup index](docs/setup/README.md), which runs in order:

1. [Discord](docs/setup/discord.md) — server, application, bot, invite
2. [Database](docs/setup/database.md) — free Neon Postgres
3. [Anthropic](docs/setup/anthropic.md) — Claude API key
4. [Jina](docs/setup/jina.md) — web-tools key (only for the built-in tools)
5. [AWS](docs/setup/aws.md) — account + deploy credentials
6. [Deploy](docs/setup/deploy.md) — build, `terraform apply`, register the command,
   and connect Discord

If you just want to run the tests locally, the [Quickstart](#quickstart) above is
enough.

## Known trade-offs & open questions

The framework's [design goals](CLAUDE.md#design-goals) are: accessible to all skill
levels, deployable on free cloud hosting, friendly to agentic coding tools, and
Claude-first (provider-agnostic later). A couple of current choices are in tension
with the first two goals and are still open for reconsideration:

- **AWS Lambda as the runtime.** The webhook/interactions model is a good fit for
  free serverless hosting (no always-on server), but AWS specifically — account
  signup, IAM, credit card, Function URL — is a steep on-ramp for a beginner. Other
  free serverless hosts with the same request/response shape (e.g. Cloudflare
  Workers, Vercel, Deno Deploy) may lower the barrier. The "blessed" free-hosting
  path is not yet settled.
- **Mandatory Postgres.** Conversation persistence currently requires a Postgres
  database (a second service to provision, even on a free tier). For a beginner's
  first agent this may be more than is needed; persistence could become *optional*
  with a zero-setup default, and Postgres opt-in for multi-turn follow-ups.
- **Single provider.** The agent loop is Claude-only today. Supporting other LLM
  providers is a possible future direction, deliberately deferred until needed.

Contributions and opinions on these are welcome.

## License

MIT — see [LICENSE](LICENSE).
