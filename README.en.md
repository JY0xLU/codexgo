<p align="center">
  <img src="assets/codexgo-logo.png" alt="codexgo logo" width="132">
</p>

<h1 align="center">codexgo</h1>

<p align="center">
  <strong>A local read-only recovery skill for Codex sessions.</strong><br>
  Recover the previous actionable request in a fresh thread, without re-explaining the whole task.
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
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square"></a>
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/JY0xLU/codexgo/main?style=flat-square">
</p>

## Purpose

`codexgo` is a small Codex skill that builds a continuation prompt for a fresh Codex thread.

It does not call the network, write to Codex databases, or edit project files. It only reads local Codex state and session records, then selects the request most suitable for continuing the previous task.

Typical use at the beginning of a fresh thread:

```text
codexgo
```

Then continue with the returned `resolved_request`.

## Use Cases

| Situation | What codexgo does |
| --- | --- |
| A long session became unusable | Recovers the previous task entry point |
| Last message was `continue` / `继续` | Finds the concrete request it refers to |
| Last message was `ok` / `好的` | Recovers the assistant proposal you accepted |
| Last message added a constraint | Merges the supplement with nearby task context |
| Current directory is nested | Searches by workspace tree or Git repository scope |
| Automation needs structured data | Emits stable JSON fields |

If no credible continuation is found, it returns an error state instead of inventing one.

## Local Inputs

`codexgo` is a local read-only parser. It uses:

| Source | Purpose |
| --- | --- |
| `state_*.sqlite` | Finds Codex threads, workspace paths, and update times |
| rollout JSONL | Reads user messages, assistant replies, tool events, and interruption markers |
| current `--cwd` | Starting point for workspace matching |
| recent user messages | Detects tasks, acknowledgements, supplements, and triggers |
| recent assistant messages | Recovers accepted proposals after short agreement replies |

By default, the current thread is skipped so the `codexgo` trigger itself does not become the recovered request.

## Matching Scope

`--scope` controls which historical threads may be used:

| Scope | Meaning |
| --- | --- |
| `exact` | Match only the exact same workspace path |
| `repo` | Match threads from the same Git repository |
| `tree` | Match parent or child directory threads |
| `auto` | Default strategy that chooses an appropriate scope |

`tree` is useful in the Codex app because a task may start at the repo root and later continue from a nested directory.

## Filtering And Backtracking

The final message before a break is often not a complete task. `codexgo` handles common low-signal messages with deterministic rules:

| Type | Examples | Behavior |
| --- | --- | --- |
| Continue trigger | `continue`, `go on`, `继续`, `jixu` | Walks back to the previous concrete task |
| Agreement | `ok`, `yes`, `好的`, `可以` | Recovers the previous assistant proposal |
| Skill trigger | `codexgo`, `golast` | Does not treat the trigger as task content |
| Interruption marker | `<turn_aborted>` | Ignores it |
| Empty shell thread | Only system text, AGENTS content, or triggers | Skips it and keeps searching |

When a request depends on older context, `context_expanded_upward` is set and nearby messages are included in `supporting_context`.

## JSON Fields

Use `--format json` for scripts:

| Field | Meaning |
| --- | --- |
| `status` | `ok` or an error state |
| `current_cwd` | Workspace passed to this run |
| `scope_used` | Search scope actually used |
| `matched_cwd` | Workspace path from the recovered thread |
| `thread_id` | Matching Codex thread |
| `literal_last_user_message` | Last user message exactly as stored in the timeline |
| `resolved_request` | Request recommended for continuation |
| `resolved_source` | Source category, such as user task, assistant proposal, or supplement merge |
| `decision_basis_message` | Proposal or comparison basis behind an accepted decision |
| `supporting_context` | Nearby messages used to resolve context dependency |
| `recent_user_messages` | Recent user messages for manual inspection |
| `context_expanded_upward` | Whether older context was pulled in |

Example:

```json
{
  "status": "ok",
  "scope_used": "tree",
  "matched_cwd": "/path/to/project",
  "resolved_request": "Finish the README polish and run the tests.",
  "resolved_source": "user_message",
  "decision_basis_message": "",
  "context_expanded_upward": false,
  "recent_user_messages": [
    "ok",
    "continue the previous direction"
  ]
}
```

## Installation

`codexgo` is a Codex skill, not a pip package. Put this repository inside Codex's `skills/codexgo` directory, then restart Codex.

### Codex App

The Codex desktop app may use a dedicated `CODEX_HOME`. On Windows, this is often `D:\CodexData\.codex`; regular CLI setups usually use `~/.codex`.

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } elseif (Test-Path "D:\CodexData\.codex") { "D:\CodexData\.codex" } else { "$HOME\.codex" }
New-Item -ItemType Directory -Force "$CodexHome\skills" | Out-Null
git clone https://github.com/JY0xLU/codexgo.git "$CodexHome\skills\codexgo"
```

Restart the Codex app so local skills are rescanned.

### Codex CLI: macOS / Linux

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
git clone https://github.com/JY0xLU/codexgo.git "${CODEX_HOME:-$HOME/.codex}/skills/codexgo"
```

### Codex CLI: Windows PowerShell

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { "$HOME\.codex" }
New-Item -ItemType Directory -Force "$CodexHome\skills" | Out-Null
git clone https://github.com/JY0xLU/codexgo.git "$CodexHome\skills\codexgo"
```

## Usage Flow

<p align="center">
  <img src="assets/codexgo-usage.png" alt="codexgo recovery flow" width="100%">
</p>

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
--lookback <n>       Nearby timeline entries to include. Defaults to 6.
--format <fmt>       text or json. Defaults to text.
```

## Privacy

- Reads only local Codex state and session records.
- Does not upload conversations or call the network.
- Does not write to Codex databases.
- Does not modify project files.
- Uses deterministic rules, not another LLM agent.

## Runtime

- Python 3.10+
- Local Codex data directory
- No third-party Python dependencies

## Boundaries

- No local session record means there is nothing to recover.
- Codex local state format changes may require parser updates.
- Recovery works best inside the same workspace or Git repository.
- Low-signal detection is rule-based, not full semantic understanding.

## Star History

<a href="https://www.star-history.com/#JY0xLU/codexgo&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
  </picture>
</a>

## Development

```bash
pytest
```

## License

Apache-2.0
