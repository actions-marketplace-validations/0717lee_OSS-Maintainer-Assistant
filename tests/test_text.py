from maintainer_agent.core.text import (
    cosine,
    extract_code_blocks,
    extract_linked_issues,
)


def test_cosine_similar_vs_different():
    a = "division by zero crash when averaging three numbers"
    b = "crash: zero division error averaging three values"
    c = "add a dark mode toggle to the settings page"
    assert cosine(a, b) > cosine(a, c)
    assert 0.0 <= cosine(a, c) <= 1.0


def test_extract_linked_issues():
    assert extract_linked_issues("Fixes #101") == [101]
    assert extract_linked_issues("closes #5 and resolves #9") == [5, 9]
    assert extract_linked_issues("no refs here") == []


def test_extract_code_blocks_only_python():
    body = (
        "text\n```python\nprint(1)\n```\nmore\n```\ntraceback text\n```\n"
    )
    blocks = extract_code_blocks(body, lang="python")
    assert len(blocks) == 1
    assert "print(1)" in blocks[0]
    # The unlabeled traceback fence is intentionally excluded.
    assert "traceback text" not in blocks[0]
