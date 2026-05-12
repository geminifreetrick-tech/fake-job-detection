from app.pipeline import text_clean


def test_clean_strips_html_and_normalizes_whitespace():
    raw = "<p>Hello&nbsp;<b>World</b>\n\n\nFoo</p>"
    out = text_clean.clean(raw)
    assert "Hello" in out
    assert "World" in out
    assert "Foo" in out
    assert "<" not in out and ">" not in out
    assert "  " not in out


def test_clean_handles_empty():
    assert text_clean.clean("") == ""
    assert text_clean.clean(None) == ""  # type: ignore[arg-type]


def test_word_tokens_basic():
    toks = text_clean.word_tokens("Hello, World! 123 foo-bar")
    assert toks[:3] == ["Hello", "World", "foo-bar"]
