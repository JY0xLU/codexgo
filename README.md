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
  "resolved_request": "Finish the README polish and run the tests.",
  "resolved_source": "user_message",
  "decision_basis_message": "",
  "context_expanded_upward": false
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
