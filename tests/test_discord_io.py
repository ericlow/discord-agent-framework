"""Tests for Discord I/O helpers."""
from discord_agent.discord_io import split


def test_short_text_single_chunk():
    assert split("hello") == ["hello"]


def test_exact_limit_single_chunk():
    text = "a" * 2000
    assert split(text) == [text]


def test_long_text_splits_into_2000_char_chunks():
    text = "a" * 4500
    chunks = split(text)
    assert len(chunks) == 3
    assert [len(c) for c in chunks] == [2000, 2000, 500]
    assert "".join(chunks) == text


def test_custom_limit():
    assert split("abcdef", limit=2) == ["ab", "cd", "ef"]
