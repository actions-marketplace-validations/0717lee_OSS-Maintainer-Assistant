# 发布操作指南

所有发布所需的文件已在 `deploy/` 目录准备好。以下是三个平台的完整操作步骤。

---

## 一、HuggingFace Space 在线 Demo

**目标**：公开可访问的在线 demo，推广时"点开就能试"。

**准备好的文件**：
- `deploy/huggingface-README.md` — Space 仓库的 README（含 frontmatter）
- `deploy/huggingface-.gitignore` — Space 仓库的 .gitignore
- `Dockerfile` — 多阶段构建（已改好）
- `action.yml` — GitHub Action 配置（已改好）

### 操作步骤

1. **创建 HuggingFace 账号**（如已有跳过）
   - 打开 https://huggingface.co/join
   - 注册并登录

2. **创建 Space**
   - 打开 https://huggingface.co/new-space
   - **Owner**: 你的用户名
   - **Space name**: `maintainer-agent`
   - **SDK**: 选择 `Docker`
   - **Visibility**: `Public`
   - 点击 **Create space**

3. **克隆 Space 仓库**
   ```bash
   git clone https://huggingface.co/spaces/你的用户名/maintainer-agent
   cd maintainer-agent
   ```

4. **复制项目文件**
   把以下文件/目录从项目根目录复制到 Space 仓库：
   ```
   Dockerfile
   pyproject.toml
   README.md
   maintainer_agent/       （整个目录）
   web/                    （整个目录，含 package.json 和 src/）
   docker/                 （整个目录，含 action-entrypoint.sh）
   ```
   然后把 `deploy/huggingface-README.md` 覆盖 Space 仓库的 `README.md`：
   ```bash
   cp deploy/huggingface-README.md README.md
   cp deploy/huggingface-.gitignore .gitignore
   ```

5. **提交并推送**
   ```bash
   git add -A
   git commit -m "Initial deployment"
   git push
   ```
   HuggingFace 会自动构建 Docker 镜像并部署。

6. **（可选）配置 Secrets**
   在 Space 的 **Settings → Variables and secrets** 添加：
   - `GITHUB_TOKEN` = 你的 GitHub Token（提高 API 限制）→ 设为 **Secret**
   - `MAINTAINER_AGENT_LLM_MODEL` = `deepseek/deepseek-v4-flash` → 设为 **Variable**
   - `DEEPSEEK_API_KEY` = 你的 DeepSeek key → 设为 **Secret**

7. **更新 GitHub README 的 demo 链接**
   打开项目 `README.md`，把 badge 链接里的 `0717lee` 改成你的 HuggingFace 用户名：
   ```
   [![Live Demo](...)](https://huggingface.co/spaces/你的用户名/maintainer-agent)
   ```

8. **等待构建完成**
   Space 页面会显示构建日志，通常 5-10 分钟。构建成功后访问：
   `https://你的用户名-maintainer-agent.hf.space`

---

## 二、GitHub Action 发布到 Marketplace

**目标**：用户在自己 repo 里 `uses: 0717lee/OSS-Maintainer-Assistant@v1` 就能用。

**准备好的文件**：
- `action.yml` — Action 定义（已打磨好）
- `docker/action-entrypoint.sh` — Action 入口脚本（已更新）
- `deploy/release-v1.0.0.md` — Release notes

### 操作步骤

1. **提交所有代码到 GitHub**
   ```bash
   cd /path/to/your/project
   git add -A
   git commit -m "feat: multi-agent dashboard, GitHub Action, weekly reports, webhook, memory, CI analysis"
   git push origin main
   ```

2. **打 v1 标签**
   ```bash
   git tag -a v1.0.0 -m "v1.0.0: First stable release"
   git push origin v1.0.0
   # GitHub Action 要求引用 tag，同时把 v1 指向最新
   git tag -f v1 v1.0.0
   git push origin v1 --force
   ```

3. **创建 GitHub Release**
   - 打开 https://github.com/0717lee/OSS-Maintainer-Assistant/releases/new
   - **Choose a tag**: `v1.0.0`
   - **Release title**: `v1.0.0 — First stable release`
   - **Description**: 复制 `deploy/release-v1.0.0.md` 的内容
   - 点击 **Publish release**

4. **发布到 GitHub Marketplace**
   - 打开 https://github.com/0717lee/OSS-Maintainer-Assistant
   - 在仓库页面右侧找到 **GitHub Marketplace** 或进入
     https://github.com/marketplace/publish-your-action
   - 选择你的仓库 `0717lee/OSS-Maintainer-Assistant`
   - 填写：
     - **Action name**: `maintainer-agent`
     - **Description**: `Multi-agent assistant for OSS maintainers: triage, AI-slop detection, bug reproduction, reply drafting.`
     - **Categories**: `Developer Tools`, `Code Quality`
     - **Pricing**: `Free`
   - 提交审核（GitHub 会检查 action.yml 是否符合规范，通常 1-2 天）

5. **验证**
   发布后在任意 repo 创建 workflow 测试：
   ```yaml
   # .github/workflows/test-maintainer-agent.yml
   name: test
   on: workflow_dispatch
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: 0717lee/OSS-Maintainer-Assistant@v1
           with:
             github-token: ${{ secrets.GITHUB_TOKEN }}
   ```

---

## 三、GitHub Token 配置

**目标**：避免 GitHub API 限流（60→5000 次/小时），并启用审批发布功能。

**准备好的文件**：
- `deploy/GITHUB-TOKEN.md` — 详细配置指南

### 操作步骤

1. **生成 Fine-grained Token**
   - 打开 https://github.com/settings/tokens?type=beta
   - **Generate new token**
   - **Token name**: `maintainer-agent`
   - **Expiration**: 90 days
   - **Repository access**: `Public Repositories (read-only)`（只读分析）或指定仓库（如需写操作）
   - **Permissions**:
     - 只读分析: `Issues: Read`, `Pull requests: Read`, `Metadata: Read`
     - 审批发布: `Issues: Write`, `Pull requests: Write`
   - 生成并复制

2. **填入 .env**
   打开项目根目录的 `.env`：
   ```
   GITHUB_TOKEN=github_pat_xxx你的token
   ```

3. **重启后端验证**
   ```bash
   cd /path/to/your/project
   python -c "from dotenv import load_dotenv; load_dotenv(); from maintainer_agent.api.server import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
   ```
   访问 `http://localhost:8000/api/health` 确认正常，输入 `pallets/flask` 分析不再限流。

---

## 文件清单

所有准备好的文件都在 `deploy/` 目录：

| 文件 | 用途 |
|------|------|
| `deploy/huggingface-README.md` | HF Space 的 README frontmatter |
| `deploy/huggingface-.gitignore` | HF Space 的 .gitignore |
| `deploy/HUGGINGFACE.md` | HF 部署文档（已更新） |
| `deploy/release-v1.0.0.md` | GitHub Release notes |
| `deploy/GITHUB-TOKEN.md` | Token 配置指南 |
| `action.yml` | GitHub Action 定义 |
| `docker/action-entrypoint.sh` | Action 入口脚本 |
| `Dockerfile` | 多阶段 Docker 构建 |

---

## 推荐执行顺序

1. **先配 Token**（解决限流，本地测试顺畅）
2. **提交代码到 GitHub**（打 tag，创建 release）
3. **发布 GitHub Action**（Marketplace 审核期间可以并行做 HF）
4. **部署 HuggingFace Space**（推代码，配置 secrets）
5. **更新 README 链接**（把 badge 里的用户名改成你的）
6. **推广**：发推文/HN 帖子，附 HF demo 链接 + Action 安装链接
