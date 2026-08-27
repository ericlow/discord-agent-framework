"""Discord I/O — send responses back to Discord over HTTP.

Covers the three things an interactions-based agent needs: posting messages to a
channel with the bot token, editing/deleting the deferred interaction reply, and
splitting long output into Discord's 2000-character limit.
"""
import logging
import os

import requests

log = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"

# SUPPRESS_EMBEDS keeps link previews out of streamed status messages.
SUPPRESS_EMBEDS = 4


def parse_event(event: dict) -> tuple[str, str, int | None, str]:
    """Extract the fields the engine needs from the async invocation payload."""
    return (
        event["interaction_token"],
        event["input_text"],
        event.get("conversation_id"),
        event.get("channel_id", ""),
    )


def post_channel_message(channel_id: str, text: str):
    """Post a message directly to a channel using the bot token."""
    try:
        requests.post(
            f"{DISCORD_API}/channels/{channel_id}/messages",
            headers={"Authorization": f"Bot {os.environ['DISCORD_BOT_TOKEN']}"},
            json={"content": text, "flags": SUPPRESS_EMBEDS},
            timeout=10,
        )
    except Exception:
        log.exception("Failed to post channel message")


def delete_original(token: str):
    """Delete the deferred @original placeholder message."""
    app_id = os.environ["DISCORD_APPLICATION_ID"]
    try:
        requests.delete(
            f"{DISCORD_API}/webhooks/{app_id}/{token}/messages/@original",
            timeout=10,
        )
    except Exception:
        log.exception("Failed to delete original message")


def send_response(token: str, content: str):
    """Send content back to Discord, patching the deferred reply and posting overflow chunks."""
    app_id = os.environ["DISCORD_APPLICATION_ID"]
    chunks = split(content)
    base = f"{DISCORD_API}/webhooks/{app_id}/{token}"
    try:
        requests.patch(f"{base}/messages/@original", json={"content": chunks[0], "flags": SUPPRESS_EMBEDS}, timeout=10)
        for chunk in chunks[1:]:
            requests.post(base, json={"content": chunk, "flags": SUPPRESS_EMBEDS}, timeout=10)
    except Exception:
        log.exception("Failed to send Discord response")


def split(text: str, limit: int = 2000) -> list[str]:
    """Split a long string into Discord-safe chunks (max 2000 chars each)."""
    if len(text) <= limit:
        return [text]
    return [text[i : i + limit] for i in range(0, len(text), limit)]
