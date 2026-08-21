---
description: 可视化本体——生成离线、单文件的交互式 HTML
---

## 输入上下文

- **工作区根目录 `<workspace>`**：默认取当前项目的 `.evoontology/`；调用者可用
  显式的 workspace 绝对路径覆盖，指向别的 ontology workspace。
- **版本**：默认可视化 `active.json` 指向的版本；也可显式指定 `semantic_vN`，
  只读渲染，不改变 `active.json`。

## 执行

调用 `evo-semantic` MCP 的 `visualize_semantics` 工具（唯一渲染入口；本命令不包含任何渲染逻辑）。
`workspace` 传当前项目的 `.evoontology/` 绝对路径，`version` 省略表示 active，或传 `semantic_vN`。
不要在本命令中运行 `python -m evoontology.visualization`。

行为约定：

- 只读：不修改 Build / Evolve / Runtime，也不修改 `active.json`、`versions/` 等任何状态；
- 输出 `<workspace>/visualizations/<version>.html`（同一版本重复生成会覆盖）；MCP 工具只生成文件，不自动打开浏览器；
- 错误显式：workspace 未初始化 / 无 active 版本 / 请求版本不存在；断裂引用只告警，不虚构图对象。

执行成功后只报告生成的 HTML 路径。
