# EvoOntology 进化流程产品化设计

## 1. 目标与原则

本次调整的目标是让语义层进化形成稳定闭环，同时保持现有产品结构和 benchmark 评测方式基本不变。

设计原则：

- 核心流程必须正确：Reject 后继续迭代，只有获得可信改进才成功结束。
- 核心能力与产物位置解耦：不要求所有日志、评测和轨迹集中到同一个 workspace。
- 少配置：提供保守默认值，仅在目标、验收标准或成本明显不确定时询问用户。
- 少侵入：复用现有 evaluator，通过轻量 adapter 接入。
- Skill 负责方法论，core 负责状态、预算和流程约束。

## 2. 总体架构

```text
Skill / Agent
  查找轨迹、诊断、归因、提出 Candidate
            │
            ▼
EvolutionSession
  状态、轮次、预算、Gate、发布
            │
            ▼
Benchmark Adapter
  调用现有评测并返回统一结果
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
    BIRD  DDR-10K InsightBench
```

Skill 决定“为什么改、改什么”；EvolutionSession 保证“流程不会违规结束”；Adapter 负责“如何在具体场景中运行和评分”。

## 3. EvolutionSession

新增轻量模块：

```text
evoontology/evolution/
├── session.py
└── adapter.py
```

`session.py` 负责：

- 管理 `running / accepted / incomplete` 状态；
- 保存 Parent、当前 Candidate 和轮次；
- Reject 后保持运行并进入下一轮；
- 达到预算或遇到外部阻塞时标记 `incomplete`；
- 最终返回前校验状态；
- Candidate 接受后安全发布并推进 checkpoint。

状态规则：

```text
running ── Reject ──> running（下一轮）
running ── Accept ──> accepted
running ── 外部阻塞或预算耗尽 ──> incomplete
```

Reject、没有有效假设或单轮实验结束都不是整个任务的完成条件。

## 4. 最小持久化状态

Workspace 只保存语义版本和进化控制状态：

```text
.evoontology/<workspace_id>/
├── active.json
├── state.json
├── versions/
└── evolution/
    └── run_x/
        ├── run.json
        ├── trajectory-sources.json
        ├── rounds.jsonl
        └── evaluations/
```

`run.json` 保存当前 Run 的状态、Parent、轮次、预算、adapter 和验收配置。`rounds.jsonl` 每轮追加一条摘要，包括假设、Candidate、指标、决策和外部产物引用。`evaluations/` 保存正式 Parent/Candidate 评测的稳定结果摘要。

大型原始日志和 trace 可以保留在 benchmark 或用户指定的位置。Workspace 只保存持续比较和恢复所需的评测摘要与文件引用，不复制全部原始产物。

## 5. Adapter 接口

Adapter 接口保持最小化：

```python
class EvolutionAdapter(Protocol):
    def evaluate(self, subject, cases=None, output_hint=None) -> dict:
        ...
```

返回结果至少包含：

```python
{
    "metrics": {...},
    "cases": [{"id": ..., "score": ..., "status": ...}],
    "artifact_paths": [...]
}
```

只要能够返回可比较指标，用户自己的场景就可以接入。逐项结果和原始产物路径用于增强诊断，但不要求统一日志格式。

现有 benchmark 仅需新增轻量 adapter，并支持显式选择语义版本。默认输出目录和 evaluator 内部逻辑保持不变。

## 6. Trajectory 的发现与固化

Trajectory 由 Agent 在当前项目、workspace、配置引用位置和用户指定位置中自主查找，不要求统一存入 `.evoontology/trajectories/`，也不要求统一格式。

首次找到或来源发生变化时，Agent 应简要说明路径、内容范围、时间和用途，并与用户确认使用范围。Resume 同一个 Run 时不重复确认。

确认后的来源写入：

```text
.evoontology/<workspace_id>/evolution/<run_id>/trajectory-sources.json
```

文件只记录来源，不复制轨迹：

```json
{
  "sources": [
    {
      "path": "benchmarks/bird/results/semantic/...",
      "scope": "33 evaluation tasks",
      "purpose": "diagnosis",
      "confirmed_at": "2026-08-20T11:30:00Z"
    }
  ]
}
```

新 Run 默认参考最近一次 Run 的来源记录，验证路径仍然有效；只有来源新增、失效或范围变化时才再次确认。没有找到轨迹时，可以先运行 Parent baseline，并根据评测结果、错误和反例开始诊断。

现有 `TrajectoryStore` 和 benchmark 轨迹记录能力暂时保留兼容，但 EvolutionSession 不直接依赖它。暂不建设统一 trajectory 中心、通用导入器或评测结果回填机制。

## 7. 版本与发布

评测 Parent 和 Candidate 时必须显式指定语义版本，不通过临时修改 `active.json` 切换版本。

Candidate 接受后：

1. 验证 Candidate；
2. 发布为新的正式版本；
3. 更新 `active.json`；
4. 推进 evolution checkpoint；
5. 将 Run 标记为 `accepted`。

Reject 或 Incomplete 不更新 active 版本，也不推进 checkpoint。发布操作应避免覆盖已有正式版本，并支持失败后安全重试。

## 8. 默认预算

第一版只提供一个核心预算：

```json
{"max_rounds": 8}
```

一轮对应一个正式 Candidate。达到上限仍未通过 Gate 时，Run 标记为 `incomplete / budget_exhausted`。

预算优先级：

```text
本次运行参数 > 项目可选配置 > 默认值 8
```

创建新的 Evolution Run 时，Skill 应向用户说明本次计划使用的 `max_rounds` 并取得确认，再将其冻结到 `run.json`。默认值 8 是确认建议，不是未经确认直接采用的执行授权。

Resume 同一个 Run 时沿用已确认预算，不重复询问。预算耗尽后如需增加轮数，必须再次取得用户确认并更新 Run 记录。

## 9. Skill 调整原则

Skill 保留方法论指导：

- 主动查找相关轨迹、评测结果和执行日志，并确认其适用范围；
- 先归因，再设计修改；
- 一个 Candidate 验证一个主要假设；
- Parent/Candidate 在受控条件下比较；
- Reject 后根据新证据继续探索；
- 只有可信、可复现且无不可接受回归的改进才算成功。

Skill 只需少量补充：

- 开始时恢复已有 EvolutionSession；
- 创建新 Run 时，与用户确认执行轮数预算；
- 查找轨迹；使用范围尚未确定时，向用户确认并保存来源记录；
- Candidate 使用独立版本评测，不修改 active 版本；
- 最终报告以 Session 的终态和已保存结果为准。

Skill 不规定具体搜索命令、固定轨迹格式或详细目录操作。状态迁移、预算计数、来源文件写入和最终校验由 core 实现。Claude Code 与 Codex 使用同一份方法论内容和共享 core，仅保留薄入口。

## 10. 实施范围

第一版实施：

- EvolutionSession、状态机和最终校验；
- 默认轮次预算；
- `run.json`、`trajectory-sources.json`、`rounds.jsonl` 和正式评测摘要；
- 显式语义版本加载；
- 安全发布和 accepted-only checkpoint；
- BIRD、DDR-10K、InsightBench 的轻量 Adapter；
- Claude/Codex Skill 的少量同步调整；
- 根 core 与插件副本的构建同步。

第一版不实施：

- 强制所有结果进入 workspace；
- 统一 trajectory 中心、固定轨迹格式和通用日志导入；
- 复杂 Candidate 目录和实验数据库；
- Git worktree、任务队列和独立调度系统；
- 大量可配置预算和运行参数。

## 11. 验收标准

- Candidate Reject 后 Run 不会被错误结束；
- 达到成功条件前只能保持 `running` 或合法转为 `incomplete`；
- 新 Run 的执行轮数经用户确认并冻结，Resume 不重复确认；
- Candidate 可以在不修改 active 版本的情况下评测；
- Accept 后才更新 active 和 checkpoint；
- Agent 能发现轨迹、确认使用范围，并在后续 Run 中复用来源记录；
- 正式 Parent/Candidate 评测摘要保存在对应 Evolution Run 中；
- 三个现有 benchmark 可通过 Adapter 返回统一结果；
- 用户场景只提供可比较指标和可选逐项结果即可接入；
- 普通 benchmark 的原有运行方式和默认输出不受影响。
