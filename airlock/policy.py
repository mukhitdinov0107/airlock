"""Ordered, deterministic policy evaluation."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from airlock.rules import RULES


Verdict = Literal["allow", "block", "flag"]


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    agent_id: str
    workspace: Path
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class Decision(BaseModel):
    verdict: Verdict
    rule_id: str | None = None
    reason: str = "No policy violation detected."
    severity: str = "info"


def _tool_applies(rule: dict[str, Any], call: ToolCall) -> bool:
    tools = rule.get("tools", ())
    return not tools or call.tool_name in tools


def _regex_fields_match(rule: dict[str, Any], call: ToolCall) -> bool:
    for field in rule.get("fields", ()):
        value = call.arguments.get(field)
        if not isinstance(value, str):
            continue
        if any(re.search(pattern, value, re.IGNORECASE) for pattern in rule["patterns"]):
            return True
    return False


def _regex_arguments_match(rule: dict[str, Any], call: ToolCall) -> bool:
    serialized = json.dumps(call.arguments, sort_keys=True, default=str)
    return any(
        re.search(pattern, serialized, re.IGNORECASE)
        for pattern in rule["patterns"]
    )


def _contains_forbidden_parts(
    relative_path: Path, forbidden_parts: tuple[tuple[str, ...], ...]
) -> bool:
    parts = relative_path.parts
    return any(
        tuple(parts[index : index + len(sequence)]) == sequence
        for sequence in forbidden_parts
        for index in range(len(parts) - len(sequence) + 1)
    )


def _workspace_path_match(rule: dict[str, Any], call: ToolCall) -> bool:
    workspace = call.workspace.expanduser().resolve()

    for field in rule.get("fields", ()):
        raw_path = call.arguments.get(field)
        if not isinstance(raw_path, str) or not raw_path.strip():
            return True

        requested = Path(raw_path).expanduser()
        candidate = requested if requested.is_absolute() else workspace / requested
        resolved = candidate.resolve(strict=False)

        try:
            relative = resolved.relative_to(workspace)
        except ValueError:
            return True

        if _contains_forbidden_parts(
            relative, tuple(rule.get("forbidden_parts", ()))
        ):
            return True

    return False


MATCHERS = {
    "regex_fields": _regex_fields_match,
    "regex_arguments": _regex_arguments_match,
    "workspace_path": _workspace_path_match,
}


def evaluate(call: ToolCall) -> Decision:
    """Return the first matching decision, defaulting to allow."""

    for rule in RULES:
        if not _tool_applies(rule, call):
            continue

        matcher = MATCHERS[rule["match_type"]]
        if matcher(rule, call):
            return Decision(
                verdict=rule["verdict"],
                rule_id=rule["id"],
                reason=rule["reason"],
                severity=rule["severity"],
            )

    return Decision(verdict="allow")
