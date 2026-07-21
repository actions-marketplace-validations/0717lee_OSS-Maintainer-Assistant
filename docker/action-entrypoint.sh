#!/usr/bin/env bash
# Entry point for the maintainer-agent GitHub Action.
# Read-only: it analyzes issues/PRs and writes a digest to the job summary.
# It never posts to the repository.
set -uo pipefail

REPO="${INPUT_REPO:-${GITHUB_REPOSITORY:-}}"
MODE="${INPUT_MODE:-digest}"
LIMIT="${INPUT_LIMIT:-30}"
DAYS="${INPUT_DAYS:-7}"
LANG="${INPUT_LANG:-en}"
SUMMARY="${GITHUB_STEP_SUMMARY:-/dev/stdout}"

# Map the generic LLM_API_KEY to the correct provider env var based on model prefix.
if [ -n "${MAINTAINER_AGENT_LLM_MODEL:-}" ] && [ -n "${LLM_API_KEY:-}" ]; then
  case "${MAINTAINER_AGENT_LLM_MODEL}" in
    deepseek/*) export DEEPSEEK_API_KEY="${LLM_API_KEY}" ;;
    gpt-*|openai/*) export OPENAI_API_KEY="${LLM_API_KEY}" ;;
    claude-*|anthropic/*) export ANTHROPIC_API_KEY="${LLM_API_KEY}" ;;
    gemini-*|google/*) export GEMINI_API_KEY="${LLM_API_KEY}" ;;
  esac
fi

echo "maintainer-agent: ${MODE} for ${REPO} (limit ${LIMIT}, lang ${LANG}$([ "$MODE" = "weekly" ] && echo ", days ${DAYS}"))"

if [ -z "${REPO}" ]; then
  echo "No repository specified (set the 'repo' input)." | tee -a "${SUMMARY}"
  exit 0
fi

if [ "$MODE" = "weekly" ]; then
  CMD="maintainer-agent weekly --repo ${REPO} --limit ${LIMIT} --days ${DAYS} --lang ${LANG} --out /tmp/digest.md"
else
  CMD="maintainer-agent digest --repo ${REPO} --limit ${LIMIT} --lang ${LANG} --out /tmp/digest.md"
fi

if eval "${CMD}"; then
  cat /tmp/digest.md >> "${SUMMARY}"
  # Also emit the full machine-readable results for downstream steps/artifacts.
  maintainer-agent run --repo "${REPO}" --limit "${LIMIT}" --lang "${LANG}" --json /tmp/results.json >/dev/null 2>&1 || true
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
