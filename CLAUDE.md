# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An open-source framework for building **Discord AI agents** on Claude's tool-use
loop. Users define an `Agent` (system prompt + model + tools) and the framework
provides the Discord runtime: interactions endpoint, deferred-response handling,
live progress streaming, and Postgres-backed conversation persistence.

## Design goals

These goals drive every decision here — weigh changes against them:

1. **Accessible to all skill levels.** A beginner should be able to build and ship
   a Discord agent. Minimize required setup, services, and prior knowledge; prefer
   sane defaults and a short happy path over configurability.
2. **Free cloud hosting.** The blessed deployment path must run on free-tier cloud
   hosting — no paid infrastructure required to get an agent live.
3. **Built with agentic coding tools.** Developers are expected to use Claude Code
   (or a similar agentic framework) to build their agent. Keep the structure clear,
   this file strong, and provide templates/examples an AI agent can extend cleanly.
4. **Claude first, provider-agnostic later.** The AI is Claude for now. Leave room
   to support other LLM providers eventually, but do not build multi-provider
   abstraction before it's needed.

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

## Commit policy

**Branching:** During this early phase, commit directly to `main` — no feature
branches. (Revisit once the public API stabilizes or outside contributors arrive.)

**When to commit** — do this proactively, without waiting to be asked:

- After a unit of work is complete and the tree is in a working state — code
  imports/runs and `pytest` passes.
- After a self-contained, user-approved change lands — one feature, one fix, or
  one coherent doc edit is one commit.
- Before ending a session or handing off, commit whatever is in a good state.

Do **not** commit mid-task, partial or broken work, failing tests, or "just to
save progress." Keep each commit a single logical change.

**Before every commit:**

1. Run `pytest` — it must pass.
2. Run the privacy/secret check and confirm it is clean: no credentials (API keys,
   tokens, connection strings) and no non-public identifiers in any committable
   file. (The exact scan is kept out of this file on purpose; run it from local
   project notes.)

**Message format:**

- Imperative subject line, ~50–72 chars ("Add X", not "Added X").
- For anything non-trivial, a blank line then a wrapped body explaining *what* and
  *why* (not a restatement of the diff).
- End with the trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`

## Challenge & approval before implementing

- Sanity-check every request against the codebase and design goals first. If it's
  redundant, conflicts with existing structure, or there's a better option — say so
  and recommend, then stop. Never silently comply with a flawed request.
- Do not start implementation until the user approves the approach. Small,
  explicitly-requested edits are fine; anything with a design choice or multiple
  files needs sign-off first.

## Spec-driven development

- For non-trivial features, write a short spec in `docs/specs/*.md` and get approval
  before coding. Specs live in files, never only in chat.
- Spec sections: **Background/WHY · User story · Acceptance criteria · Technical
  design · Gherkin scenarios (Given/When/Then) · Decisions · Out of scope**.
- Pin library versions in specs. Include a failing test (or make it the first
  implementation step) and keep it as a regression guard.

## Reusable workflows

- Put reusable procedural workflows in `.claude/skills/`, not ad-hoc in chat.

## Infrastructure & deployment

- All cloud infra is defined as **IaC** (Terraform) and committed to the repo. Never
  create or modify infra by hand in a cloud console.
- All deploys run through a **CI workflow** (GitHub Actions) — no manual, local, or
  console deploys.
- Do not click-ops or deploy via console. If the infra/deploy pipeline doesn't exist
  yet, write the IaC + CI *first*, then deploy through it.
- Human-only steps (account signup, adding credentials/secrets) must be minimal and
  documented; everything else is automated.

## Architecture decision records (ADRs)

- Record significant or hard-to-reverse architectural decisions as ADRs in
  `docs/adr/ADR-NNN-title.md`, numbered sequentially, one decision per file.
- Lead with a **1–2 sentence statement** of the decision, before any other prose.
- Sections: **Context · Decision · Status · Consequences** (note alternatives
  considered and why rejected).
- Status flow: `proposed → accepted → superseded` (link the superseding ADR).
- Write the ADR when the decision is made, not retroactively.

Write an ADR when:
- Choosing or replacing a platform, host, or major dependency.
- A decision spans multiple components or is costly to reverse (data model, auth,
  packaging approach).
- Picking one option among several with real trade-offs.
- Overriding a prior ADR or a design goal.

When a request meets a trigger, flag that an ADR is needed and pause before proceeding.
