"""Security rule definitions.

Rule behavior lives in ``policy.py``. This module intentionally contains only
ordered data so policies can be changed without rewriting the engine.
"""

from __future__ import annotations

from typing import Any


RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "shell.destructive",
        "severity": "critical",
        "verdict": "block",
        "match_type": "regex_fields",
        "tools": ("run_shell",),
        "fields": ("command",),
        "patterns": (
            r"\brm\s+(?:-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b",
            r"\bdd\b[^\n]*\bof\s*=\s*/dev/",
            r"\bmkfs(?:\.[a-z0-9_-]+)?\b",
            r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
            r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:ba|z|k)?sh\b",
            r"\b(?:ufw|firewall-cmd|iptables|pfctl)\b[^\n]*"
            r"(?:disable|--flush|\s-F\b)",
        ),
        "reason": "Destructive or security-disabling shell command detected.",
    },
    {
        "id": "filesystem.workspace_escape",
        "severity": "critical",
        "verdict": "block",
        "match_type": "workspace_path",
        "tools": ("write_file",),
        "fields": ("path",),
        "forbidden_parts": ((".git", "hooks"), (".ssh",)),
        "reason": "Write target is outside the agent workspace or security-sensitive.",
    },
    {
        "id": "secrets.exfiltration",
        "severity": "critical",
        "verdict": "block",
        "match_type": "regex_arguments",
        "tools": ("run_shell", "write_file"),
        "patterns": (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"\bAKIA[0-9A-Z]{16}\b",
            r"\b(?:sk-ant-|sk-proj-|ghp_|github_pat_)[A-Za-z0-9_-]{12,}\b",
            r"(?is)(?:curl|wget|https?://).{0,240}"
            r"(?:\.env\b|private[_ -]?key|api[_ -]?key|secret|token)",
            r"(?is)(?:\.env\b|private[_ -]?key|api[_ -]?key|secret|token)"
            r".{0,240}(?:curl|wget|https?://)",
        ),
        "reason": "Potential secret material or external secret transfer detected.",
    },
)
