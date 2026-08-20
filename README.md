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
- **零配置接入**：一条 Marketplace 命令安装插件，语义 MCP 自动拉起，Agent 通过两个有界工具
  `browse_semantics` / `resolve_semantics` 查询语义层。

## 深度学习类比

SkillOpt 的核心理念在这里同样成立——语义层就是 Agent 的可训练状态：

| 深度学习 | EvoOntology |
| --- | --- |
| 模型权重 | 语义层 `semantic_vN`（Markdown/JSON 记录） |
| Forward pass | Data Agent 在 benchmark 上执行任务 |
| Loss / gradient | 历史轨迹诊断 + 因果归因 |
| Gradient clipping | Candidate 局部补丁（Content / Tool / Schema） |
| SGD step | 把补丁落成新版本 |
| 验证集 | `fixed_split` 的 Validation Reserve / `rolling_trajectory` 的 Validation Reserve |
| LR schedule | `EvolutionSession` 的轮次预算（默认 8 轮） |

## 架构总览

```text
自然语言问题 ──▶ Data Agent（Claude Code / Codex / benchmark harness）
                    │ MCP: browse_semantics / resolve_semantics
                    ▼
              EvoOntology 语义层 semantic_vN
                    │
                    │ /evo-evolve
                    ▼
        EvolutionSession：冻结预算与数据 → 诊断 → 归因 → 补丁 → 评估门控
                    │
                    ▼
        Accept 发布 semantic_vN+1 / Reject 下一轮 / Incomplete 保持 Parent
```

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

安装后新建会话再运行 `/evo-build`（Claude Code）或让 Codex 按 `build-semantic-layer` skill 构建。

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

## 两种 mode

Build Step 0 确定并写入 `.evoontology/project.json` 的 `mode`：

- **`fixed_split`**：有固定问题集、Ground Truth 和评测边界的 benchmark。Construction Pool 用于
  Build/诊断，Validation Reserve 只用于最终 Gate。
- **`rolling_trajectory`**：没有固定测试集的真实业务 / 冷启动。seed workload 初始化 `semantic_v0`，
  后续按 checkpoint 收集新任务轨迹，用独立抽样任务或 LLM Judge 完成 Gate。

两种 mode 共用同一套 workspace、版本与 checkpoint 机制，区别只在 workload 如何进入构建、进化与评估。

## 语义 MCP（零配置）

插件 `.mcp.json` 自动拉起服务，默认 workspace 为当前项目的 `.evoontology/`：

- `browse_semantics(query, kind, limit)` —— 发现与当前问题相关的概念；
- `resolve_semantics(mentions, context)` —— 把选中概念解析为 grounded 的 Mapping，并带回关联的
  Relation / Constraint / Evidence；
- 资源 `evo-semantic://session-manifest` —— 会话开始时可读的简洁说明。

## 仓库结构

| 目录 | 内容 |
| --- | --- |
| `evoontology/` | 核心包：ontology store / runtime(MCP) / trajectory / trigger / evaluation / evolution / validate |
| `plugins/` | Claude Code 插件与 Codex 插件（各内置一份 core 副本） |
| `benchmarks/` | 三个 benchmark 环境 + 统一 adapter 注册表 |
| `scripts/` | `sync_plugin_core.py`：把根 core 同步到两个插件 |
| `tests/` | 核心路径回归测试 |
| `docs/` | 架构与接入文档 |

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
- `plugins/claude-code/README.md` · `plugins/evoontology-codex/README.md` —— 插件组件说明。

## License

MIT © Eric Chong
