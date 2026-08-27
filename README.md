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

A full walkthrough from nothing to a running agent. If you just want to run the
tests locally, the [Quickstart](#quickstart) above is enough.

### 1. Gather credentials

- **Anthropic API key** — from the [Anthropic Console](https://console.anthropic.com/).
- **Jina API key** — from [jina.ai](https://jina.ai/), only if you use the built-in
  `search_web` / `fetch_url` tools.
- **Postgres database** — a local instance, or a free-tier host (e.g. Neon, Supabase).
  You'll need its connection string as `DATABASE_URL`.

### 2. Create a Discord application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   and click **New Application**.
2. On the **General Information** page, copy the **Application ID** and **Public Key**.
3. Under **Bot**, click **Reset Token** and copy the **bot token**.
4. Under **OAuth2 → URL Generator**, select the `applications.commands` and `bot`
   scopes, then open the generated URL to invite the bot to your server.
5. (Optional, for instant command registration) enable Developer Mode in Discord,
   right-click your server, and **Copy Server ID** — this is your `DISCORD_GUILD_ID`.

### 3. Install

```bash
git clone <your-fork-url> && cd discord-agent-framework
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 4. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
DISCORD_PUBLIC_KEY=...
DISCORD_APPLICATION_ID=...
DISCORD_BOT_TOKEN=...
DISCORD_GUILD_ID=...          # optional; omit for global (~1h) registration
JINA_API_KEY=...              # only if using the built-in web tools
DATABASE_URL=postgresql://user:pass@host:5432/discord_agent
```

### 5. Initialize the database

Creates the database (name taken from `DATABASE_URL`) and the `conversations` table:

```bash
python db/init_db.py
```

### 6. Register your slash command

Using the bundled example:

```bash
python -m examples.research_agent.register_command
```

### 7. Deploy and connect to Discord

Deploy your handler to a serverless host and set its public URL as the
**Interactions Endpoint URL** in the Developer Portal (Discord sends a PING to
verify the Ed25519 signature). The handler must be able to invoke itself for
engine mode. See [`examples/research_agent/`](examples/research_agent/) for a
complete, deployable example and step-by-step deploy notes.

Then type your slash command (e.g. `/research <question>`) in your server.

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
