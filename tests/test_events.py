from __future__ import annotations

import unittest

from airlock.events import MAX_PREVIEW_LENGTH, arguments_preview, redact


class EventTests(unittest.TestCase):
    def test_redacts_common_secret_shapes(self) -> None:
        text = "api_key=super-secret-value token: abc123"
        redacted = redact(text)
        self.assertNotIn("super-secret-value", redacted)
        self.assertNotIn("abc123", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_preview_is_bounded(self) -> None:
        preview = arguments_preview({"content": "x" * 1000})
        self.assertLessEqual(len(preview), MAX_PREVIEW_LENGTH)
        self.assertTrue(preview.endswith("…"))


if __name__ == "__main__":
    unittest.main()
