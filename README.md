# Airlock

Airlock is a transparent MCP security checkpoint. It mirrors a real upstream
tool server, blocks unsafe calls before execution, and streams redacted policy
decisions to a live dashboard.

## Run in 60 seconds

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run.sh
```

The event API is now available at `http://127.0.0.1:8000`. The frontend
teammate's `dashboard/index.html` will be served at the same address.

Verify the complete MCP chain:

```bash
AIRLOCK_EVENT_URL=http://127.0.0.1:8000/api/events \
  .venv/bin/python -m demo.smoke_test
```

Expected result:

```text
PASS: passthrough and all three Airlock blocks are deterministic
```

## Connect an agent

Use the absolute path to `airlock-proxy.sh` in Cursor or Claude's MCP config.
This example assigns the host to workspace A:

```json
{
  "mcpServers": {
    "airlock": {
      "type": "stdio",
      "command": "/absolute/path/to/airlock/airlock-proxy.sh",
      "env": {
        "AIRLOCK_AGENT_ID": "cursor-agent",
        "AIRLOCK_WORKSPACE": "/absolute/path/to/airlock/demo/workspace_a",
        "AIRLOCK_EVENT_URL": "http://127.0.0.1:8000/api/events"
      }
    }
  }
}
```

Configure the second host with `AIRLOCK_AGENT_ID=claude-agent` and
`demo/workspace_b`. If the event API is deployed, replace
`AIRLOCK_EVENT_URL` with its HTTPS URL.

If `AIRLOCK_EVENT_TOKEN` is configured on the event service, set the same
value in each proxy's environment. Airlock sends it as a bearer token.

## Demo

1. Start the dashboard and leave it visible.
2. Give the good host [`demo/scenario_safe.md`](demo/scenario_safe.md).
3. Give the attacking host [`demo/scenario_attack.md`](demo/scenario_attack.md).
4. Show green allowed events followed by three red blocked events.
5. Verify workspace A was not overwritten.

## Frontend handoff

The frontend owns `dashboard/index.html` and can build a separate landing page.
The WebSocket and event payload contract is documented in
[`dashboard/README.md`](dashboard/README.md). No frontend build step is
required for the MVP.

## Hosted product shape

Deploy the landing page and FastAPI event hub publicly while each agent runs
the enforcement proxy locally:

```text
Cursor/Claude -> local Airlock -> local tools
                       |
                       +-> hosted event API -> live dashboard
```

For a hosted event hub:

```bash
HOST=0.0.0.0 PORT="${PORT:-8000}" AIRLOCK_EVENT_TOKEN="<random-token>" ./run.sh
```

[`render.yaml`](render.yaml) provides a ready-to-deploy Render web service.
Set `AIRLOCK_EVENT_TOKEN` in Render, then copy that value and the deployed
`https://<service>/api/events` URL into both local MCP configurations.

The proxy enforces policy even if telemetry delivery fails.

## Development boundaries

- The upstream uses an executable allowlist and `shell=False`.
- Demo credentials must always be fake.
- Regex policies demonstrate enforcement; they are not a complete shell
  sandbox.
- No database, merge coordination, or LLM classifier is included in the MVP.
