"""Lambda entry point for the research agent.

One Lambda function, two roles (see discord_agent.interactions):

* Front half — verifies the Discord signature, defers, and self-invokes in
  engine mode. Provided by ``interactions.make_handler``.
* Engine half — ``engine_handler`` below: loads/creates the conversation, runs
  the Agent, streams progress to the channel, and posts the final answer.
"""
import logging

from discord_agent import interactions, persistence
from discord_agent.discord_io import (
    delete_original,
    parse_event,
    post_channel_message,
    send_response,
    split,
)

from .config import build_agent

log = logging.getLogger()
log.setLevel(logging.INFO)

agent = build_agent()


def engine_handler(event, context):
    """Engine mode: run the agent and deliver the result to Discord."""
    token, input_text, conversation_id, channel_id = parse_event(event)

    db = None
    try:
        db = persistence.conn()
        if conversation_id is not None:
            messages = persistence.load_conversation(db, conversation_id)
            if messages is None:
                send_response(token, f"No conversation found with ID {conversation_id}")
                return
            messages.append({"role": "user", "content": input_text})
        else:
            messages = [{"role": "user", "content": input_text}]
            conversation_id = persistence.create_conversation(db, messages)

        log.info("start: cid=%s input=%r", conversation_id, input_text[:80])
        post_channel_message(channel_id, f"**Researching:** {input_text}")

        answer = agent.run(messages, progress_hook=lambda s: post_channel_message(channel_id, s))
        log.info("answer complete len=%d", len(answer))

        persistence.update_conversation(db, conversation_id, messages)
        delete_original(token)
        for chunk in split(f"{answer}\n\nConversation ID: {conversation_id}"):
            post_channel_message(channel_id, chunk)
    except Exception as e:
        log.exception("Engine failed: %s", e)
        send_response(token, f"Research failed: {e}")
    finally:
        if db:
            db.close()


# The Lambda handler Discord calls. Engine-mode self-invocations are delegated
# to engine_handler by make_handler.
handler = interactions.make_handler(engine_handler)
