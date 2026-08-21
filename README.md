# EvoOntology

*给 Data Agent 一个「像训练神经网络一样训练语义层」的机制：有轮次预算、有验证集、有
Accept/Reject 门控，但改的是语义记录（Term / Mapping / Relation / Constraint / Evidence），而不是模型权重。*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

> 📖 完整使用指南见 [`USAGE.md`](USAGE.md)；架构与接入文档见 [`docs/`](docs/README.md)。

## 为什么需要 EvoOntology

Data Agent 直接查库时，常因自然语言与数据库 schema 之间的 gap 答错：指标口径不清、实体指代不明、
隐含约束缺失。手写的语义层能缓解这个问题，但**会过时**——业务在变、问题在变，而手工维护的语义层没有
反馈回路。

EvoOntology 把语义层变成**可训练的状态**：

- **版本化语义层**：五类记录构成 `semantic_vN`，每次修改都产生新版本，可对比、可回滚；
- **有门控的进化**：`/evo-evolve` 从历史任务轨迹诊断问题、归因、打补丁，Candidate 必须在受控评估中
  **可复现地优于 Parent** 才能发布；Reject 不是终点，而是下一轮的输入；
- **零配置接入**：通过 Marketplace 安装插件，语义层自动接入，Agent 通过
  `browse_semantics` / `resolve_semantics` 发现并解析分析概念。

## 支持的 Benchmark

| Benchmark | 类型 | 目录 |
| --- | --- | --- |
| BIRD | text-to-SQL | `benchmarks/bird/` |
| DDR-10K | 自主数据分析 | `benchmarks/ddr_10k/` |
| InsightBench | 迭代分析 / 代码生成 | `benchmarks/insightbench/` |

每个 benchmark 是一个自包含环境，通过 `EvolutionAdapter` 接入进化循环（对标 SkillOpt 的
`envs/<name>/`）。统一发现入口：`python -m benchmarks list`。接入新环境见
[`docs/guide/new-benchmark.md`](docs/guide/new-benchmark.md)。

## 安装

选择你正在使用的客户端，通过 Marketplace 安装插件（无需 clone 仓库、无需建虚拟环境、无需单独
`pip install`）：

### Claude Code

```bash
claude plugin marketplace add Cmd210/EvoOntology
claude plugin install evoontology@evoontology
claude plugin list
```

### Codex

```bash
codex plugin marketplace add Cmd210/EvoOntology
codex plugin add evoontology-codex@evoontology
codex plugin list
```

安装后新建会话再运行 `/evo-build`（Claude Code）或让 Codex 按 `$evo-build` skill 构建。

## 快速开始

```bash
# 1) 在目标项目里构建初始语义层（Step 0 会确认 fixed_split / rolling_trajectory）
/evo-build

# 2) Data Agent 通过语义 MCP grounding 概念后执行任务，轨迹写入 .evoontology/trajectories/

# 3) 达到触发条件后进化（默认 8 轮预算；只有 Accept 才推进 checkpoint）
/evo-evolve

# 4) 查看当前语义层（只读离线 HTML）
python -m evoontology.visualization --root .evoontology --no-browser
```

## 两种使用场景

- **`fixed_split`**：适合有固定问题集、Ground Truth 和评测边界的 benchmark。
- **`rolling_trajectory`**：适合没有固定测试集的真实业务或冷启动。

两者的数据边界、进化触发与评估流程详见 [`USAGE.md`](USAGE.md)。

## 语义层怎么接入

插件安装后自动接入语义 MCP，默认 workspace 为当前项目的 `.evoontology/`。Agent 可用
`browse_semantics` / `resolve_semantics` 发现并解析分析概念，无需额外配置。详见
[`USAGE.md`](USAGE.md)。

## 开发

```bash
python -m pytest tests -q
python scripts/sync_plugin_core.py --check
python -m benchmarks list
```

修改 `evoontology/` 后运行 `python scripts/sync_plugin_core.py` 同步到两个插件再提交。发布门禁
`python -m evoontology.validate --root <workspace>` 只做结构校验（JSON 合法 / 引用完整 / 可加载）。

## 文档

- [`USAGE.md`](USAGE.md) —— 产品化使用指南（安装、workspace、进化闭环、端到端流程）；
- [`docs/architecture.md`](docs/architecture.md) —— 架构总览与 SkillOpt 对照；
- [`docs/guide/new-benchmark.md`](docs/guide/new-benchmark.md) —— 接入新 benchmark；
- `plugins/claude-code/README.md` · `plugins/evoontology-codex/README.md` —— 插件安装与使用说明。

## License

MIT © Eric Chong
