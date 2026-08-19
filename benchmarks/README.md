# Benchmarks

三个 benchmark 接入示例：`bird/`（text-to-SQL）、`ddr_10k/`（自主数据分析）、
`insightbench/`（迭代分析 / 代码生成）。用户准备官方数据后，可用 EvoOntology 插件完整运行
Build → Use → Record → Evolve → Evaluate 闭环。

## 复用 EvoOntology Core

三个 benchmark 的确定性能力统一由仓库根的 `evoontology` 包提供，不重复维护：

| 能力 | 模块 | 接入方式 |
| --- | --- | --- |
| Ontology 存储 / 版本管理 | `evoontology.ontology.store.SemanticStore` | `save_version` / `set_active` / `promote` |
| Semantic Runtime | `evoontology.runtime.runtime.SemanticLayer` | `browse` / `resolve` / `manifest` |
| Semantic MCP | `evoontology.runtime.mcp_server` | `python -m evoontology.runtime.mcp_server --store <workspace>` |
| Trajectory 记录 | `evoontology.trajectory.TrajectoryStore` | `append` 一条 task 轨迹 |
| Evolution Trigger | `evoontology.trigger.EvolutionTrigger` | `check()` / `mark_evolved()` |
| Evaluation 调度 | `evoontology.evaluation.EvaluationGate` | `decide_gt` / `decide_judge` |

每个 benchmark 目录下的 Data Agent、Native Tools、Runner、Evaluator 为该
benchmark 特有实现。数据边界直接复用 benchmark 官方划分，不在仓库中维护二次切分脚本或
预先划分的数据。`tceo/` 中保留 benchmark 特有的 Binder、scope 和 manifest adapter，
但 active-version 选择与五类 JSON 文件门禁统一调用 `SemanticStore.load_records()`；轨迹统一
写入 Core 的 `TrajectoryStore`。BIRD 使用每数据库一个 workspace：
`bird/.evoontology/<db_id>/`，DDR 与 InsightBench 各使用一个 `.evoontology/` workspace。

## 数据准备

仓库不提供 benchmark 原始大型数据、预构建 `semantic_v0` 与预构建 evolved ontology。各
benchmark 的 README 说明官方数据准备方式；准备后运行 `/evo-build` 构建自己的 ontology。
