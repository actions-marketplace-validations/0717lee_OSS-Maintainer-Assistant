# Contributing

Thanks for helping improve maintainer-agent! We value small, focused,
well-explained changes - the same bar the tool applies to others.

## A good pull request

1. **Links an issue** it addresses (`Fixes #123`). Open one first for larger changes.
2. **Explains the motivation** - what and why, not just "improves things".
3. **Stays focused** - one logical change per PR; avoid mixing refactors and features.
4. **Includes tests** for behavior changes (`pytest` under `tests/`).
5. **Passes CI** - run `pytest` locally; `ruff check .` for style.

## Dev setup

```bash
pip install -e ".[dev]"     # core + pytest + ruff
pip install -e ".[all]"     # optional: langgraph, litellm, faiss
pytest -q
```

## Good first issues

New contributors are very welcome - look for issues labeled `good first issue`,
and feel free to ask questions. Running `maintainer-agent run --fixtures` is the
fastest way to see the whole pipeline end to end.

By contributing, you agree your work is licensed under the project's MIT license.
