---
description: 可视化本体——生成离线、单文件的交互式 HTML
---

## 输入上下文

- **工作区根目录 `<workspace>`**：默认取当前项目的 `.evoontology/`；调用者可用
  `--root <workspace>` 覆盖，指向别的 ontology workspace。
- **版本**：默认可视化 `active.json` 指向的版本；也可显式指定 `semantic_vN`，
  只读渲染，不改变 `active.json`。

## 执行

调用 Core `visualize()`（唯一渲染入口；本命令不包含任何渲染逻辑）：

```bash
python -m evoontology.visualization --root <workspace> [--version semantic_vN]
```

行为约定：

- 只读：不修改 Build / Evolve / Runtime，也不修改 `active.json`、`versions/` 等任何状态；
- 输出 `<workspace>/visualizations/<version>.html`（同一版本重复生成会覆盖），支持时自动打开浏览器；
- 无界面环境可追加 `--no-browser`，仅生成文件；
- 错误显式：workspace 未初始化 / 无 active 版本 / 请求版本不存在；断裂引用只告警，不虚构图对象。

执行成功后只报告生成的 HTML 路径。
