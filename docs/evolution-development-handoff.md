# EvoOntology 进化流程开发交接

## 当前目标

将语义层自进化从“由 Skill 自行判断何时结束”的开放式流程，调整为由 core 保证生命周期正确的闭环：Reject 后继续，只有 Accept 或合法 Incomplete 才能结束。

完整设计以 [evolution-productization-design.md](evolution-productization-design.md) 为准；本文只记录开发起点和关键约束。

## 已确认的设计决策

- 新增轻量 `EvolutionSession`，状态只有 `running`、`accepted`、`incomplete`。
- Reject 不结束 Run，不推进 checkpoint，不切换 active 版本。
- Accept 后才发布 Candidate、更新 `active.json`、推进 checkpoint。
- 新 Run 开始时，Skill 必须和用户确认 `max_rounds`；默认建议为 8。预算冻结到 `run.json`，Resume 不重复确认；扩展预算需再次确认。
- workspace 只保存版本、Run 状态、轮次摘要、正式评测摘要和轨迹来源引用；不承担全部日志仓库职责。
- Agent 自主在项目、workspace、配置引用目录和用户指定目录中寻找轨迹。首次发现或来源变化时，先向用户说明并确认范围。
- 每个 Run 将已确认路径写入 `trajectory-sources.json`；只保存引用，不复制轨迹。新 Run 默认参考最近一次记录。
- 不引入 Evidence/EvidenceSource 等新抽象；Adapter 直接返回标准化评测结果。
- 现有 evaluator 默认输出目录保持不变。Adapter 可传输出提示，但 core 不强制所有结果落入 workspace。
- Skill 提供方法论，不堆叠具体命令、固定目录或轨迹格式。

## 建议的最小结构

```text
evoontology/evolution/
├── session.py
└── adapter.py

.evoontology/<workspace_id>/
├── active.json
├── state.json
├── versions/
└── evolution/run_x/
    ├── run.json
    ├── trajectory-sources.json
    ├── rounds.jsonl
    └── evaluations/
```

`run.json` 保存状态、Parent、当前轮次、冻结预算、评测配置和 accepted Candidate。`rounds.jsonl` 每轮追加假设、Candidate、指标、决策和原始产物路径。`evaluations/` 保存 Parent/Candidate 正式评测的稳定 JSON 摘要。

## 最小 Adapter 约定

```python
class EvolutionAdapter(Protocol):
    def evaluate(self, subject, cases=None, output_hint=None) -> dict:
        ...
```

返回至少包含：

```python
{
    "metrics": {...},
    "cases": [{"id": ..., "score": ..., "status": ...}],
    "artifact_paths": [...],
}
```

`cases` 的逐项结果、错误和 trace 仅用于增强诊断；只要有可比较的指标，用户自定义场景也可接入。

## 代码现状与主要缺口

- `evoontology/evaluation/evaluation.py` 只有 Gate 聚合，没有 Run/状态机。
- `evoontology/ontology/store.py` 已支持读取指定版本；但 `runtime.py` 和各 benchmark 仍默认只读 active 版本。Candidate 评测必须补齐显式版本传递，不能临时改 `active.json`。
- `evoontology/trigger/trigger.py` 当前使用 trajectory checkpoint；新 Session 语义应为仅在 Accept 后推进 checkpoint。已有 trajectory 触发能力可兼容保留，不能成为新流程的硬依赖。
- `evoontology/workspace.py` 已创建 `versions`、`trajectories`、`evolution` 目录，可做小幅扩展，不应重写 workspace 系统。
- BIRD 的 `run_evaluation.py` 已有 `--output`，默认写 `results/`；保留默认行为。
- DDR-10K 的生成与评测分为两个程序；Adapter 负责串联，不重写 evaluator。
- InsightBench 的 `main.py run` 已有 `--output-dir`；Adapter 解析现有结果。
- 根目录 `evoontology/` 与 Claude/Codex 插件中都存在 core 副本。根目录应成为唯一源，后续补构建/同步检查，避免手工维护三份。

## 推荐实施顺序

1. 先为 `EvolutionSession` 编写状态迁移测试：Reject 循环、Accept 发布、Incomplete、预算、最终 guard、checkpoint 语义。
2. 实现 `session.py` 与最小 `adapter.py`，同时让状态 JSON 原子写入。
3. 为 runtime 和 benchmark 加入显式 semantic version 选择；验证 Candidate 评测不改变 active。
4. 先实现 BIRD Adapter，使用真实但小规模的已有配置验证结果解析与路径引用。
5. 再实现 DDR-10K、InsightBench Adapter。
6. 最后少量更新 Claude/Codex evolve Skill：恢复 Session、确认预算、发现并确认轨迹来源、遵循 Session 终态。
7. 增加插件 core/Skill 同步机制和回归测试。

## 必须通过的验收

- Candidate Reject 后不能被标为完成，且下一轮仍可开始。
- 只有 Accept 才更新 active 和 checkpoint。
- `incomplete` 仅用于预算耗尽、用户中断、数据/权限缺失或评测不可信等外部条件。
- 新 Run 的预算已得到用户确认并写入 `run.json`；Resume 不重复询问。
- Candidate 评测可指定版本，不修改 `active.json`。
- 正式 Parent/Candidate 评测摘要可从对应 Run 恢复；原始产物只需保留路径引用。
- Agent 可记录用户确认的轨迹来源；没有轨迹时仍可从 Parent baseline 和评测结果启动。
- 三个 benchmark 的普通运行方式和默认输出不被破坏。

## 修改 Skill 时的边界

只补充方法论式要求：启动时恢复 Session、确认预算、发现并确认轨迹来源、独立版本比较、根据 Session 终态结束。不要把 core 的路径、状态迁移、计数逻辑或具体命令复制进 Skill。

## 工作区注意事项

- 本轮仅新增了 `docs/` 下的设计与交接文档，未实现产品代码。
- 当前工作树还存在未提交改动：
  - `plugins/claude-code/.claude-plugin/plugin.json`
  - `plugins/claude-code/scripts/check-reminder.py`
  - `plugins/claude-code/skills/evolve-semantic-layer/SKILL.md`
  - `tests/test_reminder_hook.py`

  它们不应被新会话覆盖或回退，除非先确认其来源和意图。
- 新会话应以 EvoOntology 项目根目录作为 workspace，确保能修改 core、plugins、tests 和 docs。
