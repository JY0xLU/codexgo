---
name: "codexgo"
description: "Recover the previous actionable Codex request for the current workspace at the start of a fresh session after compaction, crash, or context loss. Use when the user types `codexgo` as an explicit skill request, asks to recover the previous Codex session, or asks to continue after a compact/crash break."
---

# codexgo

Use this skill only when the user explicitly wants to recover the previous Codex session for the current workspace, usually at the start of a fresh session after compaction or crash.

Do not auto-trigger this skill later in a normal active conversation from vague phrases like "continue", "继续", or "接着做". In an active thread, prefer the current conversation context unless the user clearly names this skill.

## Run

Run:

```bash
python scripts/codexgo.py --cwd "$PWD" --format json
```

On Windows PowerShell, use the current working directory from the shell context:

```powershell
py scripts/codexgo.py --cwd . --format json
```

## Resume Work

Read these fields:

- `resolved_request`: the best task to continue now
- `literal_last_user_message`: the exact last user message from the previous thread
- `last_conversation_content`: the last meaningful conversation item
- `resolved_source`: whether the request came from a user message, assistant suggestion, supplement, or fallback
- `needs_more_context`: whether the recovered text still looks ambiguous
- `supporting_context`: nearby timeline entries

If the user wants execution, briefly state the recovered request and continue working immediately.
