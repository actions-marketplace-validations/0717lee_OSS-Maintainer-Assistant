# Release v1.0.0 — maintainer-agent GitHub Action

## 🎉 First stable release

### What's included

- **Multi-agent triage**: Triage, Quality/AI-slop, Reproducer, Responder, Digest agents orchestrated via LangGraph
- **AI slop detection**: Weighted signals (AI phrases, missing linked issues, sweeping diffs, missing tests) with explainable scores
- **Bug reproduction**: Python snippets run in a locked-down Docker sandbox (`--network none --cap-drop ALL --read-only`)
- **Drafted replies**: Situation-aware reply templates, optionally rewritten by LLM
- **Maintainer digest**: 30-second summary posted to the Actions **Summary** tab
- **Two modes**: `digest` (snapshot) and `weekly` (last N days report)
- **Bilingual**: English and Chinese digest support
- **Optional LLM**: Plug in any litellm-compatible model (DeepSeek, OpenAI, Anthropic, etc.) for enhanced analysis
- **Tiered LLM strategy**: Per-agent model assignment; low-risk items skip LLM entirely
- **Read-only by design**: Never posts to your repo; all output goes to the job summary

### Usage

```yaml
- uses: 0717lee/OSS-Maintainer-Assistant@v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    # mode: weekly        # weekly report mode
    # days: 7             # look-back window (weekly only)
    # lang: zh            # Chinese digest
    # llm-model: deepseek/deepseek-v4-flash  # enable real LLM
    # llm-api-key: ${{ secrets.DEEPSEEK_API_KEY }}
```

### Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `repo` | `""` (current repo) | owner/name to analyze |
| `mode` | `digest` | `digest` or `weekly` |
| `limit` | `30` | Max items to analyze |
| `days` | `7` | Look-back days (weekly only) |
| `lang` | `en` | `en` or `zh` |
| `github-token` | `github.token` | Read token for GitHub API |
| `llm-model` | `""` | LLM model string (optional) |
| `llm-api-key` | `""` | LLM provider API key (optional) |

### Outputs

- `digest-path`: Path to the generated digest markdown file
- Job summary: Full digest posted to `$GITHUB_STEP_SUMMARY`
