# Contributing to octo-demo

Thanks for taking the time to contribute! This project values small, focused,
well-explained changes over large sweeping ones.

## Pull request expectations

A good pull request:

1. **Links an issue.** Reference the issue it addresses (e.g. `Fixes #123`).
   If no issue exists, open one first so the change can be discussed.
2. **Explains the motivation.** Describe *why* the change is needed and *what*
   it does. Avoid vague summaries like "improves the codebase".
3. **Stays focused.** One logical change per PR. Please do not mix unrelated
   refactors, formatting churn, and features in a single PR.
4. **Includes tests.** Any behavior change must add or update tests under
   `tests/`. Bug fixes should include a regression test.
5. **Passes CI.** Run `pytest` and the linter locally before submitting.

## What we will likely close

- Auto-generated or bulk PRs with no clear motivation.
- Large rewrites that touch many files without a linked, agreed-upon issue.
- Changes with no tests for behavior that clearly needs them.

## Reporting bugs

Please include: what you expected, what actually happened, a minimal snippet or
steps to reproduce, and your environment (OS, Python version, octo version).

## Good first issues

New contributors are very welcome. Look for issues labeled `good first issue`
and feel free to ask questions.
