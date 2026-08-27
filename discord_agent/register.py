"""Register a slash command with Discord.

Run once, and again whenever the command definition changes. Guild registration
is instant; global registration takes up to ~1 hour to propagate.

Usage::

    export DISCORD_APPLICATION_ID=...   # from the Developer Portal
    export DISCORD_BOT_TOKEN=...        # from Developer Portal > Bot
    export DISCORD_GUILD_ID=...         # optional; right-click server > Copy Server ID

    from discord_agent.register import register
    register({"name": "ask", "description": "...", "options": [...]})
"""
import os

import requests

# Discord application command option types
STRING_OPTION = 3


def register(command: dict) -> dict:
    """Register ``command`` with Discord and return the API response JSON.

    If ``DISCORD_GUILD_ID`` is set, registers to that guild (instant); otherwise
    registers globally (~1h to propagate).
    """
    app_id = os.environ["DISCORD_APPLICATION_ID"]
    token = os.environ["DISCORD_BOT_TOKEN"]
    guild_id = os.environ.get("DISCORD_GUILD_ID")

    if guild_id:
        url = f"https://discord.com/api/v10/applications/{app_id}/guilds/{guild_id}/commands"
        scope = f"guild {guild_id}"
    else:
        url = f"https://discord.com/api/v10/applications/{app_id}/commands"
        scope = "global (~1h to propagate)"

    resp = requests.post(url, headers={"Authorization": f"Bot {token}"}, json=command, timeout=10)
    resp.raise_for_status()
    print(f"Registered /{command['name']} to {scope}: {resp.status_code}")
    return resp.json()
