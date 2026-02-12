"""OpenEcho Debug Web Console — atom 10.2.

FastAPI + WebSocket live event feed.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI(title="OpenEcho Debug Console")

# Connected WebSocket clients
_clients: list[WebSocket] = []

# In-memory event buffer for the web page
_events: list[dict[str, Any]] = []
MAX_EVENTS = 500


async def broadcast_event(event: dict[str, Any]) -> None:
    """Broadcast an event to all connected WebSocket clients."""
    _events.append(event)
    if len(_events) > MAX_EVENTS:
        _events.pop(0)
    message = json.dumps(event, ensure_ascii=False)
    for ws in list(_clients):
        try:
            await ws.send_text(message)
        except Exception:
            _clients.remove(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.append(websocket)
    try:
        # Send recent events
        for ev in _events[-50:]:
            await websocket.send_text(json.dumps(ev, ensure_ascii=False))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.remove(websocket)


@app.get("/debug")
async def debug_page() -> HTMLResponse:
    html = """<!DOCTYPE html>
<html><head><title>OpenEcho Debug</title>
<style>
body { font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }
#events { max-height: 80vh; overflow-y: auto; }
.event { border-bottom: 1px solid #333; padding: 4px 0; }
.ts { color: #569cd6; } .comp { color: #4ec9b0; } .action { color: #ce9178; }
</style></head>
<body><h1>OpenEcho Debug Console</h1>
<div id="events"></div>
<script>
const ws = new WebSocket(`ws://${location.host}/ws`);
const el = document.getElementById('events');
ws.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    const div = document.createElement('div');
    div.className = 'event';
    div.innerHTML = `<span class="ts">${ev.timestamp||''}</span> <span class="comp">[${ev.component||''}]</span> <span class="action">${ev.action||''}</span>`;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
};
</script></body></html>"""
    return HTMLResponse(html)


@app.get("/debug/state")
async def debug_state() -> dict[str, Any]:
    """Return current system state (placeholder)."""
    return {
        "events_buffered": len(_events),
        "clients_connected": len(_clients),
    }
