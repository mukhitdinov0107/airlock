# Frontend contract

The frontend can be a single `dashboard/index.html` file. The FastAPI service
serves that file at `/` automatically.

## Initial state

Connect to `ws://<host>/ws`. The first message is:

```json
{
  "type": "snapshot",
  "events": []
}
```

## Live events

Every subsequent message is:

```json
{
  "type": "event",
  "event": {
    "time": "2026-07-26T02:30:00+00:00",
    "agent_id": "cursor-agent",
    "tool_name": "write_file",
    "args_preview": "{\"path\":\"notes.md\"}",
    "verdict": "allow",
    "rule_id": null,
    "reason": "No policy violation detected.",
    "severity": "info"
  }
}
```

Verdicts are `allow`, `block`, or `flag`. Render green, red, and amber
respectively. Count verdicts from the snapshot, then increment for each event.

The REST fallback is `GET /api/events`, which returns `{"events": [...]}`.
Health is available at `GET /health`.
