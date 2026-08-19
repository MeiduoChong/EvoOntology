# EvoOntology

为 Data Agent 提供**自进化的语义层（Ontology Layer）**：在自然语言问题与数据库 schema
之间加一层可版本化、可自我改进的语义映射。

本仓库交付的是产品化形态：

```text
evoontology/   核心包（确定性能力：store / runtime / trajectory / trigger / evaluation）
plugins/       Claude Code 插件 + Codex 适配层（/evo-build、/evo-evolve 两命令）
benchmarks/    三个 benchmark 接入示例（bird / ddr_10k / insightbench）
tests/         核心路径测试
```

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
状态与版本管理。安装或更新后请新建一个会话，再执行 `/evo-build`。

## 作用

Data Agent 直接查库时，常因自然语言与 schema 之间的 gap 而答错。EvoOntology 插入一层
语义层，Agent 在会话中用两个 MCP 工具查询：

- `browse_semantics(query, kind, limit)` —— 发现与当前问题相关的概念；
- `resolve_semantics(mentions, context)` —— 把选中概念解析为 grounding 的 Mapping，
  并带回关联的 Relation / Constraint / Evidence。

语义层会自进化：`/evo-build` 构建初始 `semantic_v0`；`/evo-evolve` 依据 Tool Call 级
历史任务轨迹走「诊断 → 归因 → 补丁 → Parent/Candidate 评估 → 发布新版本」。

## 目录

| 目录 | 内容 |
| --- | --- |
| `evoontology/` | 核心包：`ontology/`（五类记录 + 版本化 store）、`runtime/`（browse/resolve/MCP）、`trajectory/`（Tool Call 级轨迹）、`trigger/`（进化提醒）、`evaluation/`（GT / LLM Judge 调度）、`validate`（发布门禁） |
| `plugins/claude-code/` | Claude Code 插件：`.mcp.json`（零配置语义 MCP）、`commands/`、`skills/`、`hooks/`（Session Start 提醒）、`scripts/`（check-reminder） |
| `plugins/evoontology-codex/` | 自包含 Codex 插件：manifest + skills + MCP + 安装脚本 |
| `benchmarks/` | 三个 benchmark 接入示例（各含 Data Agent / Native Tools / Runner / Evaluator） |
| `tests/` | 核心路径测试（store / runtime / trajectory / trigger / evaluation） |

## EvoOntology Workspace

默认 Workspace 是 `<project-root>/.evoontology/`；benchmark 也可以显式指定独立 Workspace。
一个 Workspace 对应一条独立的语义版本与进化历史：

```text
.evoontology/
├── project.json       # mode、数据源、workload、Evaluator 与数据边界
├── active.json        # 当前正式语义版本
├── state.json         # reminder checkpoint 与阈值
├── versions/          # semantic_vN 与 vN-cK
├── trajectories/      # 每个 Data Agent 任务一条 JSON trajectory
└── evolution/         # 每轮 context.json + result.json
```

Core 通过 `resolve_workspace()` 统一解析路径，`ensure_workspace()` 幂等创建三个目录；
`project.json` 在 Build Step 0 确认后写入，`active.json` 与 `state.json` 只在 `semantic_v0`
保存并校验成功后生成，避免失败构建留下虚假的激活状态。

### 两种项目模式

Step 0 会根据项目是否有固定 benchmark 边界选择一种 mode，并写入 `project.json`：

- **`fixed_split`**：适合 BIRD 等已有问题集、Ground Truth 和固定评测边界的 benchmark。
  Build 只使用 Construction Pool（例如 Fold A）；Validation Reserve（例如 Fold B）只用于
  Parent/Candidate 正式 Gate，不能回流到构建、诊断或补丁生成。
- **`rolling_trajectory`**：适合没有固定测试集的真实业务或冷启动项目。初始 seed workload
  用于构建 `semantic_v0`，上线后的 Data Agent task 持续写入 `trajectories/`；达到阈值后，
  Evolver 从 checkpoint 之后的新轨迹中诊断问题，并使用独立抽样任务或 LLM Judge 完成 Gate。

两种 mode 共用同一套 Workspace、版本和 checkpoint 机制；区别只在 workload 如何进入构建、
进化与评估。已有稳定 benchmark 划分时不要重新随机切分；没有 GT 时也无需人为伪造 Fold A/B。

## 语义 MCP（零配置）

`.mcp.json` 以模块形式 spawn 服务，client 自动拉起，无需手动起服、无需填写 workspace
路径。默认 workspace 为当前项目的 `.evoontology/`：

```bash
python -m evoontology.runtime.mcp_server
```

如需指向别的 workspace，追加 `--store <workspace-root>`。

## 默认设置（可调整）

产品默认零配置，以下参数有内置默认值，需要时可让 agent 调整（或直接改 workspace 的
`state.json`）。

### 进化触发阈值

EvoOntology 使用两类互补信号判断语义层是否值得复盘，满足任一条件便会在 Session Start
给出非阻塞提醒：

- **工作量信号**：自初始语义层发布或上次完成正式 Gate 后，新增 ≥ **30** 条 task trajectory
  （`min_new_trajectories`）。一条 trajectory 对应 Data Agent 完成的一次任务，而不是数据库
  记录数或工具调用次数；
- **时间信号**：距初始语义层发布或上次完成正式 Gate ≥ **7** 天（`min_days`），避免低频项目的
  语义层长期缺少复盘。

首次 `/evo-build` 会自动初始化计时状态；旧工作区若缺少状态，Session Start 钩子也会安全补建，
且不会丢弃已经积累的 trajectory。提醒只提供决策信号，**不会自动执行进化**；成功完成
`/evo-evolve` 的 Accept 或 Reject 完成落盘后，系统会推进本轮 trajectory 与时间 checkpoint；
未完成可靠 Gate 时不会推进。

阈值可以按项目节奏调整。例如告诉 Claude / Codex「以后每 60 个任务提醒我一次」，agent 会更新
`<workspace>/state.json` 的 `thresholds` 字段。

### 评估协议（有 / 无 Ground Truth）

系统自动选择，无需手动声明模式：

- **有 GT**：benchmark 提供 `score_fn(answer, gt)` 绝对评分，Candidate 平均分严格高于
  Parent 才 accept；
- **无 GT**：走 LLM Judge——匿名 A/B 比较 Parent 与 Candidate，Candidate 零硬伤且胜出
  任务严格多于 Parent 才 accept（门槛见 `plugins/claude-code/docs/evaluation-protocol.md`）。

无 GT 时需指定一个**独立于 Evolver 的 judge 模型**（provider / model / api key，凭据用
环境变量），直接告诉 agent 即可。

## 三个 benchmark 接入示例

`benchmarks/` 下是三个 benchmark 的接入示例，各含 Agent 实现、语义运行时、MCP server
与评估入口；其确定性能力统一由仓库根的 `evoontology` 包提供，不重复维护。

| 目录 | 基准 | 任务类型 |
| --- | --- | --- |
| `benchmarks/bird/` | BIRD | text-to-SQL |
| `benchmarks/ddr_10k/` | DDR-10K | 自主数据分析 |
| `benchmarks/insightbench/` | InsightBench | 迭代分析 / 代码生成 |

运行 benchmark 仍需准备相应 benchmark 自身的 Python 依赖。模型凭据从环境变量读取，
benchmark 数据需本地自备（见各 benchmark 目录的 README）。

## 测试

仓库回归测试使用 `python -m pytest tests/`。

## 文档

`USAGE.md`（完整使用指南）· `plugins/claude-code/README.md`（插件组件）·
`plugins/claude-code/docs/`（版本命名 / 评估协议 / 轨迹格式）。
