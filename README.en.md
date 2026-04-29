# codexgo

[中文](README.md)

`codexgo` is a tiny recovery tool for Codex. It helps recover the previous actionable task after a Codex session is interrupted by compaction failure, crash, or lost context.

It is local-only and read-only. It does not upload conversations and does not modify the Codex state database.

## When to Use It

After a Codex session breaks, open a fresh Codex session in the same project directory and type:

```text
codexgo
```

The skill reads the local Codex state database, finds the previous thread for the current workspace, parses the rollout timeline, and returns the request that most likely needs to be continued.

## What It Handles

- Last user message is a real task: returns that task.
- Last user message is `continue`, `go on`, `继续`, or similar: walks back to the previous real request.
- Last user message is `ok`, `yes`, `好的`, or similar: recovers the assistant suggestion you agreed to.
- Last user message is a supplement such as `补充：...`: merges it with the previous context.
- Output can be plain text or JSON.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/JY0xLU/codexgo.git ~/.codex/skills/codexgo
```

Restart Codex, then type `codexgo` at the beginning of a fresh session.

## CLI

```bash
python scripts/codexgo.py --cwd . --format text
python scripts/codexgo.py --cwd . --format json
```

Options:

```text
--cwd <path>         Workspace path. Defaults to the current directory.
--codex-home <path>  Codex data directory. Defaults to CODEX_HOME or ~/.codex.
--scope <mode>       Search mode: auto, exact, repo, or tree. Defaults to auto.
--skip-current       Skip the current thread. Enabled by default.
--recent <n>         Number of recent user messages to include. Defaults to 3.
--lookback <n>       Nearby timeline entries to include as context. Defaults to 6.
--format <fmt>       text or json. Defaults to text.
```

## Requirements

- Python 3.10+
- Codex local state in `~/.codex`
- No third-party Python packages

## Development

Run tests:

```bash
python -m pytest tests/test_codexgo.py -p no:cacheprovider
```
