---
description: 构建 semantic_v0——读数据、探索 schema、生成 5 类记录
---

## 输入上下文

本命令是触发指令，不是确定性操作；build 的实际执行者是按 skill 行动的 agent。agent 需要
三处输入，均来自当前项目上下文（由调用者提供）：

- **工作区根目录 `<workspace>`**：默认取当前项目的 `.evoontology/`（首次运行自动创建）；
  调用者可用 `--root <workspace>` 覆盖，指向别的 ontology workspace。
- **项目上下文**：首次构建时由 skill 确认数据源、workload、Evaluator 和数据边界，并保存到
  `<workspace>/project.json`；后续复用，不重复猜测。
- **允许的工作量（workload）**：Fixed-Split Mode 使用冻结的 construction subset；
  Rolling-Trajectory Mode 使用 seed workload。Builder 不得读取保留验证数据或 ground truth。

本命令中的 `<workspace>` 始终指 Core `resolve_workspace()` 解析后的目录；skill 中出现的
`.evoontology/` 表示这个默认 Workspace，而不是另行拼接的第二个目录。

## 执行

执行 `build-semantic-layer` skill（`skills/build-semantic-layer/`），构建初始语义层。

按 skill 的 Builder Workflow 执行：Workload-Guided Probing → Evidence-Grounded
Commitment，产出 Term / Mapping / Relation / Constraint / Evidence 五类记录，发布为
`semantic_v0`。

发布时先保存 `versions/semantic_v0/`，再调用下面的命令校验尚未激活的版本：

```bash
python -m evoontology.validate --root <workspace> --version semantic_v0
```

校验通过后才将 `active.json` 指向 `semantic_v0`。

发布成功后调用下面的幂等初始化命令，从 `semantic_v0` 发布时刻开始计算首次进化的时间阈值：

```bash
python -c "from evoontology import EvolutionTrigger; EvolutionTrigger(r'<workspace>').initialize()"
```

该命令写入首次提醒所需的 `checkpoint_time`，并保持 `checkpoint_trajectory` 为空；如果状态
已经存在，则保留已有 checkpoint、trajectory 与自定义阈值。
