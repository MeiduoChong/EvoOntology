# EvoOntology

*为 Data Agent 提供可版本化、可评估、可自我进化的语义层——像训练模型一样训练 Ontology：有冻结预算、有验证集、有 Accept / Reject 门禁，但改的是语义记录而不是模型权重。*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

> 📖 完整使用指南见 [`USAGE.md`](USAGE.md)；产品化设计权威文档见
> [`docs/evolution-productization-design.md`](docs/evolution-productization-design.md)。

---

## 为什么需要 EvoOntology

Data Agent 直接查库时，常因自然语言与数据库 schema 之间的 gap 答错：指标口径不清、
实体指代不明、隐含约束缺失。人工编写的语义层能缓解这个问题，但**会过时**——业务在变、
问题在变，而手工维护的语义层没有反馈回路。

EvoOntology 的解法是把语义层变成**可训练的状态**：

- **版本化的语义层**：五类记录（Term / Mapping / Relation / Constraint / Evidence）
  构成 `semantic_vN`，每次修改都产生新版本，可对比、可回滚；
- **有门禁的进化**：`/evo-evolve` 从历史任务轨迹诊断问题、归因、打补丁，Candidate 必须
  在受控评估中**可复现地优于 Parent** 才能发布；Reject 不是终点，而是下一轮的输入；
- **零配置接入**：一条 Marketplace 命令安装插件，语义 MCP 自动拉起，Agent 通过两个
  有界工具 `browse_semantics` / `resolve_semantics` 查询语义层。

语义层从此和代码一样有版本历史、有测试、有发布门禁，并且能沿着真实使用轨迹持续改进。

## 架构总览

```text
自然语言问题 ──▶ Data Agent（Claude Code / Codex / benchmark harness）
                    │  MCP: browse_semantics / resolve_semantics
                    ▼
          EvoOntology 语义层  semantic_vN（Term/Mapping/Relation/Constraint/Evidence）
                    ▲
                    │ Accept：发布 semantic_vN+1、切换 active、推进 checkpoint
                    │
   /evo-evolve ─────┤  EvolutionSession：冻结预算与数据 → 诊断 → 归因 → 补丁 → 评估门禁
                    │
          trajectories/（Tool Call 级任务轨迹）+ 评估结果
```

- **Build**：`/evo-build` 走 Workload-Guided Probing → Evidence-Grounded Commitment，
  产出五类记录并发布 `semantic_v0`；
- **Use**：Data Agent 会话中用语义 MCP  grounding 概念，再交给原生工具执行查询；
- **Record**：任务轨迹以 Tool Call 粒度写入 `trajectories/`（不存思维链）；
- **Evolve**：达到触发条件后提醒，`/evo-evolve` 在一个 EvolutionSession 内循环
  Candidate，直到 Accept 或外部条件导致 Incomplete。

## 安装

请选择正在使用的客户端，通过项目 Marketplace 安装插件。无需 clone 仓库、创建虚拟环境或
单独执行 `pip install`。

### Claude Code

```bash
claude plugin marketplace add Cmd210/EvoOntology
claude plugin marketplace list
claude plugin install evoontology@evoontology
claude plugin list
```

`marketplace list` 只验证 Marketplace 来源，真正下载插件的是 `plugin install`；
`plugin list` 用于确认最终安装状态。

> marketplace 的 `source` 用 `git-subdir` 指向 `plugins/claude-code` 子目录，需较新版本
> Claude Code；旧版本可能报 schema 校验错误。

### Codex

```bash
codex plugin marketplace add Cmd210/EvoOntology
codex plugin marketplace list
codex plugin add evoontology-codex@evoontology
codex plugin list
```

两种客户端安装的是各自的插件包，功能一致：Build / Evolve 方法、语义 MCP、Workspace
状态与版本管理。两个插件都内置同一份 `evoontology` 核心包（由
`scripts/sync_plugin_core.py` 从仓库根同步），自包含、开箱即用。安装或更新后请新建
一个会话，再执行 `/evo-build`。

## 两个命令

| 命令 | 语义 | 执行者 |
| --- | --- | --- |
| `/evo-build` | 构建 `semantic_v0`：读数据、探索 schema、生成五类记录 | agent 按 build skill |
| `/evo-evolve` | 触发进化：诊断 → 归因 → 补丁 → Parent/Candidate gate → 发布 | agent 按 evolve skill |

两者都是**触发指令**；真正的构建 / 进化由 agent 按 skill 执行，确定性状态（版本、预算、
checkpoint、来源记录）由核心包保证。

## 进化闭环（EvolutionSession）

每次 `/evo-evolve` 对应一个 Run，由 `evoontology.evolution.EvolutionSession` 状态机托管，
落盘在 `<workspace>/evolution/run_<N>/`：

```text
running ──Reject──▶ running（同一 run 内下一轮 Candidate）
running ──Accept──▶ accepted（发布新版本、推进 checkpoint）
running ──预算耗尽/外部阻断──▶ incomplete（不发布、不推进）
```

关键规则：

- **预算先确认**：新 run 先向用户说明计划使用的轮数（默认 8），确认后冻结；resume
  同一 run 不重复询问；
- **轨迹来源先确认**：轨迹来源或范围未定时，向用户说明路径、内容范围、时间与用途并
  确认，确认后持久化到 `run_<N>/trajectory-sources.json`；新 run 默认复用上次来源记录，
  仅当来源新增、失效或范围变化时重新确认；
- **三个进化维度**：Content / Tool / Schema，Candidate 改动必须可溯源到目标维度、
  可回滚到 Parent；
- **独立版本评估**：Candidate 以自己的存储版本参评（`--semantic-version` /
  `version=`），比较期间不修改 `active.json`；
- **只有 Accept 推进 checkpoint**：Reject 写结果后继续下一轮；Incomplete 保持 Parent
  与 checkpoint 不变。

## Workspace

默认 Workspace 是 `<project-root>/.evoontology/`；benchmark 可显式指定独立 Workspace。
一个 Workspace 对应一条独立的语义版本与进化历史：

```text
.evoontology/
├── project.json       # mode、数据源、workload、Evaluator 与数据边界
├── active.json        # 当前正式语义版本
├── state.json         # reminder checkpoint 与阈值
├── versions/          # 正式 semantic_vN 与候选 vN-cK，各含五类 JSON
├── trajectories/      # 每个 Data Agent 任务一条 JSON trajectory
└── evolution/         # 每个 run 一个目录 run_N/
    └── run_N/
        ├── run.json                 # 状态、Parent、当前 Candidate、轮次、冻结预算
        ├── trajectory-sources.json  # 用户确认的轨迹来源记录
        ├── rounds.jsonl             # 每轮一行摘要
        └── evaluations/             # 正式 Parent/Candidate 评估摘要
```

Core 通过 `resolve_workspace()` 统一解析路径；`project.json` 在 Build Step 0 确认后写入，
`active.json` 与 `state.json` 只在 `semantic_v0` 保存并校验成功后生成，避免失败构建留下
虚假的激活状态。

### 两种项目模式

Build Step 0 会根据项目是否有固定 benchmark 边界选择一种 mode，写入 `project.json`：

- **`fixed_split`**：适合 BIRD 等已有问题集、Ground Truth 和固定评测边界的 benchmark。
  Build 只使用 Construction Pool；Validation Reserve 只用于 Parent/Candidate 正式 Gate，
  不能回流到构建、诊断或补丁生成。
- **`rolling_trajectory`**：适合没有固定测试集的真实业务或冷启动项目。seed workload
  用于构建 `semantic_v0`，上线后的 task 持续写入 `trajectories/`；达到阈值后从
  checkpoint 之后的新轨迹中冻结批次，用独立抽样任务或 LLM Judge 完成 Gate。

两种 mode 共用同一套 Workspace、版本和 checkpoint 机制；区别只在 workload 如何进入构建、
进化与评估。

## 语义 MCP（零配置）

插件的 `.mcp.json` 以模块形式 spawn 服务，client 自动拉起，无需手动起服、无需填写
workspace 路径。默认 workspace 为当前项目的 `.evoontology/`：

```bash
python -m evoontology.runtime.mcp_server
```

如需指向别的 workspace，追加 `--store <workspace-root>`。接入后 Data Agent 可见：

- `browse_semantics(query, kind, limit)` —— 发现与当前问题相关的概念；
- `resolve_semantics(mentions, context)` —— 把选中概念解析为 grounding 的 Mapping，
  并带回关联的 Relation / Constraint / Evidence；
- 资源 `evo-semantic://session-manifest` —— 会话开始时读取的简洁说明。

这两个工具返回的是元数据与指引；数据库查询与代码执行仍由原生工具负责。

## 默认设置（可调整）

产品默认零配置，以下参数有内置默认值，需要时直接告诉 agent（例如「以后每 60 个任务
提醒我一次」），由 agent 更新 `state.json`。

### 进化触发阈值

满足任一条件即在 Session Start 给出**非阻塞提醒**（不会自动进化）：

- **工作量信号**：checkpoint 之后新增 ≥ **30** 条 task trajectory；
- **时间信号**：距 checkpoint ≥ **7** 天。

首次 `/evo-build` 自动初始化计时状态；只有正式 Gate 的 Accept 才推进 checkpoint。

### 评估协议（有 / 无 Ground Truth）

系统自动选择，无需手动声明：

- **有 GT**：benchmark 提供 `score_fn(answer, gt)` 绝对评分，Candidate 平均分严格高于
  Parent 才 Accept；
- **无 GT**：LLM Judge 匿名 A/B 比较 Parent 与 Candidate，Candidate 零硬伤且胜出任务
  严格多于 Parent 才 Accept（门槛见
  `plugins/claude-code/docs/evaluation-protocol.md`）。无 GT 时需指定一个独立于
  Evolver 的 judge 模型，凭据走环境变量。

## 仓库结构

| 目录 | 内容 |
| --- | --- |
| `evoontology/` | 核心包 v1.1.0：`ontology/`（五类记录 + 版本化 store）、`runtime/`（browse/resolve/MCP）、`trajectory/`（Tool Call 级轨迹）、`trigger/`（进化提醒）、`evaluation/`（GT / LLM Judge 调度）、`evolution/`（EvolutionSession 状态机 + adapter 契约）、`validate`（发布门禁） |
| `plugins/claude-code/` | Claude Code 插件：`/evo-build`、`/evo-evolve` 命令，builder / evolver skill，`.mcp.json`，Session Start 提醒 hook，内置 core 副本 |
| `plugins/evoontology-codex/` | 自包含 Codex 插件：`AGENTS.md` 项目指令、skills、`.mcp.json`，内置 core 副本 |
| `benchmarks/` | 三个 benchmark 接入示例（各含 Data Agent / Native Tools / Runner / Evaluator / EvolutionAdapter） |
| `scripts/` | `sync_plugin_core.py`：把根 core 同步到两个插件副本（`--check` 用于 CI） |
| `tests/` | 核心路径回归测试 |
| `docs/` | 产品化设计文档（权威） |

## Benchmarks

`benchmarks/` 下是三个接入示例，确定性能力统一由 `evoontology` 核心包提供，
benchmark 侧只保留特有的 Agent、工具与评估实现：

| 目录 | 基准 | 任务类型 |
| --- | --- | --- |
| `benchmarks/bird/` | BIRD | text-to-SQL |
| `benchmarks/ddr_10k/` | DDR-10K | 自主数据分析 |
| `benchmarks/insightbench/` | InsightBench | 迭代分析 / 代码生成 |

仓库不提供 benchmark 原始数据与预构建 ontology：准备官方数据后运行 `/evo-build` 构建
`semantic_v0`，再跑 baseline / semantic 两个条件。运行 benchmark 需要各自的 Python
依赖与模型凭据（见各目录 README）。

## 开发者

```bash
# 回归测试（core + 插件同步校验）
python -m pytest tests -q

# 校验两个插件内置 core 副本与仓库根一致
python scripts/sync_plugin_core.py --check
```

修改 `evoontology/` 后运行 `python scripts/sync_plugin_core.py` 同步到两个插件，
再提交。发布门禁 `python -m evoontology.validate --root <workspace>` 只做结构校验
（JSON 合法 / 引用完整 / 可加载），不做数据库语义校验。

## 文档

- [`USAGE.md`](USAGE.md) —— 产品化使用指南（安装、workspace、进化闭环、端到端流程）
- [`docs/evolution-productization-design.md`](docs/evolution-productization-design.md) —— 设计权威文档
- `plugins/claude-code/docs/` —— 版本命名 / 评估协议 / 轨迹格式
- `plugins/claude-code/README.md` · `plugins/evoontology-codex/README.md` —— 插件组件说明

## License

MIT © Eric Chong