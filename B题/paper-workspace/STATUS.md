# 数学建模论文能力状态

- 模式：`full-paper`
- 当前阶段：`delivery`
- 下一动作：导出 LaTeX/PDF，完成编译、页面检查和交付记录。
- MCP 是否必需：`false`

| 阶段 | 状态 | 主产物 |
|---|---|---|
| `intake` | `complete` | `00-intake/materials-index.json` |
| `background` | `complete` | `01-background/background-ledger.json` |
| `calibration` | `skipped` | `02-calibration/template-calibration-profile.json` |
| `blueprint` | `complete` | `03-blueprint/paper-blueprint.json` |
| `evidence` | `complete` | `04-evidence/claim-evidence-matrix.json` |
| `drafting` | `complete` | `05-manuscript/manuscript.json` |
| `review` | `complete` | `06-review/quality-report.json` |
| `delivery` | `blocked` | `07-delivery/delivery-manifest.json` |

使用 `paper_workspace.py status` 获取机器可读状态。
