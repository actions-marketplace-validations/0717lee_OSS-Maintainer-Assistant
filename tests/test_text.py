from maintainer_agent.core.text import (
    extract_code_blocks,
    extract_linked_issues,
)


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
