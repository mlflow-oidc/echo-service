# Echo Service ✅

Tiny FastAPI app to receive, inspect, and browse webhooks (suitable for testing MLflow webhooks).

## Features
- Receives webhook POSTs at `/webhook`
- Keeps the last **1000** webhooks in memory (no persistence)
- Web UI at `/` to browse recent webhooks and view details
- JSON API at `/api/webhooks` and `/api/webhooks/{id}`
- Adds technical metadata (IP, User-Agent, headers, timestamp)
- Health endpoint at `/health`
- Serves a small SVG favicon at `/favicon.ico`

---

## Quick start (local)

1. Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the server (development):

```bash
# Run directly from source (port 8000)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or run using the package entrypoint (Dockerfile uses 8800)
uvicorn echo_service:app --reload --host 0.0.0.0 --port 8800
```

3. Open the UI: http://localhost:8000/ (or :8800 if you used that port)

---

## Docker

Build and run the provided Docker image (the Dockerfile exposes port **8800**):

```bash
docker build -t echo-service .
docker run -p 8800:8800 echo-service
# Open http://localhost:8800/
```

If you prefer a different port, set the runtime port mapping accordingly.

---

## API & examples

- POST /webhook — receive any webhook payload (JSON, form, raw text, multipart)

Example JSON POST:

```bash
curl -i -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"event":"run.completed","run_id":"abc123"}'
```

- GET /api/webhooks — list recent webhooks (JSON)
- GET /api/webhooks/{id} — get webhook detail (JSON)
- GET /health — simple health JSON

Get the latest webhook ID and show it:

```bash
LATEST=$(curl -s http://localhost:8000/api/webhooks | jq -r '.[0].id')
curl -s http://localhost:8000/api/webhooks/$LATEST | jq .
```

---

## Tests

Run the unit tests with:

```bash
pytest -q
```

Note: The test suite uses `fastapi.testclient` and will start the app in-process.

---

## Notes

- The store is in-memory only and will be cleared when the app restarts (no persistence by design).
- The app prefers `X-Forwarded-For` when present to populate the client IP (useful behind proxies).
- The default stored webhook limit is `1000` (set in `echo_service/main.py` as `deque(maxlen=1000)`).

---

## Packaging & development

- A basic `pyproject.toml` is included for metadata and dev extras.
- To build a wheel and install it, you can run `python -m build` if you have `build` installed.

---

## License

MIT
