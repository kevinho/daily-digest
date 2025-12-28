from src.llm import generate_digest


def test_generate_digest_placeholder():
    result = generate_digest("hello world")
    assert "tldr" in result
