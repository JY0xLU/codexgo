<p align="center">
  <img src="assets/codexgo-logo.png" alt="codexgo logo" width="132">
</p>

<h1 align="center">codexgo</h1>

<p align="center">
  <strong>给 Codex 新线程递一张“刚才干到哪了”的小纸条。</strong><br>
  旧会话断了，别急着从头讲。让它先翻一下本机黑匣子。 (｀・ω・´)
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

## 一句话

`codexgo` 是一个很小的 Codex skill。它不替你写代码，也不联网找资料，只负责一件事：当你被迫换到新 Codex 线程时，帮你从本机记录里整理出“下一句应该继续交给 Codex 的任务”。

它像一个本地黑匣子读取器。飞机没有了，黑匣子还在；线程没了，线索还在。

## 适合什么时候用

你已经把需求讲清楚了，Codex 也开始做了，但会话突然不可用了。新线程打开后，你当然可以手动复述一遍，不过这通常很烦，而且容易漏掉刚才定下来的约束。

这时先输入：

```text
codexgo
```

它会在当前工作区附近找最近的 Codex 会话记录，把更像“任务本体”的那句话整理出来。这样新线程不用靠猜，也不用你临场背诵上一轮对话。

## 它会交还什么

`codexgo` 的输出重点不是“完整聊天记录”，而是一张续航提示卡：

| 场景 | 它倾向于交还 |
| --- | --- |
| 最后一条就是明确任务 | 直接交还那条任务 |
| 最后一条只是 `continue` / `go on` / `继续` | 往前找真正要继续的事情 |
| 最后一条是 `ok` / `yes` / `好的` | 找回你刚刚认可的助手建议 |
| 最后一条是补充说明 | 把补充和前面的任务线索拼在一起 |
| 最后一条依赖旧上下文 | 附带必要的 supporting context |
| 你要接自动化脚本 | 用 JSON 输出结构化字段 |

它不会假装自己懂一切。找不到可恢复内容时，它会老实报错。

## 黑匣子里读什么

`codexgo` 只做本地只读分析。它会打开 Codex 数据目录里的状态索引和会话流水文件，把它们拼成一条可以续接的线索链：

| 线索 | 用途 |
| --- | --- |
| `state_*.sqlite` | 找到最近的 Codex thread、工作区路径和更新时间 |
| rollout JSONL | 读取用户消息、助手回复、工具事件和中断前后的时间线 |
| 当前 `--cwd` | 判断应该优先恢复哪个工作区或 Git 仓库里的线程 |
| 最近用户消息 | 区分真正任务、短回复、补充说明和触发词 |
| 助手上一条建议 | 当用户只回复 `ok` / `好的` 时，找回刚才被同意的方案 |

默认会跳过当前 thread，避免你在新线程里输入 `codexgo` 后，它又把“你刚刚输入 codexgo”当成要恢复的任务。这个小坑很滑，已经踩过，已经填上。

## 搜索范围怎么选

工作区匹配不是只看一个绝对路径。`codexgo` 支持几种范围，默认 `auto` 会尽量选一个安全的范围：

| 范围 | 适合场景 |
| --- | --- |
| `exact` | 只看完全相同的工作区路径 |
| `repo` | 在同一个 Git 仓库内找上一条可恢复线程 |
| `tree` | 当前目录和父/子目录之间都可能有关联时使用 |
| `auto` | 先按当前上下文自动尝试，不够再放宽 |

这对 Codex App 很重要：你可能在项目根目录开过会话，也可能在子目录里重新打开新线程。`codexgo` 会尽量把这两种情况接起来，而不是死守一个路径。

## 它怎么避开噪声

断线前最后一句经常不是任务本身，而是人类很自然的短回复。`codexgo` 会把这些看成路标，而不是终点：

| 类型 | 例子 | 处理方式 |
| --- | --- | --- |
| 继续触发 | `continue`、`go on`、`继续`、`jixu` | 向前找上一条真实任务 |
| 同意回复 | `ok`、`yes`、`好的`、`可以` | 找回上一条助手建议 |
| 技能触发 | `codexgo`、`golast` | 不把触发词当任务 |
| 中断标记 | `<turn_aborted>` | 忽略 |
| 空壳线程 | 只有系统提示、AGENTS 或触发词 | 跳过，继续找更早的可恢复线程 |

它也会识别一些“需要往上看”的表达，比如“继续刚才那个思路”“按上一轮决定走”“如果我理解错了就调整”。这类话单独看不够完整，所以 JSON 里会用 `context_expanded_upward` 标记是否向前补了上下文。

## 续航卡字段

JSON 输出适合接脚本，也适合看它到底为什么这么判断：

| 字段 | 含义 |
| --- | --- |
| `status` | `ok` 或错误状态 |
| `current_cwd` | 你这次运行时传入的工作区 |
| `scope_used` | 实际使用的搜索范围 |
| `matched_cwd` | 命中的历史线程工作区 |
| `thread_id` | 命中的 Codex thread |
| `literal_last_user_message` | 时间线上最后一条用户消息，保留原貌 |
| `resolved_request` | 最终建议交给新线程继续执行的任务 |
| `resolved_source` | 结果来自用户消息、助手方案、补充合并等哪类来源 |
| `decision_basis_message` | 如果用户在同意一个方案，这里放决策依据 |
| `supporting_context` | 为了消解模糊引用而附带的附近上下文 |
| `recent_user_messages` | 最近几条用户消息，方便人工确认 |
| `context_expanded_upward` | 是否为了补足语义向更早的对话回看 |

普通文本输出更适合人直接看，JSON 输出更适合自动化接力。

## 放到 Codex 里

`codexgo` 是 Codex skill，不是 pip 包。把仓库放进 Codex 的 `skills/codexgo` 目录，再重启 Codex。

### Codex App

Codex 桌面 App 可能使用独立的 `CODEX_HOME`。在这台 Windows 机器上，常见位置是 `D:\CodexData\.codex`；普通 CLI 环境通常是 `~/.codex`。

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } elseif (Test-Path "D:\CodexData\.codex") { "D:\CodexData\.codex" } else { "$HOME\.codex" }
New-Item -ItemType Directory -Force "$CodexHome\skills" | Out-Null
git clone https://github.com/JY0xLU/codexgo.git "$CodexHome\skills\codexgo"
```

然后完全重启 Codex App。小纸条递送员要重新被扫描到。 (｡•̀ᴗ-)✧

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

你也可以把它当普通脚本调用，方便调试或接到别的自动化里：

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

JSON 输出示例：

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

## 本地规矩

- 只检查你机器上的 Codex 状态索引和会话流水文件。
- 不上传对话，不调用网络，不改写 Codex 数据。
- 不修改当前项目，除非你把输出交给别的自动化继续执行。
- 规则型判断，不是一个新的 LLM 语义代理。

换句话说，它不是“云记忆”，只是你电脑里的一枚小书签。书签不会很聪明，但它知道刚才夹在哪一页。

## 运行条件

- Python 3.10+
- 本机存在 Codex 数据目录
- 不需要第三方 Python 依赖

## 边界

- 如果本机没有对应会话记录，它没有东西可翻。
- 如果 Codex 将来改动本地状态格式，解析逻辑可能需要更新。
- 它更擅长在同一工作区或同一 Git 仓库内续接任务。
- 它会尽量避开“嗯”“继续”“好的”这类短回复，但不是自然语言全知裁判。

## Star History

<a href="https://www.star-history.com/#JY0xLU/codexgo&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=JY0xLU/codexgo&type=Date" />
  </picture>
</a>

## 开发

运行测试：

```bash
pytest
```

## License

Apache-2.0
