"""Register the /research slash command. Run once (and after changing COMMAND).

Reads credentials from the environment; a ``.env`` file in the project root is
loaded automatically (same convention as ``db/init_db.py``):

    DISCORD_APPLICATION_ID=...
    DISCORD_BOT_TOKEN=...
    DISCORD_GUILD_ID=...        # optional; omit for global registration

    python -m examples.research_agent.register_command
"""
from dotenv import load_dotenv

from discord_agent.register import register

from .config import COMMAND

if __name__ == "__main__":
    load_dotenv()
    register(COMMAND)
