"""Transparent MCP tool proxy with policy enforcement."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from airlock.config import PROJECT_ROOT, Settings
from airlock.events import EventPublisher, build_event
from airlock.policy import ToolCall, evaluate


logging.basicConfig(
    level=os.getenv("AIRLOCK_LOG_LEVEL", "INFO"),
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _blocked_result(reason: str) -> types.CallToolResult:
    return types.CallToolResult(
        content=[
            types.TextContent(
                type="text",
                text=f"Blocked by Airlock: {reason}",
            )
        ],
        isError=True,
    )


async def run_proxy(settings: Settings | None = None) -> None:
    settings = settings or Settings.from_env()
    settings.workspace.mkdir(parents=True, exist_ok=True)

    upstream_environment = os.environ.copy()
    upstream_environment["AIRLOCK_WORKSPACE"] = str(settings.workspace)
    upstream_parameters = StdioServerParameters(
        command=settings.upstream_command,
        args=list(settings.upstream_args),
        env=upstream_environment,
        cwd=PROJECT_ROOT,
    )

    publisher = EventPublisher(
        url=settings.event_url,
        timeout=settings.event_timeout_seconds,
        token=settings.event_token,
    )
    server = Server(
        "airlock",
        version="0.1.0",
        instructions=(
            "Airlock mirrors upstream tools and blocks calls that violate "
            "workspace, shell, or secret-handling policies."
        ),
    )

    try:
        async with stdio_client(upstream_parameters) as (upstream_read, upstream_write):
            async with ClientSession(upstream_read, upstream_write) as upstream:
                await upstream.initialize()
                upstream_tools = (await upstream.list_tools()).tools
                logger.info(
                    "Airlock ready for agent=%s with %d upstream tools",
                    settings.agent_id,
                    len(upstream_tools),
                )

                @server.list_tools()
                async def list_tools() -> list[types.Tool]:
                    return upstream_tools

                @server.call_tool()
                async def call_tool(
                    name: str, arguments: dict[str, Any]
                ) -> types.CallToolResult:
                    call = ToolCall(
                        tool_name=name,
                        arguments=arguments,
                        agent_id=settings.agent_id,
                        workspace=settings.workspace,
                    )
                    decision = evaluate(call)
                    await publisher.publish(build_event(call, decision))

                    if decision.verdict == "block":
                        logger.warning(
                            "Blocked agent=%s tool=%s rule=%s",
                            settings.agent_id,
                            name,
                            decision.rule_id,
                        )
                        return _blocked_result(decision.reason)

                    return await upstream.call_tool(name, arguments)

                async with stdio_server() as (read_stream, write_stream):
                    await server.run(
                        read_stream,
                        write_stream,
                        server.create_initialization_options(),
                    )
    finally:
        await publisher.close()


def main() -> None:
    asyncio.run(run_proxy())


if __name__ == "__main__":
    main()
