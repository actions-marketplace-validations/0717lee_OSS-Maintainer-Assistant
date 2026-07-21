# Promotion / Launch Kit

Ready-to-adapt copy for launching maintainer-agent to both English and Chinese
developer communities. Replace the demo/GIF links (and confirm the
`0717lee/OSS-Maintainer-Assistant` references) before posting.

## Positioning

- **EN one-liner:** A multi-agent, *explainable* assistant that helps open-source
  maintainers fight AI slop - triage, AI-slop detection, sandboxed reproduction,
  and reply drafts, with a human always in the loop.
- **ZH 一句话：** 帮开源维护者对抗 AI slop 的多 Agent 助手——分诊、AI-slop 识别、
  沙箱复现、回复草稿，人始终在关键环节把关。

## Pre-launch checklist

- [ ] Repo hygiene: README (EN + 中文), LICENSE, CONTRIBUTING, topics/tags, description.
- [ ] Live demo link (or `docker run` one-liner) + a short GIF/screenshot in the README.
- [ ] Publish the image to GHCR and tag `v1.0.0`; verify `uses: 0717lee/OSS-Maintainer-Assistant@v1`.
- [ ] Turn on the self-demo Action so the repo shows a real digest in its Actions tab.
- [ ] Prepare a pinned "author" first comment with context + FAQ.
- [ ] Line up 2-3 friends to give early, honest feedback (not upvote rings).

## Channels & timing

| Channel | Audience | Best time (roughly) | Notes |
|---|---|---|---|
| Hacker News (Show HN) | Global devs | Tue-Thu, ~08:00-10:00 ET | Title matters most; reply fast |
| Reddit r/opensource, r/programming | Global devs | Weekday mornings ET | Follow subreddit self-promo rules |
| Lobsters | Global devs | Weekdays | Needs invite; tag `ai`, `devtools` |
| X/Twitter | Global devs | Tue-Thu | Thread + demo GIF |
| 掘金 / SegmentFault | 中文开发者 | 工作日 10:00-12:00 | 长文 + 架构图 + 演示 |
| V2EX (`分享创造` 节点) | 中文开发者 | 工作日晚间 | 简洁真诚，避免硬广 |
| 微信公众号 / 即刻 | 中文开发者 | 晚间 | 讲"为什么做" |

## Show HN (title options)

1. `Show HN: maintainer-agent - an explainable multi-agent assistant vs AI slop`
2. `Show HN: I built a read-only agent that triages issues and flags AI-slop PRs`
3. `Show HN: Fighting AI slop in open source with explainable, human-gated agents`

### HN post body (EN)

> Maintainers are getting buried in low-effort, AI-generated PRs and issues, and
> most tooling is defensive (filters, caps, PR limits). I tried the opposite: a
> small team of **explainable, human-gated** agents that triage, score PRs for
> AI-slop against the repo's CONTRIBUTING.md, reproduce bugs in a sandbox, and
> draft replies - nothing is posted without approval.
>
> It runs fully offline (deterministic rule model + fixtures), so you can try the
> whole pipeline with zero credentials, and there's a GitHub Action that posts a
> read-only digest to your Actions summary. Every decision shows its evidence and
> a confidence score; there's a small labeled eval (precision/recall/F1) too.
>
> Demo: <link> · Repo: <link>. Feedback very welcome - especially on the slop
> signals and where they'd misfire.

## Reddit r/opensource (EN)

> **maintainer-agent: an explainable, read-only assistant for issue/PR triage and
> AI-slop detection**
>
> Short version: it triages issues/PRs, flags likely AI-generated slop with
> *explained* signals (checked against your CONTRIBUTING.md), reproduces bugs in a
> locked-down Docker sandbox, and drafts replies - all human-gated and read-only
> by default. Add it as a GitHub Action for a weekly digest, or run the dashboard
> locally. Fully offline demo, MIT licensed. Would love feedback on the heuristics.

## X/Twitter thread (EN)

1. Open source is drowning in AI slop. Maintainers are burning out. I built the
   opposite of a filter: maintainer-agent, an explainable multi-agent assistant. 🧵
2. It triages issues/PRs, scores AI-slop vs your CONTRIBUTING.md, reproduces bugs
   in a sandbox, and drafts replies. Every call shows its evidence + confidence.
3. Human-in-the-loop by design: read-only + dry-run by default; nothing is posted
   without per-action approval. Full audit log.
4. Runs fully offline (no keys). GitHub Action posts a read-only digest. MIT.
   Demo + repo: <link>

## 掘金 / SegmentFault 文章（ZH）

**标题选项：**
- 《开源维护者被 AI slop 淹没？我做了一个"可解释、人在回路"的多 Agent 助手》
- 《不止是过滤：用多 Agent 帮维护者分诊、识别 AI-slop、沙箱复现》

**开头：**
> 2025-2026，维护者被 LLM 生成的低质 PR/Issue 压垮，而现有工具大多在"过滤/限流"。
> 我尝试反过来做：一组**可解释、人类可控**的 Agent，负责分诊、以 CONTRIBUTING.md 为
> 标准给 PR 的 AI-slop 打分、在 Docker 沙箱里复现 bug、起草回复——默认只读、发帖需
> 逐条批准。完全离线可跑，附带 precision/recall 评估，并提供 GitHub Action 一键接入。

## V2EX（`分享创造`，ZH）

> **[分享创造] maintainer-agent：对抗 AI slop 的可解释多 Agent 维护助手**
>
> 分诊 + AI-slop 识别（对照仓库 CONTRIBUTING.md）+ 沙箱复现 + 回复草稿，默认只读、
> 人在回路。可离线体验，也能作为 GitHub Action 给自己仓库发只读摘要。MIT 开源，欢迎
> 拍砖，尤其是 slop 判定信号在哪些场景会误判。Demo：<链接> 仓库：<链接>

## 微信公众号（标题选项，ZH）

- 《AI slop 正在拖垮开源维护者，我用多 Agent 做了个"可解释"的解法》
- 《一个默认只读、人在回路的开源维护助手：它如何判定"AI 灌水 PR"》

## Keywords / hashtags

`open source`, `maintainer`, `AI slop`, `LLM`, `triage`, `LangGraph`, `agents`,
`devtools`, `#opensource`, `#AIagents`, `#devtools` · 中文：`开源` `维护者` `AI 灌水`
`多智能体` `LangGraph` `开发者工具`

## Launch-day tips

- Post once per channel; don't cross-post identical text within minutes.
- Be present for the first 2-3 hours to answer questions - engagement > upvotes.
- Lead with the problem (AI slop) and the demo; keep the pitch honest about limits
  (small eval set, Python-only reproduction, offline model is rule-based).
- Ask a concrete question ("where would the slop signals misfire?") to invite
  substantive replies.
