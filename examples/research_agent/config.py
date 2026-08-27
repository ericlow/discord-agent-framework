"""Configuration for the research agent example.

This is where all the agent-specific choices live: the system prompt, the model,
the tools, and the slash-command definition. Swap these out to build a different
agent on the same framework.
"""
from discord_agent import Agent
from discord_agent.builtins import fetch_url_tool, search_web_tool
from discord_agent.register import STRING_OPTION

SYSTEM_PROMPT = """You are a diligent web research assistant. Given a question or a \
URL, investigate it and answer clearly and concisely.

Use search_web to find relevant sources and fetch_url to read them. Read at least \
two sources before drawing a conclusion. Prefer primary sources over summaries.

Write a direct answer first, then a few short supporting points. Cite the URLs you \
relied on at the end under a "Sources" line. Keep the whole reply under 300 words."""


def build_agent() -> Agent:
    """Construct the research Agent with its tools."""
    return Agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[search_web_tool, fetch_url_tool],
    )


# Slash-command definition, passed to discord_agent.register.register().
COMMAND = {
    "name": "research",
    "description": "Research a question or URL and get a sourced answer",
    "options": [
        {
            "type": STRING_OPTION,
            "name": "input",
            "description": "Your question or URL — or a conversation ID + follow-up",
            "required": True,
        }
    ],
}
