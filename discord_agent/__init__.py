"""discord_agent — a framework for building Discord AI agents on Claude's tool-use loop."""
from .agent import Agent
from .tools import Tool, ToolRegistry

__all__ = ["Agent", "Tool", "ToolRegistry"]
__version__ = "0.1.0"
