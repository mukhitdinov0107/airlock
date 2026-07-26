# Airlock — Security Layer for Multi-Agent Systems

This file is the source of truth for the hackathon build.

## Product

Airlock is an MCP proxy between AI agents and their tools. It mirrors upstream
tools, evaluates every call against security policies, forwards safe calls,
blocks unsafe calls before execution, and streams redacted decisions to a live
dashboard.

The demo must show two real MCP hosts working against separate workspaces. A
safe agent produces allowed events. An attacking agent triggers deterministic
blocks for a dangerous shell command, a cross-agent file write, and secret
exfiltration.

## MVP definition of done

- Airlock runs as an MCP stdio server launched by Cursor or Claude.
- It starts an upstream MCP server, mirrors its tool definitions, and forwards
  allowed calls without changing their result.
- It blocks policy violations and returns `Blocked by Airlock: <reason>` as an
  MCP tool error.
- It publishes one redacted event per decision to a shared FastAPI service.
- The service keeps an in-memory event history and broadcasts events over a
  WebSocket to the dashboard.
- A deterministic smoke script proves blocked calls never reach the upstream.

## Process topology

Each MCP host launches its own Airlock stdio process, and each Airlock process
launches an upstream stdio server:

```text
Cursor -> Airlock A -> Upstream A
Claude -> Airlock B -> Upstream B
                 \-> hosted/local event API -> dashboard
```

The dashboard event store cannot live inside a proxy process. The FastAPI
service owns history and WebSocket subscribers; proxies send events over HTTP.
Dashboard outages must never disable policy enforcement.

## Identity and workspaces

MCP does not provide a dependable per-agent identity. Trusted launch
configuration supplies:

- `AIRLOCK_AGENT_ID`
- `AIRLOCK_WORKSPACE`
- `AIRLOCK_EVENT_URL`

The proxy never accepts identity or workspace ownership from tool arguments.
Paths are canonicalized and checked against the assigned workspace before any
write is forwarded. The upstream repeats workspace enforcement as defense in
depth.

## Components

- `airlock/proxy.py`: low-level MCP server/client passthrough.
- `airlock/policy.py`: ordered rule evaluation and decision models.
- `airlock/rules.py`: rule definitions as data.
- `airlock/events.py`: redaction, preview creation, and best-effort publishing.
- `airlock/dashboard.py`: FastAPI event ingestion, history, and WebSocket.
- `airlock/config.py`: environment-backed process configuration.
- `demo/upstream_server.py`: deliberately constrained MCP tools.
- `demo/smoke_test.py`: deterministic end-to-end verification.
- `dashboard/index.html`: live zero-build operator UI.

## Policy order

1. Dangerous shell commands: destructive commands, fork bombs,
   curl/wget-to-shell, firewall disabling, and destructive filesystem tools.
2. Path escape/cross-agent writes: writes outside the configured workspace,
   including `/etc`, SSH data, Git hooks, `..`, and symlink escapes.
3. Secret exfiltration: private keys, common API key shapes, `.env` transfer,
   or commands that send local secret material to external URLs.
4. Prompt-injection detection is a stretch goal and is not part of the MVP.

The first matching block wins. If no block matches, the default is allow.
`policy.evaluate()` is pure; `proxy.py` publishes the decision exactly once.

## Safety boundary

Regex policy is a demo policy layer, not an arbitrary shell sandbox. The demo
upstream uses `shell=False`, an executable allowlist, a minimal environment,
timeouts, output limits, workspace checks, and fake secrets. Never use real
credentials in a scenario.

## Scope

Do not add a database, authentication system, frontend framework, merge guard,
LLM classifier, dynamic tool-catalog updates, or policy editor before the core
demo passes end to end.
