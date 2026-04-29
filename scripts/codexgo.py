#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


LOW_SIGNAL = {
    "continue",
    "goon",
    "keepgoing",
    "resume",
    "carryon",
    "继续",
    "继续吧",
    "接着",
    "接着做",
}

AGREEMENTS = {
    "ok",
    "okay",
    "yes",
    "yep",
    "sure",
    "agreed",
    "doit",
    "goahead",
    "好",
    "好的",
    "可以",
    "同意",
    "行",
}

SUPPLEMENT_STARTS = (
    "补充",
    "补一下",
    "补充说明",
    "再补充",
    "另外",
    "还有",
    "顺便",
    "ps",
    "p.s",
    "additional",
    "additionally",
    "one more thing",
)

REFERENCE_WORDS = (
    "do that",
    "do this",
    "that plan",
    "this plan",
    "same as above",
    "above",
    "continue that",
    "that approach",
    "previous approach",
    "这个",
    "那个",
    "上面",
    "前面",
    "同上",
    "这个方案",
    "按这个",
    "按上面",
    "刚才那个",
    "前面的方案",
    "上一条方案",
    "继续这个方向",
)

AMBIGUOUS_COUNT_TERMS = (
    "两端",
    "三端",
    "两种",
    "三种",
    "两个",
    "三个",
    "这两种",
    "这三种",
    "这两个",
    "这三个",
    "那两种",
    "那三种",
    "那两个",
    "那三个",
)

CONCRETE_HINTS = (
    "/",
    "\\",
    "://",
    ".md",
    ".py",
    ".ts",
    ".js",
    "`",
    "fix",
    "update",
    "implement",
    "refactor",
    "read",
    "修复",
    "更新",
    "实现",
    "重构",
    "读取",
)

SELECTION_HINTS = (
    "choose",
    "select",
    "decide",
    "compare",
    "which",
    "pick",
    "选",
    "选择",
    "选型",
    "择优",
    "对比",
    "比较",
    "哪个",
)


@dataclass
class Thread:
    id: str
    cwd: str
    title: str
    first_user_message: str
    updated_at: int
    rollout_path: str


@dataclass
class Entry:
    role: str
    text: str


@dataclass
class Resolved:
    literal_last_user_message: str
    resolved_request: str
    resolved_source: str
    resolved_index: int
    context_index: int
    assistant_message_before_last_user: str = ""
    previous_context_message: str = ""
    decision_basis_message: str = ""
    needs_more_context: bool = False
    ambiguity_hints: tuple[str, ...] = ()


def compact(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if ch.isalnum())


def clean_user_text(text: str) -> str:
    value = text.replace("\r\n", "\n").strip()
    if not value:
        return ""
    if value.lower() in {"codex", "assistant", "claude"}:
        return ""
    if value.startswith("# AGENTS.md instructions for "):
        return ""
    return value


def norm_path(value: str) -> str:
    value = os.path.expanduser(value)
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normcase(os.path.normpath(value))


def git_root(cwd: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    root = result.stdout.decode("utf-8", errors="replace").strip()
    return root or None


def find_state_db(codex_home: Path) -> Path:
    direct = codex_home / "state_5.sqlite"
    if direct.exists():
        return direct
    candidates = sorted(
        codex_home.glob("state_*.sqlite"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"No Codex state_*.sqlite found in {codex_home}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recover the previous actionable Codex request for this workspace."
    )
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--scope", choices=("auto", "exact", "repo", "tree"), default="auto")
    parser.add_argument("--skip-current", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--recent", type=int, default=3)
    parser.add_argument("--lookback", type=int, default=6)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args()


def read_threads(conn: sqlite3.Connection) -> list[Thread]:
    rows = conn.execute(
        """
        SELECT id, cwd, title, first_user_message, updated_at, rollout_path
        FROM threads
        WHERE rollout_path IS NOT NULL AND rollout_path != ''
        ORDER BY updated_at DESC
        LIMIT 2000
        """
    ).fetchall()
    return [
        Thread(
            id=str(row[0]),
            cwd=str(row[1]),
            title=str(row[2] or ""),
            first_user_message=str(row[3] or ""),
            updated_at=int(row[4] or 0),
            rollout_path=str(row[5] or ""),
        )
        for row in rows
    ]


def target_paths(cwd: str, scope: str) -> list[tuple[str, str]]:
    root = git_root(cwd)
    if scope == "exact":
        return [("exact", cwd)]
    if scope == "repo":
        return [("repo", root)] if root else []
    if scope == "tree":
        return [("tree", cwd)]
    targets = [("exact", cwd)]
    if root:
        targets.append(("repo", root))
    targets.append(("tree", cwd))
    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for label, path in targets:
        key = (label, norm_path(path))
        if key not in seen:
            seen.add(key)
            deduped.append((label, path))
    return deduped


def thread_matches(label: str, thread_cwd: str, target: str) -> bool:
    left = norm_path(thread_cwd)
    right = norm_path(target)
    if label == "tree":
        return left == right or left.startswith(right.rstrip("\\/") + os.sep)
    return left == right


def locate_thread(codex_home: Path, cwd: str, scope: str, skip_current: bool) -> tuple[str, str, Thread]:
    db_path = find_state_db(codex_home)
    normalized_cwd = norm_path(cwd)
    with sqlite3.connect(db_path) as conn:
        threads = read_threads(conn)
    for label, target in target_paths(cwd, scope):
        matches = [
            thread
            for thread in threads
            if thread.rollout_path and Path(thread.rollout_path).exists() and thread_matches(label, thread.cwd, target)
        ]
        if skip_current and label != "tree" and norm_path(target) == normalized_cwd and matches:
            matches = matches[1:]
        if matches:
            return label, target, matches[0]
    raise LookupError(f"No previous Codex thread found for cwd={cwd}")


def assistant_text(payload: dict) -> str:
    chunks: list[str] = []
    for item in payload.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "output_text":
            chunks.append(str(item.get("text") or ""))
    return "\n".join(part for part in chunks if part).strip()


def user_text(payload: dict) -> str:
    chunks: list[str] = []
    for item in payload.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "input_text":
            chunks.append(str(item.get("text") or ""))
    return "\n".join(part for part in chunks if part).strip()


def parse_rollout(path: Path) -> list[Entry]:
    entries: list[Entry] = []
    fallback_users: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            payload = record.get("payload") or {}
            if record.get("type") == "event_msg" and payload.get("type") == "user_message":
                text = clean_user_text(str(payload.get("message") or ""))
                if text:
                    entries.append(Entry("user", text))
                continue
            if record.get("type") != "response_item" or payload.get("type") != "message":
                continue
            role = payload.get("role")
            if role == "assistant":
                text = assistant_text(payload)
                if text:
                    entries.append(Entry("assistant", text))
            elif role == "user":
                text = clean_user_text(user_text(payload))
                if text:
                    fallback_users.append(text)
    if not any(entry.role == "user" for entry in entries):
        entries.extend(Entry("user", text) for text in fallback_users)
    return dedupe(entries)


def dedupe(entries: list[Entry]) -> list[Entry]:
    result: list[Entry] = []
    last: tuple[str, str] | None = None
    for entry in entries:
        key = (entry.role, entry.text)
        if key != last:
            result.append(entry)
        last = key
    return result


def is_low_signal(text: str) -> bool:
    folded = compact(text)
    return not folded or folded in LOW_SIGNAL or len(folded) <= 4


def is_agreement(text: str) -> bool:
    return compact(text) in AGREEMENTS


def is_supplement(text: str) -> bool:
    folded = compact(text)
    return any(folded.startswith(compact(prefix)) for prefix in SUPPLEMENT_STARTS)


def has_concrete_hint(text: str) -> bool:
    lower = text.lower()
    if has_list(text):
        return True
    if count_inline_candidates(text) >= 3:
        return True
    return any(hint in lower for hint in CONCRETE_HINTS if hint.isascii()) or any(
        hint in text for hint in CONCRETE_HINTS if not hint.isascii()
    )


def has_list(text: str) -> bool:
    return re.search(r"(^|\n)\s*(?:[-*]|\d+[.)、])\s+", text) is not None


def count_inline_candidates(text: str) -> int:
    candidates = re.split(r"\s*(?:/|,|，|、|\|| vs | VS | versus | 和 | 与 | or )\s*", text)
    return sum(1 for candidate in candidates if re.search(r"[A-Za-z0-9\u4e00-\u9fff]{2,}", candidate))


def has_selection_hint(text: str) -> bool:
    lower = text.lower()
    return any(hint in lower for hint in SELECTION_HINTS if hint.isascii()) or any(
        hint in text for hint in SELECTION_HINTS if not hint.isascii()
    )


def is_decision_basis(text: str) -> bool:
    if not has_selection_hint(text):
        return False
    return has_list(text) or count_inline_candidates(text) >= 3


def ambiguity_hints(text: str) -> tuple[str, ...]:
    hints: list[str] = []
    lower = text.lower()
    if is_low_signal(text):
        hints.append("low_signal")
    if is_agreement(text):
        hints.append("agreement")
    if any(word in lower for word in REFERENCE_WORDS if word.isascii()) or any(
        word in text for word in REFERENCE_WORDS if not word.isascii()
    ):
        hints.append("reference")
    if any(term in text for term in AMBIGUOUS_COUNT_TERMS):
        hints.append("count_shorthand")
    if ("方案" in text or "plan" in lower) and not has_concrete_hint(text):
        hints.append("plan_reference")
    return tuple(dict.fromkeys(hints))


def combine_ambiguity_hints(*texts: str) -> tuple[str, ...]:
    combined: list[str] = []
    for text in texts:
        if not text.strip():
            continue
        for hint in ambiguity_hints(text):
            if hint not in combined:
                combined.append(hint)
    return tuple(combined)


def needs_context(text: str) -> bool:
    hints = ambiguity_hints(text)
    if "low_signal" in hints or "agreement" in hints:
        return True
    if "count_shorthand" in hints:
        return True
    if "reference" in hints or "plan_reference" in hints:
        return not has_concrete_hint(text)
    return False


def previous_context(entries: list[Entry], before_index: int) -> tuple[int, Entry] | None:
    for index in range(before_index - 1, -1, -1):
        entry = entries[index]
        if entry.role == "assistant":
            return index, entry
        if entry.role == "user" and not (is_low_signal(entry.text) or is_agreement(entry.text) or is_supplement(entry.text)):
            return index, entry
    return None


def previous_decision_basis(entries: list[Entry], before_index: int, max_scan: int = 32) -> tuple[int, Entry] | None:
    floor = max(0, before_index - max_scan)
    for index in range(before_index - 1, floor - 1, -1):
        entry = entries[index]
        if entry.role == "user" and is_decision_basis(entry.text):
            return index, entry
    return None


def merge_decision_basis(decision_basis: str, current: str) -> str:
    if not decision_basis:
        return current
    if not current:
        return decision_basis
    return f"{decision_basis}\n\nCurrent execution slice:\n{current}"


def entry_resolves_ambiguity(text: str, hints: tuple[str, ...]) -> bool:
    if not hints:
        return False
    if "count_shorthand" in hints and (has_list(text) or count_inline_candidates(text) >= 3):
        return True
    if ("reference" in hints or "plan_reference" in hints) and has_concrete_hint(text):
        return True
    return False


def explanatory_context_index(entries: list[Entry], anchor_index: int, hints: tuple[str, ...], max_scan: int) -> int | None:
    if anchor_index < 0 or not hints:
        return None
    floor = max(0, anchor_index - max_scan)
    best_index: int | None = None
    for index in range(anchor_index, floor - 1, -1):
        entry = entries[index]
        if not entry.text.strip():
            continue
        if entry_resolves_ambiguity(entry.text, hints):
            best_index = index
            if entry.role == "user" or has_list(entry.text):
                break
    return best_index


def resolve(entries: list[Entry], first_user_message: str) -> Resolved:
    user_indexes = [index for index, entry in enumerate(entries) if entry.role == "user"]
    if not user_indexes:
        fallback = clean_user_text(first_user_message)
        return Resolved(
            literal_last_user_message=fallback,
            resolved_request=fallback,
            resolved_source="first_user_message",
            resolved_index=-1,
            context_index=-1,
            needs_more_context=needs_context(fallback),
            ambiguity_hints=ambiguity_hints(fallback),
        )

    last_user_index = user_indexes[-1]
    last_user = entries[last_user_index].text

    if is_agreement(last_user):
        for index in range(last_user_index - 1, -1, -1):
            entry = entries[index]
            if entry.role == "assistant":
                decision = previous_decision_basis(entries, index)
                decision_index = index
                decision_text = ""
                resolved_text = entry.text
                if decision is not None and needs_context(entry.text):
                    decision_index, decision_entry = decision
                    decision_text = decision_entry.text
                    resolved_text = merge_decision_basis(decision_text, entry.text)
                return Resolved(
                    literal_last_user_message=last_user,
                    resolved_request=resolved_text,
                    resolved_source="assistant_suggestion_with_decision_basis" if decision_text else "assistant_suggestion",
                    resolved_index=index,
                    context_index=decision_index,
                    assistant_message_before_last_user=entry.text,
                    previous_context_message=resolved_text,
                    decision_basis_message=decision_text,
                    needs_more_context=needs_context(resolved_text),
                    ambiguity_hints=combine_ambiguity_hints(decision_text, entry.text),
                )

    if is_supplement(last_user):
        context = previous_context(entries, last_user_index)
        if context is not None:
            context_index, entry = context
            decision_text = ""
            base_context = entry.text
            if entry.role == "assistant":
                decision = previous_decision_basis(entries, context_index)
                if decision is not None and needs_context(entry.text):
                    decision_index, decision_entry = decision
                    decision_text = decision_entry.text
                    base_context = merge_decision_basis(decision_text, entry.text)
                    context_index = decision_index
            merged = f"{base_context}\n\nSupplement:\n{last_user}"
            return Resolved(
                literal_last_user_message=last_user,
                resolved_request=merged,
                resolved_source=(
                    f"supplement_plus_decision_basis_and_previous_{entry.role}"
                    if decision_text
                    else f"supplement_plus_previous_{entry.role}"
                ),
                resolved_index=last_user_index,
                context_index=context_index,
                assistant_message_before_last_user=entry.text if entry.role == "assistant" else "",
                previous_context_message=base_context,
                decision_basis_message=decision_text,
                needs_more_context=needs_context(base_context) or needs_context(last_user),
                ambiguity_hints=combine_ambiguity_hints(base_context, last_user),
            )

    resolved_index = last_user_index
    resolved_text = last_user
    if is_low_signal(last_user):
        for index in reversed(user_indexes[:-1]):
            candidate = entries[index].text
            if not is_low_signal(candidate) and not is_agreement(candidate):
                resolved_index = index
                resolved_text = candidate
                break

    return Resolved(
        literal_last_user_message=last_user,
        resolved_request=resolved_text,
        resolved_source="user_message",
        resolved_index=resolved_index,
        context_index=resolved_index,
        needs_more_context=needs_context(resolved_text),
        ambiguity_hints=ambiguity_hints(resolved_text),
    )


def last_meaningful(entries: list[Entry]) -> Entry:
    for entry in reversed(entries):
        if entry.text.strip():
            return entry
    return Entry("unknown", "")


def supporting_context(entries: list[Entry], resolved: Resolved, lookback: int) -> list[dict[str, str]]:
    context, _ = collect_supporting_context(entries, resolved, lookback)
    return context


def collect_supporting_context(entries: list[Entry], resolved: Resolved, lookback: int) -> tuple[list[dict[str, str]], bool]:
    if resolved.resolved_index < 0:
        return [], False
    anchor = min(resolved.context_index, resolved.resolved_index)
    effective_lookback = max(lookback, 0)
    start = max(0, anchor - effective_lookback)
    expanded = False
    if resolved.needs_more_context or resolved.ambiguity_hints:
        explanatory_index = explanatory_context_index(
            entries,
            anchor,
            resolved.ambiguity_hints,
            max(effective_lookback * 4, 12),
        )
        if explanatory_index is not None and explanatory_index < start:
            start = explanatory_index
            expanded = True
    return [{"role": entry.role, "text": entry.text} for entry in entries[start : resolved.resolved_index + 1]], expanded


def recent_user_messages(entries: list[Entry], count: int) -> list[str]:
    messages = [entry.text for entry in entries if entry.role == "user"]
    return messages[-count:] if count > 0 else []


def local_time(timestamp: int) -> str:
    if timestamp > 10_000_000_000:
        timestamp //= 1000
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except (OSError, OverflowError, ValueError):
        return str(timestamp)


def build_result(args: argparse.Namespace) -> dict[str, object]:
    cwd = os.path.abspath(args.cwd)
    scope, matched_cwd, thread = locate_thread(Path(args.codex_home), cwd, args.scope, args.skip_current)
    entries = parse_rollout(Path(thread.rollout_path))
    resolved = resolve(entries, thread.first_user_message)
    tail = last_meaningful(entries)
    context, context_expanded_upward = collect_supporting_context(entries, resolved, args.lookback)
    return {
        "status": "ok",
        "current_cwd": cwd,
        "scope_used": scope,
        "matched_cwd": matched_cwd,
        "thread_id": thread.id,
        "thread_title": thread.title,
        "updated_at_local": local_time(thread.updated_at),
        "rollout_path": thread.rollout_path,
        "literal_last_user_message": resolved.literal_last_user_message,
        "last_conversation_role": tail.role,
        "last_conversation_content": tail.text,
        "resolved_request": resolved.resolved_request,
        "resolved_source": resolved.resolved_source,
        "assistant_message_before_last_user": resolved.assistant_message_before_last_user,
        "previous_context_message": resolved.previous_context_message,
        "decision_basis_message": resolved.decision_basis_message,
        "needs_more_context": resolved.needs_more_context,
        "ambiguity_hints": list(resolved.ambiguity_hints),
        "context_expanded_upward": context_expanded_upward,
        "supporting_context": context,
        "recent_user_messages": recent_user_messages(entries, args.recent),
    }


def render_text(result: dict[str, object]) -> str:
    lines = [
        "Recovered Codex request",
        f"- matched workspace: {result['matched_cwd']}",
        f"- thread: {result['thread_title']} ({result['thread_id']})",
        f"- updated: {result['updated_at_local']}",
        f"- source: {result['resolved_source']}",
        f"- needs more context: {result['needs_more_context']}",
        f"- context expanded upward: {result.get('context_expanded_upward', False)}",
        "",
        "Last conversation content:",
        f"[{result['last_conversation_role']}] {result['last_conversation_content'] or '(empty)'}",
        "",
        "Literal last user message:",
        str(result["literal_last_user_message"] or "(empty)"),
        "",
        "Resolved request:",
        str(result["resolved_request"] or "(empty)"),
    ]
    decision_basis = str(result.get("decision_basis_message") or "")
    if decision_basis:
        lines.extend(["", "Decision basis message:", decision_basis])
    context = result.get("supporting_context") or []
    if context:
        lines.append("")
        lines.append("Supporting context:")
        for index, item in enumerate(context, start=1):
            lines.append(f"{index}. [{item['role']}] {item['text']}")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        result = build_result(args)
    except Exception as exc:
        if args.format == "json":
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"codexgo failed: {exc}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
