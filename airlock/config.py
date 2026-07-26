"""Environment-backed configuration for Airlock processes."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    agent_id: str
    workspace: Path
    event_url: str
    event_token: str | None
    event_timeout_seconds: float
    upstream_command: str
    upstream_args: tuple[str, ...]
    dashboard_host: str
    dashboard_port: int

    @classmethod
    def from_env(cls) -> "Settings":
        workspace = Path(
            os.getenv("AIRLOCK_WORKSPACE", PROJECT_ROOT / "demo" / "workspace_a")
        ).expanduser()

        return cls(
            agent_id=os.getenv("AIRLOCK_AGENT_ID", "demo-agent"),
            workspace=workspace.resolve(),
            event_url=os.getenv(
                "AIRLOCK_EVENT_URL", "http://127.0.0.1:8000/api/events"
            ),
            event_token=os.getenv("AIRLOCK_EVENT_TOKEN"),
            event_timeout_seconds=float(
                os.getenv("AIRLOCK_EVENT_TIMEOUT_SECONDS", "0.75")
            ),
            upstream_command=os.getenv("AIRLOCK_UPSTREAM_COMMAND", sys.executable),
            upstream_args=tuple(
                os.getenv(
                    "AIRLOCK_UPSTREAM_ARGS", "-m demo.upstream_server"
                ).split()
            ),
            dashboard_host=os.getenv("AIRLOCK_DASHBOARD_HOST", "127.0.0.1"),
            dashboard_port=int(os.getenv("AIRLOCK_DASHBOARD_PORT", "8000")),
        )
