# continue

中文 | [English](#english)

`continue` 是一个很小的 Codex 恢复工具。它适合在 Codex 因为 compaction、崩溃或上下文丢失而中断后，帮你从本地 Codex 会话记录里找回上一轮真正要继续的任务。

它只读本地文件，不上传对话，不修改 Codex 数据库。

## 使用场景

当 Codex 会话断掉后，在同一个项目目录里重新打开 Codex，然后输入：

```text
continue
```

这个 skill 会读取本地 Codex 状态数据库，找到当前工作区对应的上一个 thread，解析 rollout 记录，然后输出最可能需要继续执行的请求。

## 它会处理什么

- 最后一条用户消息是真正的任务：直接返回这条任务。
- 最后一条用户消息是 `continue`、`go on`、`继续` 等低信息回复：向前找到上一条真实请求。
- 最后一条用户消息是 `ok`、`yes`、`好的` 等同意回复：恢复你刚刚同意的助手方案。
- 最后一条用户消息是 `补充：...` 这类补充说明：把补充内容和前面的上下文合并。
- 输出支持普通文本和 JSON。

## 安装

把仓库 clone 到 Codex 的 skills 目录：

```bash
git clone https://github.com/JY0xLU/continue.git ~/.codex/skills/continue
```

然后重启 Codex。之后在新会话开头输入 `continue` 即可。

## 命令行

```bash
python scripts/continue.py --cwd . --format text
python scripts/continue.py --cwd . --format json
```

参数：

```text
--cwd <path>         工作区路径，默认是当前目录。
--codex-home <path>  Codex 数据目录，默认是 CODEX_HOME 或 ~/.codex。
--scope <mode>       搜索范围：auto、exact、repo、tree，默认是 auto。
--skip-current       跳过当前 thread，默认启用。
--recent <n>         输出最近几条用户消息，默认是 3。
--lookback <n>       输出多少条附近上下文，默认是 6。
--format <fmt>       text 或 json，默认是 text。
```

## 要求

- Python 3.10+
- 本地存在 Codex 状态目录 `~/.codex`
- 不需要第三方 Python 依赖

## 开发

运行测试：

```bash
python -m pytest tests/test_continue.py -p no:cacheprovider
```

## English

[中文](#continue) | English

`continue` is a tiny recovery tool for Codex. It helps recover the previous actionable task after a Codex session is interrupted by compaction failure, crash, or lost context.

It is local-only and read-only. It does not upload conversations and does not modify the Codex state database.

## When to Use It

After a Codex session breaks, open a fresh Codex session in the same project directory and type:

```text
continue
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
git clone https://github.com/JY0xLU/continue.git ~/.codex/skills/continue
```

Restart Codex, then type `continue` at the beginning of a fresh session.

## CLI

```bash
python scripts/continue.py --cwd . --format text
python scripts/continue.py --cwd . --format json
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
python -m pytest tests/test_continue.py -p no:cacheprovider
```
