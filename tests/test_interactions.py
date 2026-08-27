"""Tests for the Discord interactions handler built by make_handler."""
import json

from nacl.signing import SigningKey

from discord_agent import interactions


def _dummy_engine(event, context):
    return {"engine": True}


def _event(body: str, signing_key: SigningKey, timestamp: str = "1700000000"):
    signature = signing_key.sign(f"{timestamp}{body}".encode()).signature.hex()
    return {
        "headers": {
            "x-signature-ed25519": signature,
            "x-signature-timestamp": timestamp,
        },
        "body": body,
        "isBase64Encoded": False,
    }


def _public_key_hex(signing_key: SigningKey) -> str:
    return signing_key.verify_key.encode().hex()


def _command_event(input_text: str, signing_key: SigningKey):
    body = json.dumps({
        "type": interactions.APPLICATION_COMMAND,
        "token": "test-token",
        "data": {"options": [{"name": "input", "value": input_text}]},
    })
    return _event(body, signing_key)


# --- signature verification ---

def test_tampered_body_is_rejected(monkeypatch):
    sk = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", _public_key_hex(sk))
    handler = interactions.make_handler(_dummy_engine)
    event = _event(json.dumps({"type": interactions.PING}), sk)
    event["body"] = json.dumps({"type": interactions.APPLICATION_COMMAND})

    assert handler(event, None)["statusCode"] == 401


def test_wrong_key_is_rejected(monkeypatch):
    sk = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", _public_key_hex(SigningKey.generate()))
    handler = interactions.make_handler(_dummy_engine)

    assert handler(_event(json.dumps({"type": interactions.PING}), sk), None)["statusCode"] == 401


# --- ping ---

def test_ping_returns_pong(monkeypatch):
    sk = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", _public_key_hex(sk))
    handler = interactions.make_handler(_dummy_engine)

    resp = handler(_event(json.dumps({"type": interactions.PING}), sk), None)

    assert resp["statusCode"] == 200
    assert json.loads(resp["body"]) == {"type": interactions.PONG}


# --- engine mode delegation ---

def test_engine_mode_delegates():
    handler = interactions.make_handler(_dummy_engine)
    assert handler({"mode": "engine"}, None) == {"engine": True}


# --- slash command routing ---

def test_command_returns_deferred(monkeypatch):
    sk = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", _public_key_hex(sk))
    monkeypatch.setattr(interactions, "_defer_interaction", lambda i, t: None)
    monkeypatch.setattr(interactions, "_invoke_engine", lambda p: None)
    handler = interactions.make_handler(_dummy_engine)

    assert handler(_command_event("what is the capital of France?", sk), None)["statusCode"] == 200


def test_new_conversation_routing(monkeypatch):
    sk = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", _public_key_hex(sk))
    captured = {}
    monkeypatch.setattr(interactions, "_defer_interaction", lambda i, t: None)
    monkeypatch.setattr(interactions, "_invoke_engine", lambda p: captured.update(p))
    handler = interactions.make_handler(_dummy_engine)

    handler(_command_event("https://example.com summarize this", sk), None)

    assert "conversation_id" not in captured
    assert captured["input_text"] == "https://example.com summarize this"
    assert captured["mode"] == "engine"
    assert captured["interaction_token"] == "test-token"


def test_continuation_routing(monkeypatch):
    sk = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", _public_key_hex(sk))
    captured = {}
    monkeypatch.setattr(interactions, "_defer_interaction", lambda i, t: None)
    monkeypatch.setattr(interactions, "_invoke_engine", lambda p: captured.update(p))
    handler = interactions.make_handler(_dummy_engine)

    handler(_command_event("42 what about the follow-up?", sk), None)

    assert captured["conversation_id"] == 42
    assert captured["input_text"] == "what about the follow-up?"
    assert captured["mode"] == "engine"
