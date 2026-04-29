# codexgo

[English](README.en.md)

`codexgo` 是一个很小的 Codex 恢复工具。Codex 因为 compaction、崩溃或上下文丢失而中断后，它可以从本地 Codex 会话记录里找回上一轮真正要继续的任务。

它只读本地文件，不上传对话，不修改 Codex 数据库。

## 使用场景

当 Codex 会话断掉后，在同一个项目目录里重新打开 Codex，然后输入：

```text
codexgo
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
git clone https://github.com/JY0xLU/codexgo.git ~/.codex/skills/codexgo
```

然后重启 Codex。之后在新会话开头输入 `codexgo` 即可。

## 命令行

```bash
python scripts/codexgo.py --cwd . --format text
python scripts/codexgo.py --cwd . --format json
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
python -m pytest tests/test_codexgo.py -p no:cacheprovider
```
