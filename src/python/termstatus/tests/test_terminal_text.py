from termstatus.terminal_text import normalized_text


def test_normalized_text_non_string_returns_none() -> None:
    assert normalized_text(123) is None
    assert normalized_text(None) is None
    assert normalized_text(["hello"]) is None


def test_normalized_text_strips_control_characters_and_whitespace() -> None:
    assert normalized_text("  hello\x00world\x1b  ") == "helloworld"
    assert normalized_text("   ") is None
    assert normalized_text("\x00\x1b") is None
