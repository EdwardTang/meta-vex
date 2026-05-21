# AlphaGo Coding Lab — VEX MetaHarness Playground

A web playground that lets K-8 students see industrial-grade AutoML applied to a VEX IQ-style robotics task. Students don't write algorithms — they define the scenario and reward, and watch the system self-discover an optimal strategy in real time.

Built for the AI Builders Space platform (Koyeb-backed Docker deployment) using FastAPI + matplotlib + the platform's OpenAI-compatible LLM proxy.

## Architecture

```
GET  /                   → static/index.html (Chinese UI)
GET  /api/health         → service status + task config
POST /api/evolve         → run 50-gen GA, return policy + base64 PNG comparison
POST /api/coach          → grok-4-fast explains the evolved policy in Chinese
```

All assets served from one process / one port (Koyeb-compatible).

## Local dev

```bash
cd playground
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env       # paste your AI_BUILDER_TOKEN
set -a; . ./.env; set +a
.venv/bin/uvicorn app.main:app --reload --port 8000
# → open http://localhost:8000
```

The `/api/coach` route needs `AI_BUILDER_TOKEN`. The simulation + viz routes work without a token.

## Deploy to ai-builders.space

1. Push this folder to a public GitHub repo
2. Call the deployment API:

```bash
curl -X POST https://space.ai-builders.com/backend/v1/deployments \
  -H "Authorization: Bearer $AI_BUILDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/<you>/meta-vex",
    "service_name": "meta-vex",
    "branch": "main"
  }'
```

3. Wait 5–10 min. Open `https://meta-vex.ai-builders.space`.

`AI_BUILDER_TOKEN` is auto-injected into the container at runtime, so the coach route works without manual config. Default `PORT=8000` is honored via `${PORT:-8000}` in the Dockerfile.

## Resource budget (Koyeb nano = 256 MB)

| Component | Estimate |
|---|---|
| python:3.11-slim + uvicorn | ~60 MB |
| matplotlib (Agg backend) | ~50 MB |
| openai SDK | ~15 MB |
| app code + sim state | ~10 MB |
| **Headroom** | ~120 MB |

Stdlib-only simulation (no numpy/scipy) keeps memory low. matplotlib renders directly to base64 PNG in-process — no disk writes during request.

## Files

```
playground/
├── Dockerfile              # python:3.11-slim, shell-form CMD honors $PORT
├── requirements.txt        # fastapi, uvicorn, matplotlib, openai, pydantic
├── .env.example
├── .gitignore
├── README.md
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI routes
    ├── simulation.py       # GA + VEX task (stdlib)
    ├── viz.py              # matplotlib → base64 PNG
    ├── coach.py            # grok-4-fast Chinese explanation
    └── static/
        ├── index.html      # AlphaGo Coding Lab Chinese UI
        ├── style.css       # dark-mode card layout
        └── app.js          # fetch /api/evolve + /api/coach
```
