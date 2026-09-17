# Render Docker deployment

Create a Free web service from this repository. Choose Docker and set Dockerfile
Path to `./Dockerfile.render`, or create a Blueprint using `render.yaml`.
Deploy the reviewed `main` branch; `deploy/render` can be used for a preview.
The original Dockerfile remains the CLI/offline assignment deliverable.

The web image starts Streamlit on `0.0.0.0` and Render's `PORT` (default 10000).
Health check: `/_stcore/health`. No database or paid disk is required.

Configure environment variables in Render:

| Variable | Value |
|---|---|
| LLM_PROVIDER | gemini |
| LLM_MODEL | gemini-3.1-flash-lite |
| WEB_SEARCH_PROVIDER | duckduckgo |
| GOOGLE_API_KEY | Your private key, entered only in Render |
| RESEARCH_LOG_LEVEL | WARNING |

Sample demo works without a key. Never commit `.env` or real keys. Live requests
from visitors consume the configured provider account's quota; the current token
budget is per pipeline, not a global multi-user quota. Leave the key unset for a
sample-only public demo.

Free services sleep after inactivity and may start slowly on the next visit.
Filesystem cache is disposable and may disappear after restart or redeploy.

Verify the deployed URL: health endpoint returns HTTP 200; sample research returns
three references and downloads; live research returns cited evidence or an explicit
source degradation warning. A successful build alone is not end-to-end acceptance.

Local check:
```powershell
docker build -f Dockerfile.render -t vertex-research-web .
docker run --rm -p 10000:10000 --env-file .env vertex-research-web
```

Official guide: https://render.com/docs/docker
