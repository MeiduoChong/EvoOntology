---
description: 触发进化——诊断→归因→补丁→Parent/Candidate gate→落地
---

## 输入上下文

本命令是触发指令，不是确定性操作；evolve 的实际执行者是按 skill 行动的 agent。agent 需要
三处输入，均来自当前项目上下文（由调用者提供）：

- **工作区根目录 `<workspace>`**：默认取当前项目的 `.evoontology/`；调用者可用
  `--root <workspace>` 覆盖，指向别的 ontology workspace。
- **项目上下文**：复用 `<workspace>/project.json` 中已确认的数据源、Evaluator 和数据边界。
- **工作量（workload）**：Evolver 只使用本轮冻结的 Evolution Pool；Validation Reserve
  仅在正式 Gate 时开放，ground truth 只能由指定 Evaluator 读取。

本命令中的 `<workspace>` 始终指 Core `resolve_workspace()` 解析后的目录；每次命令只执行
一轮 evolution，Validation Reserve 一旦用于正式 Gate，本轮即以 Accept、Reject 或
Incomplete 结束。

## 执行

执行 `evolve-semantic-layer` skill（`skills/evolve-semantic-layer/`），触发一次进化循环。

按 skill 的 Evolution Loop 执行：Diagnose → Attribute → Patch → Evaluate/Gate。评估协议见
`docs/evaluation-protocol.md`（有 GT 绝对评分 / 无 GT LLM Judge 相对比较）。

正式 Gate 前将候选保存为 `vN-cK`，并用以下命令校验，不改变 `active.json`：

```bash
python -m evoontology.validate --root <workspace> --version <candidate>
```

Accept 后按
`docs/versioning.md` 发布为 `semantic_vN+1`；Reject 保留 Parent。Accept/Reject 都先写完
`evolution/<round>/result.json`，再通过 Core 推进 checkpoint；Incomplete 不推进。
