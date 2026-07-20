#!/usr/bin/env bash
# Entry point for the maintainer-agent GitHub Action.
# Read-only: it analyzes issues/PRs and writes a digest to the job summary.
# It never posts to the repository.
set -uo pipefail

REPO="${INPUT_REPO:-${GITHUB_REPOSITORY:-}}"
LIMIT="${INPUT_LIMIT:-30}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/stdout}"

echo "maintainer-agent: analyzing ${REPO} (limit ${LIMIT})"

if [ -z "${REPO}" ]; then
  echo "No repository specified (set the 'repo' input)." | tee -a "${SUMMARY}"
  exit 0
fi

if maintainer-agent digest --repo "${REPO}" --limit "${LIMIT}" --out /tmp/digest.md; then
  cat /tmp/digest.md >> "${SUMMARY}"
  # Also emit the full machine-readable results for downstream steps/artifacts.
  maintainer-agent run --repo "${REPO}" --limit "${LIMIT}" --json /tmp/results.json >/dev/null 2>&1 || true
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "digest-path=/tmp/digest.md" >> "${GITHUB_OUTPUT}"
  fi
else
  {
    echo "## maintainer-agent"
    echo ""
    echo "Analysis did not complete - this is usually GitHub API rate limiting on"
    echo "unauthenticated runs. Make sure \`github-token\` is provided."
  } >> "${SUMMARY}"
fi
