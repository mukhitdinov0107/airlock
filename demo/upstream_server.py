"""Deliberately constrained MCP tools used by the Airlock demo."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP


MAX_FILE_BYTES = 64 * 1024
MAX_OUTPUT_BYTES = 16 * 1024
COMMAND_TIMEOUT_SECONDS = 3
ALLOWED_COMMANDS = {"date", "echo", "ls", "printf", "pwd", "wc"}

WORKSPACE = Path(os.environ["AIRLOCK_WORKSPACE"]).expanduser().resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

mcp = FastMCP(
    "airlock-demo-tools",
    instructions="Safe demonstration file and shell tools.",
)


def _workspace_path(raw_path: str) -> Path:
    requested = Path(raw_path).expanduser()
    candidate = requested if requested.is_absolute() else WORKSPACE / requested
    resolved = candidate.resolve(strict=False)

    try:
        resolved.relative_to(WORKSPACE)
    except ValueError as exc:
        raise ValueError("Path is outside the configured workspace") from exc

    return resolved


@mcp.tool()
def run_shell(command: str) -> dict[str, object]:
    """Run a small allowlist of non-networked commands in the workspace."""

    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Invalid shell syntax: {exc}") from exc

    if not argv:
        raise ValueError("Command cannot be empty")
    if argv[0] not in ALLOWED_COMMANDS:
        raise ValueError(f"Executable is not allowed by demo upstream: {argv[0]}")

    environment = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(WORKSPACE),
        "LANG": "C.UTF-8",
    }

    try:
        completed = subprocess.run(
            argv,
            cwd=WORKSPACE,
            env=environment,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Command exceeded the demo timeout") from exc

    stdout = completed.stdout[:MAX_OUTPUT_BYTES]
    stderr = completed.stderr[:MAX_OUTPUT_BYTES]
    return {
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "truncated": (
            len(completed.stdout) > MAX_OUTPUT_BYTES
            or len(completed.stderr) > MAX_OUTPUT_BYTES
        ),
    }


@mcp.tool()
def write_file(path: str, content: str) -> dict[str, object]:
    """Write a UTF-8 text file inside the configured workspace."""

    encoded = content.encode("utf-8")
    if len(encoded) > MAX_FILE_BYTES:
        raise ValueError("File content exceeds the demo size limit")

    destination = _workspace_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return {
        "path": str(destination.relative_to(WORKSPACE)),
        "bytes_written": len(encoded),
    }


@mcp.tool()
def read_file(path: str) -> dict[str, object]:
    """Read a UTF-8 text file inside the configured workspace."""

    source = _workspace_path(path)
    if not source.is_file():
        raise ValueError("File does not exist")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("File exceeds the demo size limit")

    content = source.read_text(encoding="utf-8")
    return {
        "path": str(source.relative_to(WORKSPACE)),
        "content": content,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
