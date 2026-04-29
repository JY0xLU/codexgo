<p align="center">
  <img src="assets/codexgo-logo.png" alt="codexgo logo" width="132">
</p>

<h1 align="center">codexgo</h1>

<p align="center">
  <strong>A tiny Codex recovery skill.</strong><br>
  Recover the last actionable request from local session history.
</p>

<p align="center">
  <a href="README.md">中文</a>
  ·
  <a href="https://github.com/JY0xLU/codexgo">GitHub</a>
</p>

<p align="center">
  <a href="https://github.com/JY0xLU/codexgo/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/JY0xLU/codexgo?style=social"></a>
  <a href="https://github.com/JY0xLU/codexgo/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/JY0xLU/codexgo?style=social"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="Dependencies" src="https://img.shields.io/badge/deps-zero-10B981?style=flat-square">
  <img alt="Local only" src="https://img.shields.io/badge/privacy-local--only-0F766E?style=flat-square">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/JY0xLU/codexgo?style=flat-square"></a>
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/JY0xLU/codexgo?style=flat-square">
</p>

## What It Is

`codexgo` solves one specific problem: you already explained the task, Codex started working, and the thread vanished because of compaction failure, crash, or lost context. Open a fresh session, type `codexgo`, and it reads local Codex state plus rollout records to recover the most likely continuation request.

## Highlights

| Feature | What it means |
| --- | --- |
| Small | One Python script, one skill file, standard library only |
| Safe | Local-only, read-only, no uploads, no database writes |
| Context-aware | Skips low-signal replies and expands context for `三端`, `this plan`, and similar references |
| Scriptable | Supports both plain text and JSON output |
| Hackable | Compact logic that is easy to read, study, and modify |

## Install in 30 seconds

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/JY0xLU/codexgo.git ~/.codex/skills/codexgo
```

Restart Codex, then type this at the beginning of a fresh session:

```text
codexgo
```

## Usage Flow

<p align="center">
  <img src="assets/codexgo-usage.png" alt="codexgo recovery flow" width="100%">
</p>

## What It Handles

| Last message before interruption | How codexgo resolves it |
| --- | --- |
| A real task | Returns that task directly |
| `continue` / `go on` / `继续` | Walks back to the previous real request |
| `ok` / `yes` / `好的` | Recovers the assistant plan you agreed to |
| `补充：...` | Merges the supplement with the previous context |
| `三端` / `this plan` / `按上面` | Expands supporting context upward automatically |
| Selection or comparison prompts | Emits `decision_basis_message` as the decision basis |
| Automation use cases | Emits JSON for downstream tools |

JSON output also includes `context_expanded_upward`, which tells callers whether codexgo had to walk further upward to resolve an ambiguous reference.

## CLI

```bash
python scripts/codexgo.py --cwd . --format text
python scripts/codexgo.py --cwd . --format json
```

Common options:

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

## Star History

<p align="center">
  <a href="https://www.star-history.com/#JY0xLU/codexgo&Date">
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date">
  </a>
</p>

## Development

Run tests:

```bash
python -m pytest tests/test_codexgo.py -p no:cacheprovider
```

## License

Apache-2.0
