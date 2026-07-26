from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from airlock.dashboard import app, event_history


EVENT = {
    "time": "2026-07-26T00:00:00+00:00",
    "agent_id": "test-agent",
    "tool_name": "write_file",
    "args_preview": '{"path":"notes.md"}',
    "verdict": "allow",
    "rule_id": None,
    "reason": "No policy violation detected.",
    "severity": "info",
}


class DashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        event_history.clear()
        self.client = TestClient(app)

    def test_ingest_and_list_event(self) -> None:
        response = self.client.post("/api/events", json=EVENT)
        self.assertEqual(response.status_code, 202)

        events = self.client.get("/api/events").json()["events"]
        self.assertEqual(events, [EVENT])

    def test_websocket_snapshot_and_live_event(self) -> None:
        with self.client.websocket_connect("/ws") as websocket:
            snapshot = websocket.receive_json()
            self.assertEqual(snapshot, {"type": "snapshot", "events": []})

            response = self.client.post("/api/events", json=EVENT)
            self.assertEqual(response.status_code, 202)
            live_message = websocket.receive_json()

        self.assertEqual(live_message, {"type": "event", "event": EVENT})


if __name__ == "__main__":
    unittest.main()
