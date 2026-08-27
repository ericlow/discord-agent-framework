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

## License

MIT — see [LICENSE](LICENSE).
