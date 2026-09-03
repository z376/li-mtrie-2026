# li-mtrie-2026

**数模国赛/美赛 端到端 skill: 5 步状态机 + 10 章论文模板 + 2026 规范 (MIT)**

读题 → 建模 → 求解 → 写论文 → 双版编译，一条龙。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version v1.5.2](https://img.shields.io/badge/version-v1.5.2-blue.svg)](CHANGELOG.md)
[![Smoke Test](https://github.com/z376/li-mtrie-2026/actions/workflows/smoke-test.yml/badge.svg)](.github/workflows/smoke-test.yml)
[![2026 Spec](https://img.shields.io/badge/2026%E8%A7%84%E8%8C%83-%E5%AF%B9%E9%BD%90-green.svg)](references/合规检查清单.md)

按 2026 年全国大学生数学建模竞赛《论文格式规范（2026 年修订稿）》+《人工智能工具
使用规定（2026 年试行）》做了对齐更新。

## 适用场景

- 全国大学生数学建模竞赛（**国赛**，A/B/C/D/E 题）
- 美赛 / 校赛 / 其它数学建模类竞赛（结构基本通用）

触发词：`开始求解`、`跑题`、`做数模`、`生成论文`、`出论文 PDF` 等。

## 核心特性

- **2026 规范全对齐** — 摘要中文、不要目录、正文 ≤ 30 页、附录两段固定说明、
  AI 工具使用声明在参考文献之前、详情 PDF 在支撑材料
- **双版编译** — `论文.tex`（纸质版，含承诺书+编号页）+ `电子版.tex`（电子版，
  不放承诺书/编号页），分别产出 `论文.pdf` 和 `电子版.pdf`
- **完整工作流** — 五步走：读题 → 求解计划（多模型比选）→ 逐题求解 → 写论文 →
  编译排版
- **10 章论文结构** — 摘要/引言/总体分析/模型假设/符号说明/建模求解/模型检验/
  模型评价/改进推广/参考文献/附录
- **赛前学习清单** — 6 大题型映射 + 30+ 算法清单 + 60/30/7 天速成路径 + 跑题红线
  （`references/赛前学习清单.md`）

## v1.5.2 新增（2026-09-03, PyMuPDF ≥1.24 fitz deprecate 兼容 + LaTeX 全绿 + writing-for-agents 二轮审计）

**Part A — `fix(scripts)` fitz deprecate 兼容** (commit 087fea2):
- `verify_pdf_metrics.py` + `visual_qa.py` 改 `try/except` 双 import: 优先 `import pymupdf as fitz` (PyMuPDF ≥1.24 推荐), fallback `import fitz` (老版本)
- 验证: 2 脚本 py_compile OK, pymupdf 1.28.2 实际跑通 24 页 PDF, 警告消失
- 向后兼容: 老 PyMuPDF <1.24 走 fallback, 不破坏

**Part B — `fix(论文)` LaTeX Overfull 全绿** (commit 9b63e6b, 6 文件):
- 11 Overfull → 0: 4.符号说明 longtable 列宽 / 5.1.1 集中优化拆 2 equation / 5.1.2 enumerate→align* / 6.模型检验 5 列表 92%→80% / 9.参考文献 sloppypar / 10.附录 verbatim 换行
- **sign-off 全绿**: 论文.pdf 24 页 + 电子版.pdf 22 页 = **0 Overfull**; AI详情.pdf 6 页 = 4 Overfull < 5 判据绿

**Part C — writing-for-agents 二轮审计 4 项整改** (commit c7ecb34, audit 7.5→7.8):
- **P3-4** `green`/`red` 锚定: SKILL.md 顶部 'checkable 红/绿' → 'green/red 二元' (pretrained 视觉 prior 替代自造词)
- **P3-3** 工具 01 ↔ 04-M1 双向链接: 调用链清晰 (粗筛→细评→格式自查→终评)
- **P3-1** 绘图规范 vs 绘图避坑 显式分工 (How / What Not), 学生不再翻错文档
- **P3-5** 角色Prompt.md 5 处 negation 改 positive (agent 实际 prompt 行为更明确)
- **P3-2 留作后续** (workflow.md + paper-spec.md 删 5 步状态机重复段, 工作量 0.5 天)

---

## v1.5.1 新增（2026-09-03, 借鉴 BZD 数模社 3 个核心 skill, 4 个新文件）

- **`references/模型字典使用指南.md`**（6.9 KB）— 11 维评估 + 4 档判定（合适/有条件合适/不合适/证据不足）+ 6 类指标 routing（分类/回归/时序/聚类/优化/评价/机理）。借鉴 BZD `bzd-model-dictionary` v1.0
- **`references/格式自查清单.md`**（9.5 KB）— 12 章节 Markdown 报告 + 100+ 原子检查点 + 15 分逐项扣分制 + 国赛特殊规则（无目录/30 页/附录分板块）。借鉴 BZD `bzd-paper-format-checker` v1.0
- **`references/百分制评审方法.md`**（6.5 KB）— 100 分制（摘要 10 + 格式 10 + 模型/求解/结果 70-75 + 补充 5-10）+ 90% 封顶 + 1/2/3 档扣分 + 格式质量系数（deterministic）+ 位次估计（CUMCM 用 2025 锚点 / 其他用均匀近似）。借鉴 BZD `bzd-review-paper` v1.0
- ⚡ **`llm-prompts/04-百分制评审.md`**（12.4 KB）— 3 模式 LLM 工具：**M1 字典预查**（选模型时）/ **M2 格式自查**（写完后）/ **M3 百分制评审**（终审前）。把 3 个方法论包装成 3 套结构化 prompt，学生 copy-paste 自用

**总览**:
- 4 个新文件（3 references + 1 llm-prompt）
- 借鉴源扩到 7 个外部 skill（BZD 3 个加入：model-dictionary + paper-format-checker + review-paper）
- 闭环：`references/方法论` + `llm-prompts/工具` 双向引用, 工具 04 的 3 模式分别对应 3 个方法论

---

## v1.5.0 新增（15 commits, 2026-08-27 → 08-31, 在 v1.4.4 13 commits 之上）

> v1.4.4 阶段（13 commits）已合入本节上半段；v1.5.0 阶段（2 commits, LLM 工具集成 + GBK fix）见尾部 ⚡ 标记。

- **`论文/figures/` 10 张示例图**（借鉴 数模陪跑独家）+ `论文/figures/README.md` 三件必做警告（整图替换 / 删图题来源 / 检查图例）
- **`\showteaching` 教学开关宏** — 3 个文件 (论文/电子版/AI详情) 统一
- **AI 工具使用声明 二者择一模板** — 对齐 2026 官方简洁版 Word
- **国奖级硬性指标**（`references/国奖级硬性指标.md`）— 6 类数字门槛 + 26 条自查表
- **去AIGC指南**（`references/去AIGC指南.md`）— 降重 4 层法 + 9 类痕迹 + 6 类代码特征 + **4 铁律 + 3 轮协议**（借鉴 aigc-reduce v1.0）
- **绘图避坑 + 图型选择决策**（借鉴 scipilot-figure-skill）— 18 条可视化陷阱 + 决策三轴（变量数/论证意图/数据规模）
- **整题建模模式 + 策略输出规范**（借鉴 bzd-modeling-ideas）— 5 跨问题架构 + 7 题型路线 + 每道题 4 段式分析（问题概述/总体思路/模型比选/创新方向）
- **跨题工具 + 验收清单 + 角色Prompt**（借鉴 mma v3.3）— 3 utility 函数 (GBK 兼容 + utf-8-sig CSV) + 38+ 项验收 + 4 角色 prompt 模板
- **题意红线**（`references/题意红线.md`）— 4 条最高优先级教训
- **verify_pdf_metrics.py**（`references/scripts/`）— 终审前 PDF 6 项程序化体检
- **编号体系 v7**（`paper-spec.md §三.6`）— 章节/列表罗马/公式 三档区分
- **跨平台代码红线 + 代码完整性铁律** — SKILL.md + 10.附录.tex 双写
- **writing-for-agents 6 维度审计** — workflow.md 砍 149 行重复 + 4 处 negation 改 positive
- ⚡ **LLM 工具集成**（`references/llm-prompts/`）— 3 个结构化 prompt 工具（选题推荐 / 代码修复 / 自动审稿）+ README 总览。不调外部 API，copy-paste 到 Mavis/Claude/GPT 即可。**96 小时救星**：traceback → 根因 + 最小修复 + 验证步骤（debug 30% 时间节约 8-10 小时）
- ⚡ **verify_pdf_metrics.py GBK fix**（commit 8866cbc, hotfix）— Windows GBK PowerShell 5.1 跑 emoji 不再乱码/崩溃，stdout/stderr reconfigure utf-8

详细变更见 `CHANGELOG.md` (v1.4.4 + v1.5.0 条目覆盖 15 commits 累计)。

## 快速上手

**先选包** (`默认完整包`):
- **完整包** (~22 MB, 含思源宋体) — 开箱即用, 编译无需装字体 → **推荐** (默认)
- **轻量包** (~4 MB, 不含字体) — 适合分享/上传, 编译需自装思源宋体

1. 把赛题 PDF 放到 `题目/`，数据放到 `数据/`
2. 跟 skill 说"开始求解"
3. skill 会自动：判题组（本科 ABC / 高职 DE）→ 读题读数据 → 列候选模型 → 等你
   选方案 → 求解 → 写论文 → 编译两份 PDF
4. 输出：
   - `论文/论文.pdf` — 纸质版提交用
   - `论文/电子版.pdf` — 电子版提交用
   - `支撑材料.rar` — 全部源码、数据集、中间图（≤ 20MB）
   - `支撑材料/AI工具使用详情.pdf` — 用了 AI 必填

## 目录结构

```
li-mtrie-2026/
├── SKILL.md                  # 入口（被 skill 系统加载）
├── README.md                 # 本文件（项目说明 + 目录结构权威源）
├── 测试报告.md                # 4 轮端到端测试记录
├── references/                # 复用层（按需查阅）
│   ├── workflow.md           # 详细工作流 + 论文硬性规则
│   ├── paper-spec.md         # 论文 10 章详细规范 + 8 项一致性自检
│   ├── 合规检查清单.md       # 4 类硬规则 + 一键验证命令 + 提交物清单
│   ├── code-template.py      # 数据驱动题模板（含 save_fig_with_qa）
│   ├── mechanism-template.py # 机理题模板（含 gen_handle_names）
│   ├── 绘图规范.md           # matplotlib/seaborn/plotly 字号/线宽/DPI 规范
│   ├── 赛前学习清单.md       # 备赛算法清单 + 题型映射 + 跑题红线
│   ├── 导入规范.md           # 共享模块导入规则 + 跨问题常量规范
│   ├── 获奖论文/              # 5 篇参考论文分析
│   │   └── 板凳龙-南科大-2024国一.md  # 极坐标+运动学+碰撞, 国一第5篇
│   ├── 2026官方答疑/          # 官方 Q&A（2026 试行规范问答）
│   │   └── 20260826-咨询问题解答.md
│   ├── examples/              # 机理题示例（螺线轨迹）
│   │   └── 机理题示例-螺线轨迹.py
│   ├── llm-prompts/           # ⚡ v1.5.0 LLM 工具集成（学生自用, copy-paste）
│   │   ├── README.md         #   4 工具总览 + 96 小时使用流程
│   │   ├── 01-选题推荐.md     #   题面+数据 → 候选模型 Top-3 (JSON)
│   │   ├── 02-代码修复.md     #   traceback → 根因 + 最小修复 + 验证
│   │   ├── 03-自动审稿.md     #   5 维评分 + 改进建议 + AI 痕迹词
│   │   └── 04-百分制评审.md   # ⚡ v1.5.1 3 模式 (M1字典预查/M2格式自查/M3百分制)
│   ├── 数模资料/              # ⚡ v1.5.1 BZD 数模社配套资源 (免费公开, 非商业自用)
│   │   ├── README.md         #   12 文件索引 + 与 li-mtrie 其他文档协同地图
│   │   ├── 5年16题训练-官方评阅细则评分要点.zip  # 5年国赛真题 + 评阅细则 + 评分要点
│   │   ├── 数学建模论文自查表.xlsx  # 单 Sheet 团队打印自查
│   │   ├── BZD数模论文AI痕迹自查指南.docx  # 人工 AIGC 自查 + 改写指南
│   │   └── 各板块写作指南/   # 8 PDF (摘要/问题重述/问题分析/模型假设/符号/模型求解/模型总结/参考文献+附录)
│   └── scripts/              # 程序化自检工具 (6 个)
│       ├── profile_data.py   #   画图前 EDA
│       ├── check_figure.py    #   提交前格式合规 (DPI ≥ 200)
│       ├── visual_qa.py       #   出图后版面自检
│       ├── verify_pdf_metrics.py  # 终审前 PDF 6 项体检 (借鉴 cumcm-live-workflow, GBK fix)
│       ├── aigc_scan.py      #   AIGC 9 维度自动扫描 (借鉴 aigc-reduce, GBK fix)
│       └── data_utils.py     #   ⚡ v1.5.0 3 跨题 utility (GBK 兼容 / utf-8-sig CSV / 字符串)
├── tools/
│   └── pack.py               # skill 自身打包工具
├── 题目/                      # 用户填：赛题 PDF/DOCX
├── 数据/                      # 用户填：附件 xlsx/csv
├── 求解/
│   ├── 求解计划.md            # 方案比选 + 详细求解思路
│   ├── 共享/                  # 跨问题共享模块（物理常量 + 工具）
│   └── 问题X/                # 求解过程中生成
│       ├── 问题X_xxx.py      # 每个问题一个 py 文件
│       ├── 图片/              # ≥ 4-6 张 PNG
│       └── 结果/              # resultX.xlsx 等国赛附件
└── 论文/                      # LaTeX 模板（format.cls + 思源宋体）
    ├── 论文.tex               # 纸质版入口（含承诺书+编号页）
    ├── 电子版.tex             # 电子版入口（不含承诺书/编号页）
    ├── AI工具使用详情.tex     # 用了 AI 必填 → 编译后放支撑材料
    ├── 9.0.AI工具使用声明.tex  # AI 声明占位（参考文献之前）
    ├── 10.0.附录固定说明.tex   # 附录 1+2 固定句占位（二选一必填）
    ├── format.cls             # 排版样式
    ├── fonts/                 # 思源宋体（编译必需）
    └── 0-10 章.tex            # 摘要/引言/总体分析/模型假设/符号/建模求解/检验/评价/改进推广/参考文献/附录
```

> **维护说明**：本目录结构是**单一权威源**，SKILL.md 和其他文档需要时引用本段，不要复制粘贴。

## 编译

完整 xelatex × 2 + 红/绿判据 + 打包流程在 **`SKILL.md` §Step 4 编译 + 终态**（含 `! Error`=0 + `Overfull \hbox`<5 + 合规检查 §2 7 项全过的 checkable 判据）。

**这里只列入口**:
- 论文版: `论文/论文.tex`（含承诺书 + 编号页）
- 电子版: `论文/电子版.tex`（不含承诺书，第一页直接摘要）

**必装依赖**: 见 `SKILL.md §必装依赖`（pandas / numpy / scipy / matplotlib / openpyxl / PyMuPDF / pulp）。**赛前 1 天**配 `python -m venv .venv` 隔离环境。

## 规范出处

- 《全国大学生数学建模竞赛论文格式规范（2026 年修订稿）》
- 《全国大学生数学建模竞赛人工智能工具使用规定（2026 年试行）》
- 官方：`https://www.mcm.edu.cn/`

## 版本

- **v1.5.2**（2026-09-03, 在 v1.5.1 之上 + 1 commit 累计）— `fix(scripts)` 兼容 PyMuPDF ≥1.24
  的 fitz deprecate. verify_pdf_metrics.py + visual_qa.py 改 try/except 双 import
  (优先 `import pymupdf as fitz`, fallback `import fitz`). 2 文件, +8/-2 行. 验证
  跑通 24 页 PDF 无警告. 向后兼容 PyMuPDF <1.24.
- **v1.5.1**（2026-09-03, 在 v1.5.0 之上 + 4 commits 累计）— 借鉴 BZD 数模社 3 个核心
  skill: `bzd-model-dictionary` (11 维评估+4档判定) + `bzd-paper-format-checker`
  (12 章节报告+15 分制) + `bzd-review-paper` (100 分+90% 封顶+格式系数+位次估计).
  产出 4 新文件: `references/模型字典使用指南.md` (6.9KB) + `references/格式自查清单.md`
  (9.5KB) + `references/百分制评审方法.md` (6.5KB) + `llm-prompts/04-百分制评审.md`
  (12.4KB, 3 模式 M1/M2/M3 合并). 借鉴源扩到 7 个外部 skill.
- **v1.5.0**（15 commits 累计, 2026-08-27 → 08-31, 在 v1.4.4 13 commits 之上新增 2 commits）—
  ⚡ LLM 工具集成（`references/llm-prompts/` 3 工具 + README, 学生 copy-paste 自用,
  不调外部 API, 96 小时救星）+ ⚡ verify_pdf_metrics.py GBK console fix
  (commit 8866cbc hotfix). 借鉴 mma v3.3 / bzd-modeling-ideas / scipilot-figure-skill /
  aigc-reduce / cumcm-live-workflow / 数模陪跑独家 6 个外部 skill. 包大小 22.51 / 3.77 MB.
- **v1.4.4**（13 commits 累计, 2026-08-27 → 08-31）— 借鉴 数模陪跑独家 + cumcm-live-workflow v5.0
  + writing-for-agents 6 维度审计 + 4-script smoke test + 8 个新文件
  （论文/figures/ 10 张图 + 教学开关 + 国奖级硬性指标 + 去AIGC指南 + 题意红线
  + verify_pdf_metrics.py + 编号体系 v7 + workflow.md refactor）
- v1.4.3（纯 framework + 求解计划模板, 2026-08-25）
- v1.4.2（恢复 题目/数据/ 学生示例）
- v1.4.1（v1.4.0 复审 P0 1 + P1 4 全部应用）
- v1.4.0（加 板凳龙-南科大-2024 国一 作为第 5 篇参考论文）
- v1.3.2（writing-for-agents 审计 P0+P1+P2 全部应用, 2026-08-25）
- v1.3.1（测试报告 §8.5 5 项 P0/P1 全部闭环）
- v1.3（24 项 P0/P1/P2 改进 + 去重 2 轮 + 端到端验证）
- v1.2（2026 规范版, 5 篇 2024 获奖论文归纳）
- v1.0（2024 高教社杯 4 篇获奖论文归纳）

## License

[MIT](LICENSE) - 仅供学习交流使用。
