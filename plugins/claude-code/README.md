# EvoOntology — Claude Code Plugin

把 EvoOntology 打包成 Claude Code 插件：提供 `/evo-build`、`/evo-evolve` 两个命令、
builder / evolver 两个 skill、语义 MCP 运行时，以及 Session Start 进化提醒。

## 组件

| 组件 | 位置 | 作用 |
| --- | --- | --- |
| Build 命令 | `commands/evo-build.md` | `/evo-build` 构建 `semantic_v0` |
| Evolve 命令 | `commands/evo-evolve.md` | `/evo-evolve` 触发进化 |
| Builder skill | `skills/build-semantic-layer/` | 构建初始语义层 |
| Evolver skill | `skills/evolve-semantic-layer/` | 诊断 → 归因 → 补丁 → gate |
| MCP 配置 | `.mcp.json` | 语义 MCP server 自动接入（零配置） |
| 进化提醒 | `hooks/hooks.json` + `scripts/check-reminder.py` | Session Start 检查 evolution_due |

语义 MCP 与确定性能力（store / runtime / trajectory / trigger / evaluation）统一由
仓库根的 `evoontology/` 包提供，本插件不重复维护运行时。

## 安装

```bash
claude plugin marketplace add Cmd210/EvoOntology
claude plugin marketplace list
claude plugin install evoontology@evoontology
claude plugin list
```

无需 clone 仓库、创建虚拟环境或单独执行 `pip install`。`marketplace list` 用于确认 Marketplace 已添加，
`plugin install` 才会下载插件，`plugin list` 用于确认最终安装状态。安装完成后 build / evolve
命令、两个 skill、语义 MCP 与进化提醒自动就位。

## 使用

安装后可用两个触发命令：

- `/evo-build` —— 读数据、探索 schema、生成五类记录，发布 `semantic_v0`；
- `/evo-evolve` —— 诊断 → 归因 → 补丁 → Parent/Candidate gate → 落地。

两者是触发指令，实际构建 / 进化由 agent 按对应 skill 执行。

### 两种 mode

- `fixed_split`：用于已有固定问题集、GT 与官方评测边界的 benchmark；Construction Pool
  用于构建和诊断，Validation Reserve 只用于最终 Gate。
- `rolling_trajectory`：用于真实业务或冷启动；seed workload 初始化语义层，后续按 checkpoint
  收集新 task trajectory。没有 GT 时使用独立任务抽样和 LLM Judge，无需强行划分 Fold A/B。

mode 在 Build Step 0 确认并写入 `project.json`，Evolve 直接复用。

### 语义 MCP

`.mcp.json` 以模块形式 spawn 语义服务，client 自动拉起。默认 workspace 为当前项目的
`.evoontology/`（零配置）；如需指向别的 workspace，在 `.mcp.json` 的 args 里追加
`"--store", "<workspace-root>"`。Data Agent 可见 `browse_semantics`、`resolve_semantics`
两个工具与 `evo-semantic://session-manifest` 资源。

### 进化提醒

每次 Session Start，`check-reminder.py` 读取 `<cwd>/.evoontology/state.json` 与
`trajectories/`，达到触发条件（默认 30 个新 task 或 7 天）时向会话注入提醒，用户自行决定
是否执行 `/evo-evolve`。不自动启动进化。

`state.json` 使用中性的 `checkpoint_time` / `checkpoint_trajectory`：首次基线是
`semantic_v0` 发布时间，完成正式 Gate 的 Accept/Reject 才推进 checkpoint。

## 发布校验（agent 自动）

`/evo-build`、`/evo-evolve` 发布新版本前，agent 会自动调用 `python -m evoontology.validate` 做确定性
门禁（JSON 合法 / 引用完整 / 可加载），用户无需手动执行。仅手动诊断 workspace 时才直接运行：

```bash
python -m evoontology.validate --root <workspace-root>

# 校验尚未激活的初始版本或 Candidate
python -m evoontology.validate --root <workspace-root> --version <version>
```

只做结构校验，不做数据库语义校验。
