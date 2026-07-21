# GitHub Token 配置指南

## 为什么需要 Token

不配 Token 时，GitHub API 限制 60 次/小时（公开仓库只读）。配置 Token 后提升到 5000 次/小时，足够频繁分析和测试。

## 步骤

### 1. 生成 Token

1. 打开 https://github.com/settings/tokens?type=beta（Fine-grained tokens，推荐）
2. 点击 **Generate new token**
3. 填写：
   - **Token name**: `maintainer-agent`
   - **Expiration**: 90 days（或自定义）
   - **Repository access**: 如果你只分析公开仓库，选 `Public Repositories (read-only)`；如果需要写操作（审批发布），选特定仓库
   - **Permissions**:
     - 如果只需要**只读分析**：`Issues: Read`，`Pull requests: Read`，`Metadata: Read`
     - 如果需要**审批发布**（打标签、发评论、关 issue）：`Issues: Write`，`Pull requests: Write`
4. 点击 **Generate token**
5. 复制 Token（`github_pat_xxx...`）

### 2. 填入 .env

打开 `C:\Users\谦友Lee\Desktop\Project\Ap\.env`，找到 `GITHUB_TOKEN=` 行，填入：

```
GITHUB_TOKEN=github_pat_xxx你的token
```

### 3. 重启后端

```bash
cd C:\Users\谦友Lee\Desktop\Project\Ap
python -c "from dotenv import load_dotenv; load_dotenv(); from maintainer_agent.api.server import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

### 4. 配置到 HuggingFace Space（可选）

在 Space 的 **Settings → Variables and secrets** 里添加：
- `GITHUB_TOKEN` = `github_pat_xxx...`（设为 Secret）

### 5. 配置到 GitHub Action（可选）

在仓库的 **Settings → Secrets and variables → Actions** 里添加：
- `GITHUB_TOKEN` 通常已自动提供（`${{ secrets.GITHUB_TOKEN }}`）
- 如果需要更高权限，创建 `MAINTAINER_AGENT_GITHUB_TOKEN` secret

## 验证

启动后端后访问 `http://localhost:8000/api/health` 确认服务正常。
然后输入 `pallets/flask` 分析，不应该再出现 429 限流错误。
