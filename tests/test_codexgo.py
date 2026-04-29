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


def make_codex_home_with_threads(
    tmp_path: Path, threads: list[tuple[str, Path, int, list[tuple[str, str]]]]
) -> Path:
    codex_home = tmp_path / "codex-home"
    codex_home.mkdir()
    db_path = codex_home / "state_5.sqlite"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE threads (id TEXT, cwd TEXT, title TEXT, first_user_message TEXT, updated_at INTEGER, rollout_path TEXT)"
        )
        for index, (thread_id, cwd, updated_at, messages) in enumerate(threads, start=1):
            rollout = tmp_path / f"rollout-{index}.jsonl"
            write_rollout(rollout, messages)
            conn.execute(
                "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?)",
                (thread_id, str(cwd), "fixture", messages[0][1], updated_at, str(rollout)),
            )
        conn.commit()
    finally:
        conn.close()
    return codex_home


def run_codexgo(tmp_path: Path, cwd: Path, messages: list[tuple[str, str]], extra_args: list[str] | None = None) -> dict:
    codex_home = make_codex_home(tmp_path, cwd, messages)
    command = [
        sys.executable,
        str(SCRIPT),
        "--cwd",
        str(cwd),
        "--codex-home",
        str(codex_home),
        "--format",
        "json",
        "--no-skip-current",
    ]
    if extra_args:
        command.extend(extra_args)
    completed = subprocess.run(
        command,
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


def test_auto_scope_does_not_recover_parent_workspace_thread_from_child_directory() -> None:
    tmp_path = make_case_dir()
    try:
        workspace = tmp_path / "workspace"
        child = workspace / "project"
        child.mkdir(parents=True)
        codex_home = make_codex_home(
            tmp_path,
            workspace,
            [("user", "recover the parent workspace task"), ("assistant", "I will do that.")],
        )
        command = [
            sys.executable,
            str(SCRIPT),
            "--cwd",
            str(child),
            "--codex-home",
            str(codex_home),
            "--format",
            "json",
            "--no-skip-current",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
        explicit_tree = subprocess.run(
            command + ["--scope", "tree"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        result = json.loads(explicit_tree.stdout)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert completed.returncode == 1
    assert "No previous Codex thread found" in completed.stdout
    assert result["scope_used"] == "tree"
    assert result["matched_cwd"] == str(child)
    assert result["thread_cwd"] == str(workspace)
    assert result["resolved_request"] == "recover the parent workspace task"


def test_tree_scope_skips_current_child_thread_by_default() -> None:
    tmp_path = make_case_dir()
    try:
        workspace = tmp_path / "workspace"
        child = workspace / "project"
        child.mkdir(parents=True)
        codex_home = make_codex_home_with_threads(
            tmp_path,
            [
                ("current", child, 200, [("user", "codexgo"), ("assistant", "Recovering now.")]),
                ("previous", workspace, 100, [("user", "resume the interrupted build"), ("assistant", "On it.")]),
            ],
        )
        command = [
            sys.executable,
            str(SCRIPT),
            "--cwd",
            str(child),
            "--codex-home",
            str(codex_home),
            "--format",
            "json",
            "--scope",
            "tree",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=True)
        result = json.loads(completed.stdout)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["scope_used"] == "tree"
    assert result["resolved_request"] == "resume the interrupted build"
    assert result["thread_id"] == "previous"
    assert result["thread_cwd"] == str(workspace)


def test_skips_archived_thread_without_recoverable_user_content() -> None:
    tmp_path = make_case_dir()
    try:
        workspace = tmp_path / "workspace"
        child = workspace / "project"
        child.mkdir(parents=True)
        codex_home = make_codex_home_with_threads(
            tmp_path,
            [
                ("current", child, 300, [("user", "codexgo"), ("assistant", "Recovering now.")]),
                (
                    "empty-archive",
                    workspace,
                    200,
                    [
                        ("user", "# AGENTS.md instructions for C:\\work"),
                        ("user", "<turn_aborted>"),
                        ("user", "codexgo"),
                        ("user", "啥意思呢"),
                    ],
                ),
                ("previous", workspace, 100, [("user", "continue the saved release task"), ("assistant", "On it.")]),
            ],
        )
        command = [
            sys.executable,
            str(SCRIPT),
            "--cwd",
            str(child),
            "--codex-home",
            str(codex_home),
            "--format",
            "json",
            "--scope",
            "tree",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=True)
        result = json.loads(completed.stdout)
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["thread_id"] == "previous"
    assert result["resolved_request"] == "continue the saved release task"


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


def test_pinyin_continue_is_low_signal() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "finish the App install smoke test"),
                ("assistant", "I will verify the installed skill."),
                ("user", "ji xu"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["resolved_request"] == "finish the App install smoke test"
    assert result["ambiguity_hints"] == []


def test_skill_trigger_words_are_low_signal_inside_previous_thread() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "finish the release checklist"),
                ("assistant", "I will continue from the checklist."),
                ("user", "codexgo"),
                ("assistant", "Recovered the previous task."),
                ("user", "啥意思呢"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["resolved_request"] == "finish the release checklist"


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


def test_pinyin_agreement_recovers_assistant_suggestion() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "choose the smallest local-only implementation"),
                ("assistant", "I will keep it as one Python file and one skill file."),
                ("user", "haode"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["resolved_request"] == "I will keep it as one Python file and one skill file."
    assert result["resolved_source"] == "assistant_suggestion"


def test_turn_aborted_is_ignored_when_reading_timeline() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "recover the real request"),
                ("assistant", "Working on it."),
                ("user", "<turn_aborted>"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["literal_last_user_message"] == "recover the real request"
    assert result["resolved_request"] == "recover the real request"


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


def test_reference_expands_supporting_context_upward() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "恢复链路要覆盖：读取状态库、解析时间线、输出结果。"),
                ("assistant", "我会按这条恢复链路推进。"),
                ("user", "先做 CLI。"),
                ("assistant", "CLI 已经完成。"),
                ("user", "继续这个方向"),
            ],
            ["--lookback", "1"],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["needs_more_context"] is True
    assert result["context_expanded_upward"] is True
    assert result["supporting_context"][0]["text"] == "恢复链路要覆盖：读取状态库、解析时间线、输出结果。"


def test_uncertain_assistant_plan_expands_to_decision_basis_on_agreement() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "对比 SQLite、本地 JSON、远程 API，选择一个最小恢复实现。"),
                ("assistant", "我先按上一条方案推进，如果我理解错了再调整。"),
                ("user", "ok"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["resolved_source"] == "assistant_suggestion_with_decision_basis"
    assert result["decision_basis_message"] == "对比 SQLite、本地 JSON、远程 API，选择一个最小恢复实现。"
    assert "uncertainty" in result["ambiguity_hints"]
    assert "reference" in result["ambiguity_hints"]


def test_backend_choice_reference_expands_to_candidate_list() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "后端候选：ZLMediaKit / MediaMTX / SRS，选一个保持本地可跑。"),
                ("assistant", "我会先比较这几个后端。"),
                ("user", "这个后端方案继续"),
            ],
            ["--lookback", "1"],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["needs_more_context"] is True
    assert result["context_expanded_upward"] is True
    assert "backend_choice" in result["ambiguity_hints"]
    assert result["supporting_context"][0]["text"] == "后端候选：ZLMediaKit / MediaMTX / SRS，选一个保持本地可跑。"


def test_agreement_merges_decision_basis_for_ambiguous_assistant_suggestion() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "对比三种方案：SQLite、本地 JSON、远程 API，选择一个最小实现。"),
                ("assistant", "建议按上一条方案：用 SQLite 做只读恢复。"),
                ("user", "ok"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["decision_basis_message"] == "对比三种方案：SQLite、本地 JSON、远程 API，选择一个最小实现。"
    assert "Current execution slice:" in result["resolved_request"]
    assert "用 SQLite 做只读恢复" in result["resolved_request"]
    assert result["resolved_source"] == "assistant_suggestion_with_decision_basis"


def test_supplement_merges_decision_basis_for_previous_assistant_context() -> None:
    tmp_path = make_case_dir()
    try:
        cwd = tmp_path / "work"
        cwd.mkdir()

        result = run_codexgo(
            tmp_path,
            cwd,
            [
                ("user", "选择输出形态：text、json、supporting_context，保持小工具实现。"),
                ("assistant", "前面的方案可以，先补 json 输出。"),
                ("user", "补充：同时更新 README"),
            ],
        )
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)

    assert result["decision_basis_message"] == "选择输出形态：text、json、supporting_context，保持小工具实现。"
    assert "Current execution slice:" in result["resolved_request"]
    assert "补充：同时更新 README" in result["resolved_request"]
    assert result["resolved_source"] == "supplement_plus_decision_basis_and_previous_assistant"
