"""OpenEcho Debug Web Console — atom 10.2.

Kanban-style pipeline visualization.
Each message is a card moving through columns: Input → Gateway → Queue → Dispatcher → Skill → Response.
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

# In-memory event buffer
_events: list[dict[str, Any]] = []
MAX_EVENTS = 2000


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
        for ev in _events[-200:]:
            await websocket.send_text(json.dumps(ev, ensure_ascii=False))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.remove(websocket)


KANBAN_HTML = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenEcho Debug</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

header {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-shrink: 0;
}
header h1 { font-size: 16px; font-weight: 600; color: #58a6ff; }
header .status { font-size: 12px; color: #8b949e; }
header .status.connected { color: #3fb950; }
header .controls { margin-left: auto; display: flex; gap: 8px; }
header button {
    background: #21262d; border: 1px solid #30363d; color: #c9d1d9;
    padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
}
header button:hover { background: #30363d; }

.board {
    display: flex;
    flex: 1;
    overflow-x: auto;
    padding: 16px;
    gap: 12px;
}

.column {
    min-width: 200px;
    max-width: 240px;
    flex-shrink: 0;
    background: #161b22;
    border-radius: 8px;
    border: 1px solid #30363d;
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 80px);
}

.column-header {
    padding: 12px;
    border-bottom: 1px solid #30363d;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}
.column-header .icon { font-size: 16px; }
.column-header .count {
    margin-left: auto;
    background: #30363d;
    border-radius: 10px;
    padding: 1px 8px;
    font-size: 11px;
    color: #8b949e;
}

.column-body {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.card {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px;
    font-size: 12px;
    transition: all 0.3s ease;
    cursor: default;
    position: relative;
}
.card.active {
    border-color: #58a6ff;
    box-shadow: 0 0 8px rgba(88,166,255,0.15);
}
.card.done {
    opacity: 0.5;
    border-color: #30363d;
}
.card .time {
    color: #8b949e;
    font-size: 10px;
    margin-bottom: 4px;
}
.card .text {
    color: #e6edf3;
    font-size: 12px;
    line-height: 1.4;
    word-break: break-word;
}
.card .detail {
    color: #8b949e;
    font-size: 11px;
    margin-top: 4px;
}
.card .badge {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 500;
    margin-top: 4px;
}
.badge-skill { background: #1f6feb33; color: #58a6ff; }
.badge-type { background: #23863633; color: #3fb950; }
.badge-error { background: #da363333; color: #f85149; }
.badge-intents { background: #a371f733; color: #bc8cff; }

/* Column-specific accent colors */
.col-input .column-header { border-left: 3px solid #f0883e; }
.col-gateway .column-header { border-left: 3px solid #a371f7; }
.col-queue .column-header { border-left: 3px solid #d29922; }
.col-dispatcher .column-header { border-left: 3px solid #58a6ff; }
.col-skill .column-header { border-left: 3px solid #3fb950; }
.col-response .column-header { border-left: 3px solid #8b949e; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

/* Message timeline at bottom */
.timeline {
    background: #161b22;
    border-top: 1px solid #30363d;
    padding: 8px 20px;
    font-size: 11px;
    color: #8b949e;
    flex-shrink: 0;
    display: flex;
    gap: 16px;
    align-items: center;
}
.timeline .msg-count { color: #58a6ff; }
</style>
</head>
<body>

<header>
    <h1>OpenEcho Debug</h1>
    <span id="status" class="status">connecting...</span>
    <div class="controls">
        <button onclick="clearBoard()">Clear</button>
        <button onclick="toggleAutoScroll()">Auto-scroll: ON</button>
    </div>
</header>

<div class="board">
    <div class="column col-input" id="col-input">
        <div class="column-header">
            <span class="icon">📩</span> Вход
            <span class="count" id="cnt-input">0</span>
        </div>
        <div class="column-body" id="body-input"></div>
    </div>

    <div class="column col-gateway" id="col-gateway">
        <div class="column-header">
            <span class="icon">🧠</span> Gateway
            <span class="count" id="cnt-gateway">0</span>
        </div>
        <div class="column-body" id="body-gateway"></div>
    </div>

    <div class="column col-queue" id="col-queue">
        <div class="column-header">
            <span class="icon">📋</span> Очередь
            <span class="count" id="cnt-queue">0</span>
        </div>
        <div class="column-body" id="body-queue"></div>
    </div>

    <div class="column col-dispatcher" id="col-dispatcher">
        <div class="column-header">
            <span class="icon">⚡</span> Диспетчер
            <span class="count" id="cnt-dispatcher">0</span>
        </div>
        <div class="column-body" id="body-dispatcher"></div>
    </div>

    <div class="column col-skill" id="col-skill">
        <div class="column-header">
            <span class="icon">🎯</span> Скилл
            <span class="count" id="cnt-skill">0</span>
        </div>
        <div class="column-body" id="body-skill"></div>
    </div>

    <div class="column col-response" id="col-response">
        <div class="column-header">
            <span class="icon">💬</span> Ответ
            <span class="count" id="cnt-response">0</span>
        </div>
        <div class="column-body" id="body-response"></div>
    </div>
</div>

<div class="timeline">
    <span>Messages: <span class="msg-count" id="msg-total">0</span></span>
    <span>Events: <span id="evt-total">0</span></span>
    <span id="last-time">—</span>
</div>

<script>
// --- State ---
const messages = {};  // msg_id -> { events: [], text: '', startTime: '' }
let eventCount = 0;
let autoScroll = true;

// Column mapping: step -> column id
const STEP_TO_COL = {
    'input': 'input',
    'session': 'gateway',
    'forward': 'gateway',
    'gateway': 'gateway',
    'queue': 'queue',
    'dispatcher': 'dispatcher',
    'skill': 'skill',
    'response': 'response',
    'error': 'response',
};

function getOrCreateMsg(msgId, ev) {
    if (!messages[msgId]) {
        messages[msgId] = {
            id: msgId,
            text: ev.user_text || '',
            startTime: ev.ts || '',
            events: [],
            cards: {},        // col -> card DOM element
            currentCol: null,
        };
        document.getElementById('msg-total').textContent = Object.keys(messages).length;
    }
    return messages[msgId];
}

function createCard(msg, col, ev) {
    const card = document.createElement('div');
    card.className = 'card active';
    card.dataset.msgId = msg.id;

    let html = `<div class="time">${ev.ts || ''}</div>`;

    if (col === 'input') {
        html += `<div class="text">${escHtml(msg.text || '...')}</div>`;
        if (ev.label) html += `<span class="badge badge-type">${escHtml(ev.label)}</span>`;
    } else if (col === 'gateway') {
        if (ev.step === 'session') {
            html += `<div class="detail">${escHtml(ev.detail || '')}</div>`;
        } else if (ev.step === 'forward') {
            html += `<div class="text">↩️ forward</div>`;
            html += `<div class="detail">${escHtml(ev.detail || '')}</div>`;
        } else {
            // LLM parsing
            html += `<div class="text">${escHtml(ev.detail || '')}</div>`;
            if (ev.label) html += `<span class="badge badge-intents">${escHtml(ev.label)}</span>`;
        }
    } else if (col === 'queue') {
        html += `<div class="text">${escHtml(ev.detail || '')}</div>`;
        if (ev.label) html += `<span class="badge badge-type">${escHtml(ev.label)}</span>`;
    } else if (col === 'dispatcher') {
        html += `<div class="text">${escHtml(ev.detail || '')}</div>`;
    } else if (col === 'skill') {
        html += `<div class="text">${escHtml(ev.detail || '')}</div>`;
        if (ev.label) html += `<span class="badge badge-skill">${escHtml(ev.label)}</span>`;
    } else if (col === 'response') {
        if (ev.step === 'error') {
            html += `<div class="text">${escHtml(ev.detail || 'error')}</div>`;
            html += `<span class="badge badge-error">error</span>`;
        } else {
            html += `<div class="text">✓ sent</div>`;
            html += `<div class="time">${ev.ts || ''}</div>`;
        }
    }

    card.innerHTML = html;
    return card;
}

function handleEvent(ev) {
    eventCount++;
    document.getElementById('evt-total').textContent = eventCount;
    if (ev.ts) document.getElementById('last-time').textContent = ev.ts;

    const msgId = ev.msg_id || ('unknown_' + eventCount);
    const msg = getOrCreateMsg(msgId, ev);
    msg.events.push(ev);

    const step = ev.step || '';
    const col = STEP_TO_COL[step];
    if (!col) return;

    // Mark previous cards for this message as done
    for (const [prevCol, prevCard] of Object.entries(msg.cards)) {
        if (prevCol !== col) {
            prevCard.classList.remove('active');
            prevCard.classList.add('done');
        }
    }

    // If card already exists in this column, update it (e.g. session + gateway.level2 both go to gateway)
    if (msg.cards[col]) {
        // Append detail to existing card
        const existing = msg.cards[col];
        if (ev.detail) {
            const d = document.createElement('div');
            d.className = 'detail';
            d.textContent = ev.detail;
            existing.appendChild(d);
        }
        if (ev.label && step !== 'session') {
            const badge = document.createElement('span');
            badge.className = 'badge badge-intents';
            badge.textContent = ev.label;
            existing.appendChild(badge);
        }
        existing.classList.add('active');
        existing.classList.remove('done');
        return;
    }

    // Create new card
    const card = createCard(msg, col, ev);
    msg.cards[col] = card;
    msg.currentCol = col;

    const body = document.getElementById('body-' + col);
    body.prepend(card);

    // Update count
    updateCount(col);

    // Auto-scroll
    if (autoScroll) {
        body.scrollTop = 0;
    }
}

function updateCount(col) {
    const body = document.getElementById('body-' + col);
    const cnt = body.children.length;
    document.getElementById('cnt-' + col).textContent = cnt;
}

function updateAllCounts() {
    ['input', 'gateway', 'queue', 'dispatcher', 'skill', 'response'].forEach(updateCount);
}

function clearBoard() {
    ['input', 'gateway', 'queue', 'dispatcher', 'skill', 'response'].forEach(col => {
        document.getElementById('body-' + col).innerHTML = '';
    });
    Object.keys(messages).forEach(k => delete messages[k]);
    eventCount = 0;
    document.getElementById('evt-total').textContent = '0';
    document.getElementById('msg-total').textContent = '0';
    updateAllCounts();
}

function toggleAutoScroll() {
    autoScroll = !autoScroll;
    event.target.textContent = 'Auto-scroll: ' + (autoScroll ? 'ON' : 'OFF');
}

function escHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// --- WebSocket ---
function connect() {
    const ws = new WebSocket(`ws://${location.host}/ws`);
    const statusEl = document.getElementById('status');

    ws.onopen = () => {
        statusEl.textContent = 'connected';
        statusEl.className = 'status connected';
    };

    ws.onmessage = (e) => {
        try {
            const ev = JSON.parse(e.data);
            handleEvent(ev);
        } catch (err) {
            console.error('Parse error:', err);
        }
    };

    ws.onclose = () => {
        statusEl.textContent = 'disconnected — reconnecting...';
        statusEl.className = 'status';
        setTimeout(connect, 2000);
    };

    ws.onerror = () => {
        ws.close();
    };
}

connect();
</script>
</body>
</html>"""


@app.get("/debug")
async def debug_page() -> HTMLResponse:
    return HTMLResponse(KANBAN_HTML)


@app.get("/debug/state")
async def debug_state() -> dict[str, Any]:
    """Return current system state."""
    return {
        "events_buffered": len(_events),
        "clients_connected": len(_clients),
    }
