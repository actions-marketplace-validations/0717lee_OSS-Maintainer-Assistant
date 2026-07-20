# Deploy to Hugging Face Spaces (Docker)

A free, shareable way to host the live demo.

1. Create a Space: https://huggingface.co/new-space -> **SDK: Docker** -> Blank.
2. Put this project's code in the Space repo (push it, or configure the Space to
   build from this GitHub repo). It needs the `Dockerfile` and `maintainer_agent/`.
3. Give the Space a `README.md` with this frontmatter so HF serves port 8000:

   ```yaml
   ---
   title: maintainer-agent
   emoji: "M"
   colorFrom: yellow
   colorTo: gray
   sdk: docker
   app_port: 8000
   pinned: false
   ---
   ```
4. (Optional) In **Settings -> Variables and secrets**, add `GITHUB_TOKEN` to
   raise GitHub rate limits, and `MAINTAINER_AGENT_LLM_MODEL` + `OPENAI_API_KEY`
   to enable a real LLM instead of the offline rule-based model.

Notes:
- The container binds `$PORT` (falling back to 8000), so it works on Spaces,
  Render, Fly, and most PaaS unchanged.
- `/api/run` caches results for ~2 minutes (`MAINTAINER_AGENT_CACHE_TTL`) to
  survive traffic spikes and GitHub rate limits.
- The dashboard has an EN / 中文 toggle; the digest is generated per-language.
