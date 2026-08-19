# EvoOntology 产品化使用指南

本文档说明产品化完成后，如何实际使用 EvoOntology。产品化把散落在三个 benchmark 里的
通用能力抽取为一个**核心包** `evoontology/`（确定性能力），并配两套 harness 适配：

- `evoontology/` —— 与 benchmark 无关的产品运行时：ontology store / runtime(MCP) /
  trajectory / trigger / evaluation / validate 门禁。
- `plugins/` —— Claude Code 插件（两命令 + 两 skill + MCP + reminder）
  与 Codex 适配层。

产品最终形态 = 一个核心包（含 validate 门禁）+ 两个 skill 命令，无 CLI。智能分析全在
skill，Python 只做「运行时 + 最小确定性校验」。默认**零配置**：不要求用户填写 workspace
路径、Evaluation Mode、Judge 模型或 Trigger 参数。

---

## 1. 安装

请选择正在使用的客户端，通过 Marketplace 安装；无需 clone 仓库、创建虚拟环境或单独运行
`pip install`。

### Claude Code

```bash
claude plugin marketplace add Cmd210/EvoOntology
claude plugin marketplace list
claude plugin install evoontology@evoontology
claude plugin list
```

### Codex

```bash
codex plugin marketplace add Cmd210/EvoOntology
codex plugin marketplace list
codex plugin add evoontology-codex@evoontology
codex plugin list
```

Marketplace 添加成功但不等于插件已经安装；请以最后一条 `plugin list` 中显示 installed/enabled
为准。安装或更新后新建会话，再运行 `/evo-build`。

---

## 2. 一个 workspace 长什么样

workspace 默认是项目根的 `.evoontology/`，首次 `/evo-build` 时自动创建：

```
.evoontology/
├── project.json         # mode / data source / workload / evaluator / boundary
├── active.json          # {"active_version": "semantic_v0"}
├── versions/            # 所有版本（正式 semantic_vN + 候选 vN-cK），每版本 5 个 JSON
├── trajectories/        # 每个任务一条 JSON trajectory
├── evolution/           # 每轮 context.json + result.json
└── state.json           # Trigger checkpoint 与阈值
```

每版本下是 5 个记录文件，对应五类对象：Term / Mapping / Relation / Constraint /
Evidence。轨迹由 Data Agent 运行时（benchmark adapter 侧）在每次任务结束时追加到
`trajectories/`。

Workspace 分阶段初始化：Step 0 确认后写 `project.json`；初始版本保存并通过
`python -m evoontology.validate --version semantic_v0` 后，才写 `active.json` 和
`state.json`。Core 默认解析 `<project-root>/.evoontology/`，benchmark 可显式传入其他路径。

### 选择 mode

- `fixed_split`：用于已有固定问题集、GT 和评测边界的 benchmark。Construction Pool 用于
  Build/诊断，Validation Reserve 只用于最终 Gate。优先复用官方划分，不额外生成随机 Fold。
- `rolling_trajectory`：用于真实业务或冷启动。先用 seed workload 初始化，之后按 checkpoint
  持续收集新的 task trajectory；没有 GT 时通过独立任务抽样和 LLM Judge 比较 Parent/Candidate，
  不需要强行划分 Fold A/B。

mode 在 Step 0 确认后写入 `project.json`，后续 Build 和 Evolve 共用，避免每轮重新判断。

---

## 3. 触发指令

| 指令 | 语义 | 执行者 |
| --- | --- | --- |
| `/evo-build` | 构建 semantic_v0：读数据、探索 schema、生成五类记录 | agent 按 build skill |
| `/evo-evolve` | 触发进化：诊断→归因→补丁→Parent/Candidate gate→落地 | agent 按 evolve skill |

两者都是**触发指令**，不是 Python 确定性操作；真正的构建 / 进化由 agent 按 skill 执行。
版本命名与切换约定见 `plugins/claude-code/docs/versioning.md`（正式 `semantic_vN`、
候选 `vN-cK`，accept 映射 `vN-cK` → `semantic_vN+1`）。

---

## 4. 配置（零配置）

产品默认零配置，无 `config.yaml`。用户需要调整时直接告诉 Claude / Codex（例如「以后每
60 个任务提醒我一次」），由 agent 更新 `state.json` 内部状态，不改配置文件。

- 进化触发默认：checkpoint 后新增 ≥ 30 个 task，或距 checkpoint ≥ 7 天。首次 checkpoint
  是 `semantic_v0` 发布时间；完成正式 Gate 的 Accept/Reject 会推进 checkpoint，Incomplete
  不推进。
- 评估协议自动选择：benchmark 提供 Evaluator（Ground Truth）时走 GT；否则走 LLM Judge
  （见 `plugins/claude-code/docs/evaluation-protocol.md`）。

---

## 5. MCP 接入

插件通过 `.mcp.json` 以模块形式 spawn 服务，client 自动拉起、无需手动起服。默认
workspace 为当前项目的 `.evoontology/`（零配置）：

```bash
python -m evoontology.runtime.mcp_server
```

接入后 Data Agent 可见：

- 工具 `browse_semantics(query, kind, limit)` —— 发现相关概念；
- 工具 `resolve_semantics(mentions, context)` —— 解析概念到 grounding 的 mapping +
  关联的 relation / constraint / evidence；
- 资源 `evo-semantic://session-manifest` —— 会话开始时读取的简洁说明。

手动起服（验证用）：

```bash
python -m evoontology.runtime.mcp_server --store <workspace-root>
```

这两个工具返回的是元数据与指引，数据库查询与 Python 执行仍由 benchmark 原生工具负责。

---

## 6. validate 门禁（agent 自动）

`/evo-build`、`/evo-evolve` 发布新版本前，agent 会自动调用 `python -m evoontology.validate` 做确定性
门禁（JSON 合法 / 引用完整 / 可加载），用户无需手动执行。仅手动诊断 workspace 时才直接运行：

```bash
python -m evoontology.validate --root <workspace-root>

# 发布前校验尚未激活的初始版本或 Candidate
python -m evoontology.validate --root <workspace-root> --version <version>
# → {"passed": true, "root": "...", "version": "semantic_v0", "errors": []}
```

validate 只做结构校验，不做数据库语义校验（表字段存在 / Mapping 可执行 / Evidence 可复现
是 Builder 探索阶段已做的事）。

---

## 7. 一个最小端到端流程

```bash
# 1. 按第 1 节通过 Claude Code 或 Codex Marketplace 安装插件

# 2. 触发构建 semantic_v0（在客户端会话里输入）
/evo-build

# 3. Data Agent 通过 MCP 接入（.mcp.json 声明，client 自动 spawn，无需手动起服）

# 4. 触发进化（或等待轨迹达到阈值后的提醒）
/evo-evolve        # agent 诊断→补丁→gate；accept 后 agent 自行发布（改 active.json）
```

agent 发布前会自动调用 `python -m evoontology.validate` 做门禁。

---

## 8. 边界（一期不做）

Web UI / SaaS / 多租户 / 消息队列 / 常驻 worker / 多 Candidate 并行 / 自动循环 / 高频改
schema 均不在本版范围。无人值守全自动进化需要常驻后台 worker，一期只做「检测 + 提醒」，
由人触发。
