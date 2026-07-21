export const I18N = {
  en: {
    tagline:
      "Triage issues and pull requests, flag low-effort AI submissions, and draft replies — you stay in control of what gets posted.",
    placeholder: "owner/name — enter any public GitHub repo",
    analyze: "Analyze",
    hint: "No token required. Works on any public repository.",
    listTitle: "Issues & pull requests",
    digestTitle: "Maintainer digest",
    footer: "Read-only by design — you approve every action before it touches GitHub.",
    source: "source",
    loading: "Analyzing repository…",
    conf: "confidence",
    draft: "Draft reply",
    proposed: "Proposed actions (awaiting your approval): ",
    st: {
      source: "source",
      backend: "backend",
      llm: "model",
      run: "run",
      items: "items",
      sample: "fixture",
    },
    stat: {
      reviewed: "reviewed",
      attention: "needs attention",
      duplicates: "duplicates",
      ready: "ready to review",
      good_first: "good first issue",
      more_info: "needs info",
    },
    errPre: "Failed to load: ",
    errSuf: ". Verify the repository name and try again.",
    empty: "Ready when you are",
    emptyHint:
      "Enter a repository in the format owner/name above — for example, pallets/flask — then click Analyze.",
    retry: "Try again",
  },
  zh: {
    tagline:
      "自动分诊 issue 与 PR，识别低质 AI 灌水提交，并起草回复——所有发布操作均由你掌控。",
    placeholder: "owner/name — 输入任意公开 GitHub 仓库",
    analyze: "分析",
    hint: "无需 token，支持任意公开仓库。",
    listTitle: "Issues 与 Pull Requests",
    digestTitle: "维护者摘要",
    footer: "只读设计——每一步操作都经你审批后才会执行。",
    source: "源码",
    loading: "正在分析仓库…",
    conf: "置信度",
    draft: "回复草稿",
    proposed: "建议动作（待你批准）：",
    st: {
      source: "来源",
      backend: "后端",
      llm: "模型",
      run: "运行",
      items: "条",
      sample: "示例",
    },
    stat: {
      reviewed: "已审阅",
      attention: "需关注",
      duplicates: "疑似重复",
      ready: "待评审",
      good_first: "适合新手",
      more_info: "信息不足",
    },
    errPre: "加载失败：",
    errSuf: "。请确认仓库名称后重试。",
    empty: "准备就绪",
    emptyHint:
      "在上方输入 owner/name 格式的仓库名称——例如 pallets/flask——然后点击「分析」。",
    retry: "重试",
  },
};

export const VMAP_ZH = {
  "likely-ai-slop": "疑似 AI 灌水",
  "needs-work": "待完善",
  "looks-good": "质量良好",
  duplicate: "疑似重复",
  security: "安全问题",
  bug: "缺陷",
  "needs-more-info": "信息不足",
  documentation: "文档",
  enhancement: "功能增强",
  question: "提问",
  reproduced: "已复现",
  "not-reproduced": "未复现",
  "reply-drafted": "已拟回复",
  "not-applicable": "不适用",
  "needs-triage": "待分诊",
  "good first issue": "适合新手",
};

export const PRI_ZH = { high: "高", medium: "中", low: "低", "-": "—" };

export const AGENT_ZH = {
  triage: "分诊",
  quality: "质量",
  reproducer: "复现",
  responder: "回复",
};

export const TONE = {
  "likely-ai-slop": "danger",
  security: "danger",
  bug: "danger",
  reproduced: "danger",
  "needs-work": "warning",
  "needs-more-info": "warning",
  "looks-good": "success",
  "not-reproduced": "success",
  "good first issue": "success",
  duplicate: "info",
  documentation: "info",
  enhancement: "info",
  question: "info",
  "reply-drafted": "neutral",
  "not-applicable": "neutral",
  "needs-triage": "neutral",
};

export const tone = (v) => TONE[v] || "neutral";
export const tV = (lang, v) => (lang === "zh" ? VMAP_ZH[v] || v : v);
export const tPri = (lang, p) => (lang === "zh" ? PRI_ZH[p] || p : p);
export const tAgent = (lang, a) => (lang === "zh" ? AGENT_ZH[a] || a : a);
