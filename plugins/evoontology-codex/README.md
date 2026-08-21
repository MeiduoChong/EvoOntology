# EvoOntology — Codex Plugin

自包含的 Codex 插件：内置 Builder / Evolver skills、项目指令和语义 MCP 接入，不引用
插件目录之外的文件。

## 组件

| 组件 | 位置 | 作用 |
| --- | --- | --- |
| 全局指令 | `AGENTS.md` | 统一 `/evo-build`、`/evo-evolve`、`/evo-visualize` 触发短语与语义工具用法 |
| MCP 接入 | `.mcp.json` | 自动启动语义 MCP server |
| Skills | `skills/` | `evo-build` / `evo-evolve` / `evo-visualize` 方法 |
| 确定性核心 | `evoontology/` | 内置 core 包（由仓库根经 `scripts/sync_plugin_core.py` 同步） |

## 安装

```bash
codex plugin marketplace add Cmd210/EvoOntology
codex plugin marketplace list
codex plugin add evoontology-codex@evoontology
codex plugin list
```

无需 clone 仓库、创建虚拟环境或单独执行 `pip install`。安装或更新后请新建会话，让 Codex
加载插件中的 skills 与 MCP 配置。

## 接入语义 MCP

插件的 `.mcp.json` 自动注册 `evo-semantic`。默认 workspace 为当前项目的
`.evoontology/`；如需指向别的 workspace，在 args 里追加 `"--store", "<workspace-root>"`。
Core 统一解析该路径，并维护 `project.json`、`active.json`、`state.json`、`versions/`、
`trajectories/` 与 `evolution/`；`state.json` 使用 `checkpoint_time` 和
`checkpoint_trajectory`。

## 使用

安装后，在 Codex 会话中：

- 说「构建语义层」或 `/evo-build` —— 按 `evo-build` skill 构建 `semantic_v0`；
- 说「进化语义层」或 `/evo-evolve` —— 按 `evo-evolve` skill 执行
  诊断 → 归因 → 补丁 → Parent/Candidate gate。进化由 `EvolutionSession` 驱动：
  新 run 先确认轮数预算（默认 8）与轨迹来源，Reject 在同一 run 内继续下一轮，
  直到 Accept 发布新版本并推进 checkpoint。
- 说「可视化语义层」或 `/evo-visualize` —— 按 `evo-visualize` skill 生成离线交互图。

Codex 原生 skill 调用写作 `$evo-build`、`$evo-evolve`、`$evo-visualize`；本文中的
`/evo-*` 是统一到 Claude Code 命令名的触发短语。实际构建 / 进化流程见本目录
`skills/` 下的三份 SKILL.md。

## 两种 mode

- `fixed_split`：用于已有固定问题集、GT 与官方评测边界的 benchmark；Construction Pool
  用于构建和诊断，Validation Reserve 只用于最终 Gate。
- `rolling_trajectory`：用于真实业务或冷启动；seed workload 初始化语义层，后续按 checkpoint
  收集新 task trajectory。没有 GT 时使用独立任务抽样和 LLM Judge，无需强行划分 Fold A/B。

mode 在 Build Step 0 确认并写入 `project.json`，Evolve 直接复用。
