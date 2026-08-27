"""Tests for the Agent tool-use loop, using a fake Anthropic client."""
from discord_agent import Agent, Tool


class FakeBlock:
    """Mimics an Anthropic content block (has attributes + model_dump)."""

    def __init__(self, **kw):
        self.__dict__.update(kw)
        self._data = dict(kw)

    def model_dump(self):
        return dict(self._data)


class FakeResponse:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


def _tool(calls):
    def handler(inp):
        calls.append(inp)
        return "sunny, 21C"
    return Tool(
        name="get_weather",
        description="weather",
        handler=handler,
        input_schema={"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    )


def test_loop_dispatches_tool_then_returns_final_text():
    tool_calls = []
    responses = [
        FakeResponse(
            [FakeBlock(type="tool_use", id="t1", name="get_weather", input={"city": "Paris"})],
            stop_reason="tool_use",
        ),
        FakeResponse([FakeBlock(type="text", text="It is sunny in Paris.")], stop_reason="end_turn"),
    ]
    client = FakeClient(responses)
    agent = Agent(system_prompt="test", tools=[_tool(tool_calls)], client=client)

    messages = [{"role": "user", "content": "weather in Paris?"}]
    result = agent.run(messages)

    assert result == "It is sunny in Paris."
    assert tool_calls == [{"city": "Paris"}]
    # user msg, assistant tool_use, user tool_result, assistant final text
    assert len(messages) == 4
    assert messages[2]["content"][0]["type"] == "tool_result"
    # tools passed on the first call, then again (still under limit) on the second
    assert "tools" in client.messages.calls[0]


def test_progress_hook_receives_status():
    responses = [
        FakeResponse(
            [FakeBlock(type="tool_use", id="t1", name="get_weather", input={"city": "Paris"})],
            stop_reason="tool_use",
        ),
        FakeResponse([FakeBlock(type="text", text="done")], stop_reason="end_turn"),
    ]
    agent = Agent(system_prompt="t", tools=[_tool([])], client=FakeClient(responses))
    seen = []
    agent.run([{"role": "user", "content": "x"}], progress_hook=seen.append)

    assert any("get_weather" in s for s in seen)


def test_tool_limit_drops_tools():
    # max_tool_calls=0 => first call already at limit, no tools sent, must answer.
    responses = [FakeResponse([FakeBlock(type="text", text="no tools used")], stop_reason="end_turn")]
    client = FakeClient(responses)
    agent = Agent(system_prompt="t", tools=[_tool([])], max_tool_calls=0, client=client)

    result = agent.run([{"role": "user", "content": "x"}])

    assert result == "no tools used"
    assert "tools" not in client.messages.calls[0]


def test_postprocess_applied():
    responses = [FakeResponse([FakeBlock(type="text", text="answer")], stop_reason="end_turn")]
    agent = Agent(
        system_prompt="t",
        client=FakeClient(responses),
        postprocess=lambda text, msgs: text.upper(),
    )
    assert agent.run([{"role": "user", "content": "x"}]) == "ANSWER"
