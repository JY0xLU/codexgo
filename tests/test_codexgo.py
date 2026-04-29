import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "codexgo.py"
TEST_WORK = ROOT / ".test-work"


def make_case_dir() -> Path:
    case_dir = TEST_WORK / uuid4().hex
    case_dir.mkdir(parents=True)
    return case_dir


def write_rollout(path: Path, messages: list[tuple[str, str]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for role, text in messages:
            if role == "user":
                record = {
                    "type": "event_msg",
                    "payload": {"type": "user_message", "message": text},
                }
            else:
                record = {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": text}],
                    },
                }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def make_codex_home(tmp_path: Path, cwd: Path, messages: list[tuple[str, str]]) -> Path:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    rollout = tmp_path / "rollout.jsonl"
    write_rollout(rollout, messages)
    db_path = codex_home / "state_5.sqlite"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE threads (id TEXT, cwd TEXT, title TEXT, first_user_message TEXT, updated_at INTEGER, rollout_path TEXT)"
        )
        conn.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?)",
            ("thread-1", str(cwd), "fixture", messages[0][1], 100, str(rollout)),
        )
        conn.commit()
    finally:
        conn.close()
    return codex_home


def run_codexgo(tmp_path: Path, cwd: Path, messages: list[tuple[str, str]]) -> dict:
    codex_home = make_codex_home(tmp_path, cwd, messages)
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cwd",
            str(cwd),
            "--codex-home",
            str(codex_home),
            "--format",
            "json",
            "--no-skip-current",
        ],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_recovers_last_normal_user_request() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [("user", "implement the parser"), ("assistant", "I will do that.")],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["resolved_request"] == "implement the parser"
    assert result["resolved_source"] == "user_message"


def test_codexgo_recovers_previous_real_request() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "refactor the timeline parser"),
                ("assistant", "I have the plan."),
                ("user", "继续"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["resolved_request"] == "refactor the timeline parser"
    assert result["resolved_source"] == "user_message"


def test_agreement_recovers_assistant_suggestion() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "make the tool tiny"),
                ("assistant", "I will keep one script and one SKILL.md."),
                ("user", "ok"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["resolved_request"] == "I will keep one script and one SKILL.md."
    assert result["resolved_source"] == "assistant_suggestion"


def test_supplement_merges_previous_context() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "recover the previous Codex task"),
                ("assistant", "I will parse the local thread database."),
                ("user", "补充：输出 json"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert "I will parse the local thread database." in result["resolved_request"]
    assert "补充：输出 json" in result["resolved_request"]
    assert result["resolved_source"] == "supplement_plus_previous_assistant"
