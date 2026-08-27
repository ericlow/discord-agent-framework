# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An open-source framework for building **Discord AI agents** on Claude's tool-use
loop. Users define an `Agent` (system prompt + model + tools) and the framework
provides the Discord runtime: interactions endpoint, deferred-response handling,
live progress streaming, and Postgres-backed conversation persistence.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # framework + dev deps (pytest, responses)
pytest                            # run all tests
pytest tests/test_agent.py::test_postprocess_applied   # a single test
python db/init_db.py              # create db (name from DATABASE_URL) + conversations table
```

`.env` (copy from `.env.example`) supplies keys. Tests do **not** need real keys
or a database — the Anthropic client is injected as a fake, and the interactions
tests generate their own Ed25519 keys.

## Architecture

The runtime is the **AWS Lambda HTTP-interactions pattern**, split across two
roles served by one function (`discord_agent/interactions.py`):

- **Front half** (`make_handler`): verify Ed25519 signature → answer PING → for a
  slash command, send a deferred (type 5) response and asynchronously self-invoke
  the same Lambda with `{"mode": "engine", ...}`. This exists because Discord
  demands a reply within 3s but an agent run takes far longer.
- **Engine half** (user-supplied, see `examples/research_agent/handler.py`): load
  or create the conversation, run `Agent.run()`, stream progress to the channel,
  persist, and post the answer.

Key seams:

- **`Agent` (`agent.py`)** is transport-agnostic. The loop reports steps through a
  `progress_hook` callback rather than calling Discord directly — that's what
  makes it testable and reusable. Final text can be transformed by an optional
  `postprocess` hook (e.g. add citations).
- **`Tool` + `ToolRegistry` (`tools.py`)** bundle each tool's schema and handler
  together; the registry derives both the `tools=[...]` array and the dispatch map
  from the same objects, so they can't drift out of sync.
- A leading integer in a command's input value is treated as a **conversation ID**
  for a follow-up turn (see `make_handler` and the example engine).

To build a new agent, follow `examples/research_agent/`: a `config.py` (prompt,
model, tools, command def) and a `handler.py` that wires `Agent` + `persistence`
+ `discord_io` and exposes `interactions.make_handler(engine_handler)`.

## Conventions

- Python 3.9+. Use `.venv/` in the repo root; always invoke `python3`.
- Default model is `claude-opus-4-8` (`agent.DEFAULT_MODEL`).
- Built-in tools (`discord_agent/builtins/`) use the Jina API (`JINA_API_KEY`).
