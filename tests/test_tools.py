"""Tests for the Tool abstraction and registry."""
import pytest

from discord_agent.tools import Tool, ToolRegistry


def _echo_tool(name="echo"):
    return Tool(
        name=name,
        description="echo the message",
        handler=lambda inp: f"you said: {inp['message']}",
        input_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    )


def test_schema_shape():
    reg = ToolRegistry([_echo_tool()])
    schemas = reg.schemas()
    assert schemas == [
        {
            "name": "echo",
            "description": "echo the message",
            "input_schema": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        }
    ]


def test_dispatch_runs_handler():
    reg = ToolRegistry([_echo_tool()])
    assert reg.run("echo", {"message": "hi"}) == "you said: hi"


def test_no_arg_tool_default_schema():
    reg = ToolRegistry([Tool(name="ping", description="ping", handler=lambda inp: "pong")])
    assert reg.schemas()[0]["input_schema"] == {"type": "object", "properties": {}, "required": []}
    assert reg.run("ping", {}) == "pong"


def test_duplicate_tool_name_rejected():
    reg = ToolRegistry([_echo_tool()])
    with pytest.raises(ValueError):
        reg.add(_echo_tool())


def test_unknown_tool_raises():
    reg = ToolRegistry([_echo_tool()])
    with pytest.raises(KeyError):
        reg.run("nope", {})
