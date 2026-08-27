"""Built-in, ready-to-register tools.

Each module exposes a ``TOOL`` (a ``discord_agent.Tool``) and the underlying
function. Both built-ins here use the Jina API and require ``JINA_API_KEY``.
"""
from .fetch_url import TOOL as fetch_url_tool
from .fetch_url import fetch_url
from .search_web import TOOL as search_web_tool
from .search_web import search_web

__all__ = ["fetch_url", "fetch_url_tool", "search_web", "search_web_tool"]
