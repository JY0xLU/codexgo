<p align="center">
  <img src="assets/codexgo-logo.png" alt="codexgo logo" width="132">
</p>

<h1 align="center">codexgo</h1>

<p align="center">
  <strong>一个很小的 Codex 断点恢复 skill。</strong><br>
  线程断了也别慌，它会去本地记录里把任务捞回来。 (｀・ω・´)
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

## 是什么

`codexgo` 处理一个很具体、也很烦人的问题：你刚把任务讲清楚，Codex 正在做，线程却因为 compact、崩溃或上下文丢失断掉了。新开一个会话输入 `codexgo`，它会像一个迷你侦探一样翻本地记录，把最应该继续的请求找回来。

不玄学，不联网，也不碰你的数据库。它只是安静地读一读本地历史，然后告诉你：“刚才我们应该继续这个。” (｡•̀ᴗ-)✧

## 问题

Codex 会定期执行自动压缩背景信息。当压缩请求中途断开时，你可能会看到类似这样的报错：

```text
Error running remote compact task: stream disconnected before completion:
error sending request for url (https://chatgpt.com/backend-api/codex/responses/compact)
```

这时候原会话通常已经无法继续，但任务上下文还留在本地记录里。`codexgo` 做的事情就是把那段上下文重新捞出来。

## 解决方案

压缩崩溃后：

1. 留在原工作区，崩溃的会话不用再硬救。
2. 新开一个 Codex 会话。
3. 输入 `codexgo`。

```text
codexgo
```

它会自动恢复上一次会话的最后一个可执行请求，方便你立即继续工作。无需手动回忆，无需重新描述任务，也不用重建上下文。

## 工作原理

1. 读取 Codex 本地 SQLite 状态数据库。
2. 定位当前工作区的上一次会话线程。
3. 解析对话时间线，识别最后的真实请求。
4. 跳过 `ok`、`继续` 等低信号消息，追溯到实际任务。
5. 对“刚才那个”“上一条方案”“继续这个方向”等模糊引用自动向上扩展上下文。

## 亮点

| 特性 | 说明 |
| --- | --- |
| 小而专 | 一个 Python 脚本，一个 skill 文件，标准库实现 |
| 安静安全 | 只读本地 Codex 数据，不上传对话，不修改数据库 |
| 有点记性 | 会跳过低信息回复，并向上追溯“刚才那个”“上一条方案”等模糊引用 |
| 好接脚本 | 同时支持普通文本输出和 JSON 输出 |
| 适合拆开看 | 逻辑集中、依赖极少，方便读代码和改造 |

## 安装

`codexgo` 是一个 Codex skill，不是 pip 包。把仓库放进 Codex 的 `skills/codexgo` 目录，然后重启 Codex 就行。

### Codex App

如果你用的是 Codex 桌面 App，推荐先按你的 `CODEX_HOME` 找目录；没有设置时，Windows App 常见位置是 `D:\CodexData\.codex`，普通 CLI 常见位置是 `~/.codex`。

Windows PowerShell：

```powershell
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } elseif (Test-Path "D:\CodexData\.codex") { "D:\CodexData\.codex" } else { "$HOME\.codex" }
New-Item -ItemType Directory -Force "$CodexHome\skills" | Out-Null
git clone https://github.com/JY0xLU/codexgo.git "$CodexHome\skills\codexgo"
```

然后完全重启 Codex App。小家伙要重新被扫描到，别只刷新页面。 (｀・ω・´)

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

重启 Codex App，或者重新打开一个 Codex CLI 会话，然后输入：

```text
codexgo
```

如果你刚从一个断掉的线程里爬出来，这通常就是第一句要说的话。别解释第二遍，让小工具先翻翻旧账。

## 使用图

<p align="center">
  <img src="assets/codexgo-usage.png" alt="codexgo recovery flow" width="100%">
</p>

## 它会处理什么

它主要负责把“人类随口说的话”变回“机器可以继续执行的任务”。小小一只，但会努力往前翻。 (ง •̀_•́)ง

| 中断前最后一条消息 | codexgo 怎么判断 |
| --- | --- |
| 真正的任务 | 直接返回这条任务 |
| `continue` / `go on` / `继续` | 向前找到上一条真实请求 |
| `ok` / `yes` / `好的` | 恢复你刚刚同意的助手方案 |
| `补充：...` | 把补充内容和前面的上下文合并 |
| “刚才那个” / “上一条方案” / “继续这个方向” | 自动向上扩展 supporting context |
| 选型或方案比较 | 输出 `decision_basis_message` 作为决策依据 |
| 需要接入脚本 | 输出 JSON，交给其他工具继续处理 |

JSON 输出里会包含 `context_expanded_upward`，用于标记是否为了消解模糊引用而向更早的对话扩展了上下文。

## 输出示例

普通文本输出：

```text
Recovered Codex request
- matched workspace: /path/to/project
- source: user_message
- needs more context: False
- context expanded upward: False

Resolved request:
Finish the README polish and run the tests.
```

JSON 输出适合脚本接入：

```json
{
  "status": "ok",
  "resolved_request": "Finish the README polish and run the tests.",
  "resolved_source": "user_message",
  "decision_basis_message": "",
  "context_expanded_upward": false
}
```

## 安全和隐私

- 只读取本机 `~/.codex/state_*.sqlite` 和 rollout JSONL。
- 不上传对话、不调用网络、不写入 Codex 数据库。
- 不修改当前项目文件，除非你把输出交给其他自动化脚本继续执行。
- 出错时会返回错误信息，不会伪造恢复结果。

换句话说，它不是“云端记忆助手”，只是你电脑里的小书签。

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

## 要求

- Python 3.10+
- 本地存在 Codex 状态目录 `~/.codex`
- 不需要第三方 Python 依赖

## 限制

- Codex 本地状态目录必须存在，否则没有历史记录可恢复。
- 如果 Codex 未来改动 SQLite schema 或 rollout 格式，可能需要更新解析逻辑。
- 模糊引用追溯是规则型逻辑，不是 LLM 语义推理。
- 在同一工作区或同一 Git 仓库中恢复效果最好。

它会尽力找线索，但不会装作什么都懂。找不到就老实报错，这点很重要。

## Star History

<p align="center">
  <a href="https://starchart.cc/JY0xLU/codexgo">
    <img width="100%" alt="codexgo Star History" src="https://starchart.cc/JY0xLU/codexgo.svg">
  </a>
</p>

## 开发

运行测试：

```bash
python -m pytest tests/test_codexgo.py -p no:cacheprovider
```

## License

Apache-2.0
