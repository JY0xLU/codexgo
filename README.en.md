<p align="center">
  <img src="assets/codexgo-logo.png" alt="codexgo logo" width="132">
</p>

<h1 align="center">codexgo</h1>

<p align="center">
  <strong>A tiny note card for the next Codex thread.</strong><br>
  When the old thread is gone, codexgo checks the local black box before you explain everything again. (｀・ω・´)
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

## In One Sentence

`codexgo` is a small Codex skill. It does not write code for you, search the web, or invent memory. Its only job is to prepare the next useful instruction for a fresh Codex thread by reading the local traces left by earlier sessions.

Think of it as a local black-box reader. The thread is gone, but the clues are still on disk.

## When To Use It

Use it when you already explained the task, Codex started working, and then the session became unusable. You can always retype the full task manually, but that is slow and easy to get subtly wrong.

At the start of the new thread, type:

```text
codexgo
```

It looks near the current workspace, finds recent Codex session records, and returns the instruction that is most useful for continuing the work.

## What It Returns

`codexgo` is not trying to replay the whole conversation. It produces a continuation card:

| Situation | What it returns |
| --- | --- |
| The last message was already a concrete task | That task |
| The last message was `continue` / `go on` / `继续` | The earlier task it points to |
| The last message was `ok` / `yes` / `好的` | The assistant proposal you accepted |
| The last message added extra detail | The merged task plus supplement |
| The request depends on older context | Supporting context nearby |
| You want automation | JSON fields for downstream tools |

If it cannot find a credible continuation, it says so instead of making one up.

## What It Reads

`codexgo` is local and read-only. It opens Codex state indexes and session timeline files, then turns them into one continuation trail:

| Clue | Purpose |
| --- | --- |
| `state_*.sqlite` | Finds recent Codex threads, workspace paths, and update times |
| rollout JSONL | Reads user messages, assistant replies, tool events, and interrupted turns |
| current `--cwd` | Decides which workspace or Git repo should be preferred |
| recent user messages | Separates concrete tasks from short acknowledgements and supplements |
| previous assistant proposal | Recovers the plan you accepted when your last reply was only `ok` / `好的` |

By default, it skips the current thread. That prevents the fresh `codexgo` trigger itself from becoming the recovered request.

## Workspace Matching

The match is not limited to one exact path. `codexgo` supports several scopes, and `auto` is the default:

| Scope | Useful when |
| --- | --- |
| `exact` | Only the same workspace path should count |
| `repo` | Any thread inside the same Git repository is relevant |
| `tree` | Parent and child directories may both contain useful history |
| `auto` | Let codexgo start narrow and widen when needed |

This matters in the Codex app because you may start a task at the repo root and continue from a nested folder later.

## Noise Handling

The last line before a break is often not the task itself. `codexgo` treats those messages as signposts:

| Type | Examples | Behavior |
| --- | --- | --- |
| Continue trigger | `continue`, `go on`, `继续`, `jixu` | Walks back to the previous concrete task |
| Agreement | `ok`, `yes`, `好的`, `可以` | Recovers the assistant proposal you accepted |
| Skill trigger | `codexgo`, `golast` | Does not treat the trigger as the task |
| Interrupted turn marker | `<turn_aborted>` | Ignores it |
| Empty shell thread | Only system text, AGENTS notes, or triggers | Skips it and keeps searching |

It also watches for references that need earlier context, such as "continue the idea I accepted" or "follow the previous decision". When it has to look upward, `context_expanded_upward` is set in JSON.

## Continuation Card Fields

JSON output is useful when you want to audit or automate the handoff:

| Field | Meaning |
| --- | --- |
| `status` | `ok` or an error state |
| `current_cwd` | Workspace passed to this run |
| `scope_used` | Search scope actually used |
| `matched_cwd` | Workspace path from the recovered thread |
| `thread_id` | Matching Codex thread |
| `literal_last_user_message` | Last user message exactly as seen in the timeline |
| `resolved_request` | Instruction to continue with |
| `resolved_source` | Whether it came from a user task, assistant proposal, supplement, etc. |
| `decision_basis_message` | The proposal or comparison that explains an accepted decision |
| `supporting_context` | Nearby context attached to resolve vague references |
| `recent_user_messages` | Recent user messages for quick human inspection |
| `context_expanded_upward` | Whether older context was pulled in |

Plain text is easier for humans; JSON is easier for tools.

## Put It In Codex

`codexgo` is a Codex skill, not a pip package. Put this repository inside Codex's `skills/codexgo` directory, then restart Codex.

### Codex App

The Codex desktop app may use a dedicated `CODEX_HOME`. On this Windows setup, it is often `D:\CodexData\.codex`; regular CLI setups usually use `~/.codex`.

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } elseif (Test-Path "D:\CodexData\.codex") { "D:\CodexData\.codex" } else { "$HOME\.codex" }
New-Item -ItemType Directory -Force "$CodexHome\skills" | Out-Null
git clone https://github.com/JY0xLU/codexgo.git "$CodexHome\skills\codexgo"
```

Fully restart the Codex app so it can rescan local skills. Tiny note courier needs to be discovered first. (｡•̀ᴗ-)✧

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

You can also run the script directly for debugging or automation:

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

JSON example:

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
    "continue the idea I accepted"
  ]
}
```

## Local Rules

- Reads only Codex state and session files on your own machine.
- Does not upload conversations, call the network, or write back to Codex data.
- Does not edit your project unless another automation consumes its output.
- Uses deterministic rules; it is not another LLM agent.

In plain words: it is not cloud memory. It is a bookmark with a flashlight.

## Runtime Notes

- Python 3.10+
- A local Codex data directory
- No third-party Python dependencies

## Boundaries

- If there is no local session record, there is nothing to read.
- If Codex changes its local state format, the parser may need an update.
- It works best inside the same workspace or Git repository.
- It avoids short low-signal replies, but it is not an all-knowing language judge.

## Star History

<a href="https://www.star-history.com/#JY0xLU/codexgo&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
  </picture>
</a>

## Development

Run tests:

```bash
pytest
```

## License

Apache-2.0
