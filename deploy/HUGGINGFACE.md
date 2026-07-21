# Deploy to Hugging Face Spaces (Docker)

A free, shareable way to host the live demo.

## Steps

1. **Create a Space**: https://huggingface.co/new-space -> **SDK: Docker** -> Blank.

2. **Push the project code** to the Space repo. It needs the `Dockerfile`, `maintainer_agent/`, `web/`, and `docker/` directories. The Dockerfile is a multi-stage build: it compiles the React/Vite frontend with Node.js, then installs the Python package with the compiled dashboard bundled in.

3. **Add Space metadata** — put this frontmatter in the Space repo's `README.md`:

   ```yaml
   ---
   title: maintainer-agent
   emoji: "🤖"
   colorFrom: yellow
   colorTo: gray
   sdk: docker
   app_port: 8000
   pinned: true
   ---
   ```

4. **(Optional) Configure secrets** in **Settings -> Variables and secrets**:
   - `GITHUB_TOKEN` — raises GitHub API rate limits for live repo analysis
   - `MAINTAINER_AGENT_LLM_MODEL` + `DEEPSEEK_API_KEY` — enables a real LLM (e.g. `deepseek/deepseek-chat`)
   - Without any keys, the demo runs fully offline with bundled fixtures and a deterministic rule-based model

## Notes

- The container binds `$PORT` (falling back to 8000), so it works on Spaces,
  Render, Fly, and most PaaS unchanged.
- `/api/run` caches results for ~2 minutes (`MAINTAINER_AGENT_CACHE_TTL`) to
  survive traffic spikes and GitHub rate limits.
- The dashboard has an EN / 中文 toggle; the digest is generated per-language.
- The Docker multi-stage build requires Docker 17.05+ (for multi-stage support).
