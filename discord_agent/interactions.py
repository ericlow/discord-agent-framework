"""Discord interactions entrypoint (the front half of the Lambda pattern).

Discord requires a response to an interaction within 3 seconds, but an agent
run takes much longer. This module implements the standard split: verify the
Ed25519 signature, answer the verification PING, and for slash commands send a
*deferred* response (type 5) immediately, then asynchronously invoke a second
Lambda ("engine mode") to do the real work and post results back later.

A single Lambda function serves both roles: when invoked with
``{"mode": "engine", ...}`` it delegates to the engine handler you supply,
avoiding a second function and its infrastructure.

Wire it up with ``make_handler``::

    from discord_agent import interactions
    from myagent.engine import handler as engine_handler

    handler = interactions.make_handler(engine_handler)
"""
import base64
import json
import logging
import os
from typing import Callable

import requests
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

log = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"

# Discord interaction + response type codes
PING = 1
APPLICATION_COMMAND = 2
PONG = 1
DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5


def verify_signature(public_key: str, signature: str, timestamp: str, body: str) -> bool:
    """Return True if the Ed25519 signature matches the raw request body."""
    try:
        VerifyKey(bytes.fromhex(public_key)).verify(
            f"{timestamp}{body}".encode(), bytes.fromhex(signature)
        )
        return True
    except (BadSignatureError, ValueError):
        return False


def _raw_body(event: dict) -> str:
    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode()
    return body


def _response(status: int, payload: dict | None = None) -> dict:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload) if payload is not None else "",
    }


def _defer_interaction(interaction_id: str, token: str):
    """Send a type 5 deferred response directly to Discord, keeping the handler alive."""
    requests.post(
        f"{DISCORD_API}/interactions/{interaction_id}/{token}/callback",
        json={"type": DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE},
        timeout=5,
    )


def _invoke_engine(payload: dict):
    """Invoke this same Lambda in engine mode, asynchronously (fire-and-forget)."""
    import boto3  # provided by the Lambda runtime; not a local dependency

    region = os.environ.get("AWS_REGION", "us-east-1")
    fn = os.environ["AWS_LAMBDA_FUNCTION_NAME"]
    boto3.client("lambda", region_name=region).invoke(
        FunctionName=fn,
        InvocationType="Event",
        Payload=json.dumps(payload).encode(),
    )


def make_handler(engine_handler: Callable, command_option: str = "input") -> Callable:
    """Build a Lambda handler for the interactions endpoint.

    ``engine_handler(event, context)`` is your agent's engine-mode entry point;
    it is called when the Lambda is self-invoked with ``mode == "engine"``.
    ``command_option`` is the name of the slash-command string option to read.

    A leading integer in the option value is treated as a conversation ID for a
    follow-up turn; the rest of the value is the new input.
    """

    def handler(event, context):
        if event.get("mode") == "engine":
            log.info("engine mode -> delegating")
            return engine_handler(event, context)

        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        signature = headers.get("x-signature-ed25519", "")
        timestamp = headers.get("x-signature-timestamp", "")
        body = _raw_body(event)

        if not verify_signature(os.environ["DISCORD_PUBLIC_KEY"], signature, timestamp, body):
            log.warning("invalid signature")
            return _response(401, {"error": "invalid request signature"})

        interaction = json.loads(body)

        if interaction.get("type") == PING:
            return _response(200, {"type": PONG})

        if interaction.get("type") == APPLICATION_COMMAND:
            options = (interaction.get("data") or {}).get("options") or []
            input_text = next((o["value"] for o in options if o["name"] == command_option), "")
            token = interaction.get("token", "")
            interaction_id = interaction.get("id", "")
            channel_id = interaction.get("channel_id", "")

            payload = {
                "mode": "engine",
                "interaction_token": token,
                "channel_id": channel_id,
                "input_text": input_text,
            }
            parts = input_text.split()
            if parts and parts[0].isdigit():
                payload["conversation_id"] = int(parts[0])
                payload["input_text"] = " ".join(parts[1:])

            log.info("command: input=%r", input_text[:80])
            _defer_interaction(interaction_id, token)
            _invoke_engine(payload)
            log.info("deferred + engine invoked async")
            return _response(200, {})

        return _response(200, {"type": PONG})

    return handler
