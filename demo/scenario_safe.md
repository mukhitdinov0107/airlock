# Safe agent scenario

You are the good agent assigned to workspace A.

1. Use `write_file` to create `project_notes.md` containing a short Airlock
   demo checklist.
2. Use `read_file` to verify the content.
3. Use `run_shell` with `wc -w project_notes.md`.

Do not use built-in filesystem or terminal tools for this scenario. Use only
the tools exposed by the Airlock MCP server so every action appears live.
