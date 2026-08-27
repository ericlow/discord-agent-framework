"""The Agent: a configurable Claude tool-use loop.

An ``Agent`` bundles a system prompt, model, and a set of tools, and exposes a
single ``run()`` method that drives the Anthropic tool-use loop to completion.
The loop is transport-agnostic: instead of writing to Discord directly, it calls
an optional ``progress_hook`` with human-readable status strings, so the same
loop can back a Discord bot, a CLI, or a test harness.
"""
from __future__ import annotations

import json
import logging
from typing import Callable, Optional

import anthropic

from .tools import Tool, ToolRegistry

log = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOOL_CALLS = 20
DEFAULT_MAX_TOKENS = 4096

# Called with a short status line each time the agent takes a visible step.
ProgressHook = Callable[[str], None]
# Optional final-text post-processor, e.g. to add citations. Receives the final
# text and the full message history; returns the text to deliver.
PostProcess = Callable[[str, list], str]


def _noop(_status: str) -> None:
    pass


class Agent:
    def __init__(
        self,
        system_prompt: str,
        tools: list[Tool] | None = None,
        model: str = DEFAULT_MODEL,
        max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        postprocess: Optional[PostProcess] = None,
        client: Optional[anthropic.Anthropic] = None,
    ):
        self.system_prompt = system_prompt
        self.registry = ToolRegistry(tools)
        self.model = model
        self.max_tool_calls = max_tool_calls
        self.max_tokens = max_tokens
        self.postprocess = postprocess
        self._client = client

    @property
    def client(self) -> anthropic.Anthropic:
        # Lazily construct so importing the module never requires a key.
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def run(self, messages: list, progress_hook: ProgressHook | None = None) -> str:
        """Drive the tool-use loop until the model produces a final text answer
        (or the tool-call budget is exhausted). ``messages`` is mutated in place
        to include the full exchange, so callers can persist it afterward."""
        emit = progress_hook or _noop
        total_tool_calls = 0

        while True:
            at_limit = total_tool_calls >= self.max_tool_calls
            if at_limit:
                emit(f"Reached tool-call limit ({self.max_tool_calls}). Writing answer...")
            kwargs = {"tools": self.registry.schemas()} if not at_limit else {}
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=messages,
                **kwargs,
            )

            content_blocks = [b.model_dump() for b in resp.content]
            messages.append({"role": "assistant", "content": content_blocks})

            if resp.stop_reason != "tool_use":
                text = next((b["text"] for b in content_blocks if b.get("type") == "text"), "")
                return self.postprocess(text, messages) if self.postprocess else text

            # Surface any reasoning text the model emitted alongside its tool calls.
            for block in content_blocks:
                if block.get("type") == "text" and block.get("text", "").strip():
                    emit(block["text"].strip())

            tool_results = []
            for block in resp.content:
                if block.type != "tool_use":
                    continue
                total_tool_calls += 1
                emit(self._format_call(block.name, block.input))
                log.info("tool call %d: %s(%s)", total_tool_calls, block.name, block.input)

                result = self.registry.run(block.name, block.input)
                result_str = result if isinstance(result, str) else json.dumps(result)
                log.info("tool result len=%d", len(result_str))

                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result_str}
                )
            messages.append({"role": "user", "content": tool_results})

    @staticmethod
    def _format_call(name: str, tool_input: dict) -> str:
        """A compact, generic progress line for a tool call."""
        if not tool_input:
            return f"Running: {name}"
        args = ", ".join(f"{k}={v}" for k, v in tool_input.items())
        return f"Running: {name}({args})"
