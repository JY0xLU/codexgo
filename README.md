# continue

Recover the previous Codex task after a compact/crash break.

`continue` is a tiny Codex global skill. When a Codex session loses context after background compaction fails, start a fresh session in the same workspace and type:

```text
continue
```

The script reads your local Codex state database, finds the previous thread for the current workspace, parses the rollout timeline, and returns the last actionable request.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/JY0xLU/continue.git ~/.codex/skills/continue
```

Restart Codex, then use `continue` at the beginning of a fresh session after a crash or compaction failure.

## What It Handles

- Last message is a real request: returns that request.
- Last message is `continue`, `go on`, `继续`, or similar: walks back to the previous real request.
- Last message is `ok`, `yes`, `好的`, or similar: recovers the assistant suggestion you agreed to.
- Last message is a supplement such as `补充：...`: merges it with the previous context.
- Output can be plain text or JSON.

## CLI

```bash
python scripts/continue.py --cwd . --format text
python scripts/continue.py --cwd . --format json
```

Options:

```text
--cwd <path>        Workspace path. Defaults to the current directory.
--codex-home <path> Codex data directory. Defaults to CODEX_HOME or ~/.codex.
--scope <mode>      Search mode: auto, exact, repo, or tree. Defaults to auto.
--skip-current      Skip the current thread. Enabled by default.
--recent <n>        Number of recent user messages to include. Defaults to 3.
--lookback <n>      Nearby timeline entries to include as context. Defaults to 6.
--format <fmt>      text or json. Defaults to text.
```

## Requirements

- Python 3.10+
- Codex local state in `~/.codex`
- No third-party Python packages

## Notes

This is a read-only local recovery tool. It does not upload conversation data and does not modify the Codex state database.
