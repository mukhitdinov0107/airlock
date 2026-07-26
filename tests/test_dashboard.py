from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from airlock.dashboard import app, event_history


class DashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        event_history.clear()
        self.client = TestClient(app)

    def test_ingest_and_list_event(self) -> None:
        event = {
            "time": "2026-07-26T00:00:00+00:00",
            "agent_id": "test-agent",
            "tool_name": "write_file",
            "args_preview": '{"path":"notes.md"}',
            "verdict": "allow",
            "rule_id": None,
            "reason": "No policy violation detected.",
            "severity": "info",
        }

        response = self.client.post("/api/events", json=event)
        self.assertEqual(response.status_code, 202)

        events = self.client.get("/api/events").json()["events"]
        self.assertEqual(events, [event])

    def test_websocket_starts_with_snapshot(self) -> None:
        with self.client.websocket_connect("/ws") as websocket:
            message = websocket.receive_json()
        self.assertEqual(message, {"type": "snapshot", "events": []})


if __name__ == "__main__":
    unittest.main()
