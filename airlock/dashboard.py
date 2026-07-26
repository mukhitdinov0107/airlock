"""FastAPI event hub and dashboard server."""

from __future__ import annotations

import asyncio
import os
from collections import deque
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse

from airlock.events import SecurityEvent


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = PROJECT_ROOT / "dashboard" / "index.html"
EVENT_TOKEN = os.getenv("AIRLOCK_EVENT_TOKEN")
MAX_EVENTS = int(os.getenv("AIRLOCK_MAX_EVENTS", "500"))
SUBSCRIBER_QUEUE_SIZE = 100

app = FastAPI(title="Airlock Event Hub", version="0.1.0")
event_history: deque[SecurityEvent] = deque(maxlen=MAX_EVENTS)
subscribers: set[asyncio.Queue[SecurityEvent]] = set()


def _authorize_ingest(authorization: str | None) -> None:
    if EVENT_TOKEN and authorization != f"Bearer {EVENT_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid event token")


async def _broadcast(event: SecurityEvent) -> None:
    for queue in tuple(subscribers):
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(event)


@app.get("/", response_model=None)
async def dashboard() -> FileResponse | JSONResponse:
    if DASHBOARD_FILE.exists():
        return FileResponse(DASHBOARD_FILE)
    return JSONResponse(
        {
            "service": "airlock-event-hub",
            "message": "Frontend not installed. Connect to /ws for live events.",
        }
    )


@app.get("/health")
async def health() -> dict[str, str | int]:
    return {"status": "ok", "events": len(event_history)}


@app.get("/api/events")
async def list_events() -> dict[str, list[dict[str, object]]]:
    return {
        "events": [event.model_dump(mode="json") for event in event_history]
    }


@app.post("/api/events", status_code=202)
async def ingest_event(
    event: SecurityEvent, authorization: str | None = Header(default=None)
) -> dict[str, bool]:
    _authorize_ingest(authorization)
    event_history.append(event)
    await _broadcast(event)
    return {"accepted": True}


@app.websocket("/ws")
async def event_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue: asyncio.Queue[SecurityEvent] = asyncio.Queue(
        maxsize=SUBSCRIBER_QUEUE_SIZE
    )
    subscribers.add(queue)

    try:
        await websocket.send_json(
            {
                "type": "snapshot",
                "events": [
                    event.model_dump(mode="json") for event in event_history
                ],
            }
        )
        while True:
            event = await queue.get()
            await websocket.send_json(
                {"type": "event", "event": event.model_dump(mode="json")}
            )
    except WebSocketDisconnect:
        pass
    finally:
        subscribers.discard(queue)
