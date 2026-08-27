"""fetch_url tool — retrieve readable text from a URL, with a Jina Reader fallback.

Tries a direct fetch + BeautifulSoup text extraction first; on 403, PDF content,
or a network error, falls back to the Jina Reader proxy (requires JINA_API_KEY).
"""
import json
import os

import requests
from bs4 import BeautifulSoup

from .. import http_utils
from ..tools import Tool

JINA_READER = "https://r.jina.ai/"

# Cap extracted text so a single page can't blow the model's context window.
MAX_CHARS = 50000


def fetch_url(url: str) -> str:
    """Fetch readable text from a URL. Falls back to Jina Reader on 403/PDF/network error."""
    text = _standard_fetch(url)
    if text is None:
        text = _jina_fetch(url)
    return text if text is not None else json.dumps({"error": f"could not fetch {url}"})


def _standard_fetch(url: str) -> str | None:
    try:
        resp = http_utils.get(url, timeout=30)
        if "pdf" in resp.headers.get("content-type", "").lower():
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:MAX_CHARS]
    except Exception:
        return None


def _jina_fetch(url: str) -> str | None:
    try:
        resp = requests.get(
            JINA_READER + url,
            headers={"Authorization": f"Bearer {os.environ['JINA_API_KEY']}"},
            timeout=30,
        )
        return resp.text[:MAX_CHARS] if resp.ok else None
    except Exception:
        return None


# Ready-to-register Tool wrapping the function above.
TOOL = Tool(
    name="fetch_url",
    description="Fetch the readable text of a web page for analysis.",
    handler=lambda inp: fetch_url(inp["url"]),
    input_schema={
        "type": "object",
        "properties": {"url": {"type": "string", "description": "The URL to fetch"}},
        "required": ["url"],
    },
)
