from collections import deque
from datetime import datetime
import json
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from echo_service.models import WebhookEntry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echo-service")

app = FastAPI(title="Webhook Echo Service")

# In-memory store: holds the last 1000 webhooks
store: deque = deque(maxlen=1000)
store_lock = asyncio.Lock()

# Templates and static files
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
# Fallback to project root during development if package resources are not installed
if not TEMPLATES_DIR.exists():
    TEMPLATES_DIR = Path.cwd() / "templates"
if not STATIC_DIR.exists():
    STATIC_DIR = Path.cwd() / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    logger.warning("Static directory not found; skipping static mount (looked for %s)", STATIC_DIR)


def _client_ip(request: Request) -> str:
    # Prefer X-Forwarded-For if behind a proxy
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # may contain a list
        return xff.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@app.post("/webhook", status_code=200)
async def receive_webhook(request: Request):
    """Receive a webhook from any source.

    Stores it in memory with some technical metadata.
    """
    raw = await request.body()
    try:
        body: Any = await request.json()
    except Exception:
        try:
            body = raw.decode(errors="replace")
        except Exception:
            body = None

    headers = {k: v for k, v in request.headers.items()}
    entry = WebhookEntry(
        id=str(uuid4()),
        received_at=datetime.utcnow().isoformat() + "Z",
        method=request.method,
        path=str(request.url.path),
        client_ip=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        headers=headers,
        body=body,
        raw_body=raw.decode(errors="replace"),
    )

    async with store_lock:
        store.appendleft(entry)

    logger.info("Received webhook %s from %s", entry.id, entry.client_ip)

    return JSONResponse({"status": "ok", "id": entry.id})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, page: int = 1, per_page: int = 25):
    """Simple UI to list recent webhooks."""
    per_page = max(1, min(200, per_page))
    start = (page - 1) * per_page
    end = start + per_page

    async with store_lock:
        entries = list(store)[start:end]
        total = len(store)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "entries": entries,
            "page": page,
            "per_page": per_page,
            "total": total,
        },
    )


@app.get("/webhooks/{entry_id}", response_class=HTMLResponse)
async def details(request: Request, entry_id: str):
    async with store_lock:
        match = next((e for e in store if e.id == entry_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Webhook not found")

    pretty_body = None
    try:
        pretty_body = json.dumps(match.body, indent=2, ensure_ascii=False)
    except Exception:
        pretty_body = match.raw_body

    return templates.TemplateResponse(
        "detail.html",
        {"request": request, "entry": match, "pretty_body": pretty_body},
    )


@app.get("/api/webhooks")
async def api_list(page: int = 1, per_page: int = 100):
    per_page = max(1, min(1000, per_page))
    start = (page - 1) * per_page
    end = start + per_page
    async with store_lock:
        items = list(store)[start:end]
    return JSONResponse([i.dict() for i in items])


@app.get("/api/webhooks/{entry_id}")
async def api_get(entry_id: str):
    async with store_lock:
        match = next((e for e in store if e.id == entry_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return JSONResponse(match.dict())


@app.get("/favicon.ico")
async def favicon():
    # Return a tiny inline SVG as the favicon to avoid 404s for browsers.
    svg = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" fill="#0d6efd"/>'
        '<text x="50%" y="50%" font-size="36" text-anchor="middle" fill="#ffffff" dy=".35em">E</text>'
        '</svg>'
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/health")
async def health():
    return {"status": "ok", "received": len(store)}
