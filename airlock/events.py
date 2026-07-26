"""Redacted security event creation and best-effort delivery."""

from __future__ import annotations

import json
import logging
import re
from datetime import timezone
from typing import Any

import httpx
from pydantic import BaseModel

from airlock.policy import Decision, ToolCall, Verdict


logger = logging.getLogger(__name__)

MAX_PREVIEW_LENGTH = 280
SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password)(\s*[=:]\s*)([^\s,;&]+)"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:sk-ant-|sk-proj-|ghp_|github_pat_)[A-Za-z0-9_-]{8,}\b"),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?"
        r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        re.DOTALL,
    ),
)


class SecurityEvent(BaseModel):
    time: str
    agent_id: str
    tool_name: str
    args_preview: str
    verdict: Verdict
    rule_id: str | None
    reason: str
    severity: str


def redact(value: str) -> str:
    """Remove common credential shapes from text before telemetry leaves."""

    redacted = value
    for index, pattern in enumerate(SECRET_PATTERNS):
        replacement = r"\1\2[REDACTED]" if index == 0 else "[REDACTED]"
        redacted = pattern.sub(replacement, redacted)
    return redacted


def arguments_preview(arguments: dict[str, Any]) -> str:
    serialized = json.dumps(arguments, sort_keys=True, default=str)
    preview = redact(serialized)
    if len(preview) > MAX_PREVIEW_LENGTH:
        return f"{preview[: MAX_PREVIEW_LENGTH - 1]}…"
    return preview


def build_event(call: ToolCall, decision: Decision) -> SecurityEvent:
    return SecurityEvent(
        time=call.timestamp.astimezone(timezone.utc).isoformat(),
        agent_id=call.agent_id,
        tool_name=call.tool_name,
        args_preview=arguments_preview(call.arguments),
        verdict=decision.verdict,
        rule_id=decision.rule_id,
        reason=decision.reason,
        severity=decision.severity,
    )


class EventPublisher:
    """Send telemetry without making tool execution depend on the dashboard."""

    def __init__(self, url: str, timeout: float, token: str | None = None) -> None:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._client = httpx.AsyncClient(timeout=timeout, headers=headers)
        self._url = url

    async def publish(self, event: SecurityEvent) -> None:
        try:
            response = await self._client.post(
                self._url, json=event.model_dump(mode="json")
            )
            response.raise_for_status()
        except (httpx.HTTPError, RuntimeError) as exc:
            logger.warning("Dashboard event delivery failed: %s", exc)

    async def close(self) -> None:
        await self._client.aclose()
