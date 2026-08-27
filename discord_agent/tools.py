"""Tool abstraction and registry.

A ``Tool`` bundles the Anthropic tool schema together with the Python callable
that runs it, so the two never drift apart. A ``ToolRegistry`` builds both the
``tools=[...]`` array passed to the Anthropic API and the name->handler dispatch
map from the same set of ``Tool`` objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Union

# A handler takes the tool's decoded input dict and returns either a string
# (sent straight back to the model) or a JSON-serializable object.
ToolResult = Union[str, dict, list]
ToolHandler = Callable[[dict], ToolResult]


@dataclass
class Tool:
    """A single tool: its schema plus the callable that executes it."""

    name: str
    description: str
    handler: ToolHandler
    # JSON schema for the tool input. Defaults to an empty object (no args).
    input_schema: dict = field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []}
    )

    def schema(self) -> dict:
        """Return the Anthropic tool definition for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }

    def run(self, tool_input: dict) -> ToolResult:
        return self.handler(tool_input or {})


class ToolRegistry:
    """A collection of tools, indexed by name."""

    def __init__(self, tools: list[Tool] | None = None):
        self._tools: dict[str, Tool] = {}
        for tool in tools or []:
            self.add(tool)

    def add(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool name: {tool.name}")
        self._tools[tool.name] = tool

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def schemas(self) -> list[dict]:
        """The ``tools=[...]`` array for the Anthropic API."""
        return [t.schema() for t in self._tools.values()]

    def run(self, name: str, tool_input: dict) -> ToolResult:
        """Dispatch a tool call by name."""
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name].run(tool_input)
