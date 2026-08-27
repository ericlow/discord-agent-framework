"""Register the /research slash command. Run once (and after changing COMMAND).

    export DISCORD_APPLICATION_ID=...
    export DISCORD_BOT_TOKEN=...
    export DISCORD_GUILD_ID=...        # optional; omit for global registration
    python -m examples.research_agent.register_command
"""
from discord_agent.register import register

from .config import COMMAND

if __name__ == "__main__":
    register(COMMAND)
