---
description: 可视化本体——生成离线、单文件的交互式 HTML
---

## 输入上下文

- **工作区根目录 `<workspace>`**：默认取当前项目的 `.evoontology/`；调用者可用
  显式的 workspace 绝对路径覆盖，指向别的 ontology workspace。
- **初始版本**：默认打开 `active.json` 指向的版本；也可显式指定 `semantic_vN`，
  只改变页面初始选择，不改变 `active.json`；页面会嵌入全部可用版本并支持切换与对比。

## 执行

调用 `evo-semantic` MCP 的 `visualize_semantics` 工具（唯一渲染入口；本命令不包含任何渲染逻辑）。
`workspace` 传当前项目的 `.evoontology/` 绝对路径，`version` 省略表示 active，或传 `semantic_vN`；
`open_browser` 默认 true（生成后自动在默认浏览器中打开），仅当用户明确要求不打开时传 false。
不要在本命令中运行 `python -m evoontology.visualization`。

行为约定：

- 只读：不修改 Build / Evolve / Runtime，也不修改 `active.json`、`versions/` 等任何状态；
- 输出唯一稳定文件 `<workspace>/visualizations/index.html`（重复生成会覆盖）；MCP 工具生成文件后默认自动在默认浏览器中打开（传 `open_browser: false` 可关闭）；
- 错误显式：workspace 未初始化 / 无 active 版本 / 请求版本不存在；断裂引用只告警，不虚构图对象。

执行成功后报告生成的 HTML 路径（默认已在浏览器中自动打开）。

注意：MCP 工具已自动在默认浏览器中打开该页面一次；不要再用任何方式（如 `Start-Process` / `explorer` / `open` 或应用内浏览器）重复打开同一 HTML，否则会出现两个重复标签页。
