<p align="center">
  <img src="assets/codexgo-logo.png" alt="codexgo logo" width="132">
</p>

<h1 align="center">codexgo</h1>

<p align="center">
  <strong>一个本地只读的 Codex 会话恢复 skill。</strong><br>
  在新线程里找回上一轮可继续执行的请求，少一点重复解释，多一点确定性。
</p>

<p align="center">
  <a href="README.en.md">English</a>
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

## 定位

`codexgo` 是一个小型 Codex skill，用来在新 Codex 线程中恢复上一轮任务的 continuation prompt。

它不会调用网络，不会写入 Codex 数据库，也不会修改项目文件。它只读取本机 Codex 状态和会话记录，尝试判断上一轮对话里最适合继续执行的请求是什么。

典型用法是在新线程开头输入：

```text
codexgo
```

然后把它返回的 `resolved_request` 交给当前 Codex 线程继续处理。

## 适用场景

| 场景 | codexgo 的作用 |
| --- | --- |
| 长线程中断后重新开会话 | 从本地历史中恢复上一轮任务入口 |
| 最后一条消息只是 `continue` / `继续` | 向前查找真正的任务内容 |
| 最后一条消息只是 `ok` / `好的` | 找回刚刚被确认的助手建议 |
| 用户补充了额外限制 | 将补充内容和前面的任务线索合并 |
| 当前目录是项目子目录 | 在工作区树或 Git 仓库范围内寻找相关历史 |
| 需要接自动化 | 输出稳定的 JSON 字段 |

如果没有找到可信的可恢复内容，它会返回错误状态，而不是编造一个任务。

## 读取内容

`codexgo` 的实现是本地只读解析，主要读取这些信息：

| 来源 | 用途 |
| --- | --- |
| `state_*.sqlite` | 查找 Codex thread、工作区路径、更新时间等索引信息 |
| rollout JSONL | 读取用户消息、助手回复、工具调用片段和中断标记 |
| 当前 `--cwd` | 作为工作区匹配的起点 |
| 最近用户消息 | 判断最后一句是任务、短回复、补充说明还是触发词 |
| 最近助手消息 | 当用户只表示同意时，用来恢复被同意的方案 |

它默认跳过当前 thread，避免把你在新线程里输入的 `codexgo` 本身当作恢复目标。

## 匹配范围

`--scope` 控制从哪些历史线程中恢复：

| 范围 | 说明 |
| --- | --- |
| `exact` | 只匹配完全相同的工作区路径 |
| `repo` | 匹配同一个 Git 仓库内的线程 |
| `tree` | 匹配当前路径的父目录或子目录线程 |
| `auto` | 默认策略，按上下文选择合适范围 |

`tree` 对 Codex App 比较有用，因为同一个项目可能在根目录和子目录都开过线程。

## 过滤与回溯

中断前最后一句经常不是完整任务。`codexgo` 会对常见低信息消息做规则处理：

| 类型 | 示例 | 处理 |
| --- | --- | --- |
| 继续类触发 | `continue`、`go on`、`继续`、`jixu` | 回溯到上一条明确任务 |
| 同意类回复 | `ok`、`yes`、`好的`、`可以` | 恢复上一条助手建议 |
| skill 触发词 | `codexgo`、`golast` | 不作为任务内容 |
| 中断标记 | `<turn_aborted>` | 忽略 |
| 空壳线程 | 只有系统提示、AGENTS 内容或触发词 | 跳过，继续找更早线程 |

如果请求依赖更早上下文，输出会通过 `context_expanded_upward` 标记，并在 `supporting_context` 中附带附近线索。

## JSON 字段

脚本模式建议使用 `--format json`：

| 字段 | 含义 |
| --- | --- |
| `status` | `ok` 或错误状态 |
| `current_cwd` | 本次运行传入的工作区 |
| `scope_used` | 实际使用的搜索范围 |
| `matched_cwd` | 命中的历史线程工作区 |
| `thread_id` | 命中的 Codex thread |
| `literal_last_user_message` | 时间线上最后一条用户消息原文 |
| `resolved_request` | 建议继续执行的请求 |
| `resolved_source` | 判断来源，例如用户任务、助手建议、补充合并 |
| `decision_basis_message` | 同意某个方案时，对应的方案依据 |
| `supporting_context` | 为消解上下文依赖附带的附近消息 |
| `recent_user_messages` | 最近几条用户消息，便于人工核对 |
| `context_expanded_upward` | 是否向更早对话补充上下文 |

示例：

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
    "继续刚才那个思路"
  ]
}
```

## 安装

`codexgo` 是 Codex skill，不是 pip 包。把仓库放进 Codex 的 `skills/codexgo` 目录，再重启 Codex。

### Codex App

Codex 桌面 App 可能使用独立的 `CODEX_HOME`。在 Windows 上，常见位置是 `D:\CodexData\.codex`；普通 CLI 环境通常是 `~/.codex`。

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } elseif (Test-Path "D:\CodexData\.codex") { "D:\CodexData\.codex" } else { "$HOME\.codex" }
New-Item -ItemType Directory -Force "$CodexHome\skills" | Out-Null
git clone https://github.com/JY0xLU/codexgo.git "$CodexHome\skills\codexgo"
```

重启 Codex App 后，本地 skill 才会被重新扫描。

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

## 使用图

<p align="center">
  <img src="assets/codexgo-usage.png" alt="codexgo recovery flow" width="100%">
</p>

## 命令行

```bash
python scripts/codexgo.py --cwd . --format text
python scripts/codexgo.py --cwd . --format json
```

常用参数：

```text
--cwd <path>         工作区路径，默认是当前目录。
--codex-home <path>  Codex 数据目录，默认是 CODEX_HOME 或 ~/.codex。
--scope <mode>       搜索范围：auto、exact、repo、tree，默认是 auto。
--skip-current       跳过当前 thread，默认启用。
--recent <n>         输出最近几条用户消息，默认是 3。
--lookback <n>       输出多少条附近上下文，默认是 6。
--format <fmt>       text 或 json，默认是 text。
```

## 本地与隐私

- 只读取本机 Codex 状态和会话记录。
- 不上传对话，不调用网络。
- 不写入 Codex 数据库。
- 不修改当前项目文件。
- 使用规则判断，不是新的 LLM 代理。

## 运行条件

- Python 3.10+
- 本机存在 Codex 数据目录
- 不需要第三方 Python 依赖

## 边界

- 没有本地会话记录时无法恢复。
- Codex 本地状态格式变化后可能需要更新解析逻辑。
- 同一工作区或同一 Git 仓库内恢复效果最好。
- 低信息识别是规则型逻辑，不是完整语义理解。

## Star History

<a href="https://www.star-history.com/#JY0xLU/codexgo&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
  </picture>
</a>

## 开发

```bash
pytest
```

## License

Apache-2.0
