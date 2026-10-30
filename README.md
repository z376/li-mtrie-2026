# li-mtrie-2026

**数模国赛/美赛 端到端 skill: 5 步状态机 + 10 章论文模板 + 2026 规范 (MIT)**

读题 → 建模 → 求解 → 写论文 → 双版编译，一条龙。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version v1.8.0](https://img.shields.io/badge/version-v1.9.0-blue.svg)](CHANGELOG.md)
[![Smoke Test](https://github.com/z376/li-mtrie-2026/actions/workflows/smoke-test.yml/badge.svg)](.github/workflows/smoke-test.yml)
[![2026 Spec](https://img.shields.io/badge/2026%E8%A7%84%E8%8C%83-%E5%AF%B9%E9%BD%90-green.svg)](references/data-usage/合规检查清单.md)

按 2026 年全国大学生数学建模竞赛《论文格式规范（2026 年修订稿）》+《人工智能工具
使用规定（2026 年试行）》做了对齐更新。

## 适用场景

- 全国大学生数学建模竞赛（**国赛**，A/B/C/D/E 题）
- 美赛 / 校赛 / 其它数学建模类竞赛（结构基本通用）

触发词：`开始求解`、`跑题`、`做数模`、`生成论文`、`出论文 PDF`、`验本 skill`（前 4 个 + `出论文 PDF` 是 SKILL.md description 里的 always-loaded 核心触发词）。

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
  （`references/preparation/赛前学习清单.md`）

## 版本历史 (早期条目已归档到 CHANGELOG.md)

> **完整变更记录见 [`CHANGELOG.md`](CHANGELOG.md)** —— 单主文件、倒序、**权威源**.
> 本 README 只保留**当前能力概览**; 历史版本条目一律去 CHANGELOG.md 查, **不在这里复制** —— 复制必 stale.
> 开发期的过程记录 (开发日志 / 测试报告 / 早期流程审计) 在 `references/归档/`.

**早期几个关键版本的一句话索引** (完整条目见 CHANGELOG.md):

| 版本 | 一句话 |
|------|--------|
| v1.5.4 | 防"答非所问"强化: Step 0 quote 锚定表 + 题面判据 grep + dryrun check 15/16/17 |
| v1.5.3 | 借鉴 BZD 12 子 skill: 9 板块自查清单 + 题意翻译 + 学校国奖画像 |
| v1.5.2 | PyMuPDF ≥1.24 fitz 兼容 + LaTeX Overfull 全绿 |
| v1.5.1 | 借鉴 BZD 3 核心 skill: 模型字典 + 格式自查清单 + 百分制评审 |
| v1.5.0 | LLM 工具集成 (5 个 prompt) + 整题建模框架 + 绘图规范体系 |

## 快速上手

**先选包** (`默认完整包`):
- **完整包** (~24 MB, 含思源宋体) — 开箱即用, 编译无需装字体 → **推荐** (默认)
- **轻量包** (~5.4 MB, 不含字体) — 适合分享/上传, 编译需自装思源宋体
  (体积随版本浮动, 以 `tools/pack.py` 实际输出为准)

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
├── README.md                 # 本文件（项目说明 + 目录索引）
├── CHANGELOG.md              # 版本变更（单主文件，倒序）⚠️ 不进分发包（pack.py 排除）
├── CHANGELOG-archive.md      # 历史变更归档 ⚠️ 不进分发包（pack.py 排除）
├── CONTRIBUTING.md           # 贡献指南 ⚠️ 不进分发包（pack.py 排除）
├── LICENSE                   # MIT
├── tags.txt                  # 发布版本清单 (git tag 倒序; 生成: git tag --sort=-v:refname > tags.txt)
├── references/                # 复用层（按需查阅）
│   ├── code-template.py      # 数据驱动题模板（含 save_fig_with_qa + 守恒校验指针）
│   ├── mechanism-template.py # 机理题模板（含 gen_handle_names + §4.1 守恒校验接入）
│   ├── 代理审计prompt.md      # ⚡ v1.5.9 P1-4 代理交叉审计 prompt（A-H 板块）
│   ├── 评阅要点对齐.md        # ⚡ v1.5.9.1 P1-1 评阅要点 → 论文段映射矩阵
│   ├── workflow/              # 工作流层
│   │   ├── workflow.md        #   详细工作流 + 论文硬性规则
│   │   ├── Python环境.md      #   ⚡ v1.6.0 P2-1 解释器探测 + GBK + 装包
│   │   ├── 导入规范.md        #   共享模块导入规则 + 跨问题常量规范
│   │   ├── 整题建模模式.md    #   整题建模流程
│   │   ├── 模型决策树.md      #   6 大题型 × 3 层模型决策
│   │   └── 模型字典使用指南.md
│   ├── paper/                 # 论文规范层
│   │   ├── paper-spec.md      #   论文 10 章详细规范 + 一致性自检 + §4.1 Overfull 案例
│   │   ├── 写作与附录检查.md
│   │   ├── 国奖级硬性指标.md
│   │   ├── 格式自查清单.md
│   │   └── 百分制评审方法.md
│   ├── read-checklist/        # 读题层
│   │   ├── 读题清单.md        #   15 项空表模板（跑题前必填）
│   │   ├── 题意红线.md        #   ⚡ §红线 1-7（含 P0-1 边界离散式）
│   │   ├── 红线与失败模式.md
│   │   └── 题意翻译.md        #   ⚡ v1.5.3 题意翻译 5 步流程
│   ├── audit/                 # 审计层
│   │   ├── 验收清单.md        #   A-J 段 + §J 验收标准打钩区
│   │   ├── 验收标准.md        #   ⚡ v1.6.3 验收标准 6 条 → check 号 / 判据 / 兜底
│   │   ├── auto-check-list.md #   跑题后自动检查各 check 段
│   │   ├── post-solution-audit-list.md  # 34 层审计清单 L1-L34 (L17 在 auto-check-list)
│   │   ├── post-solution-audit.md       # 4 必做 + 1 可选 + 状态机
│   │   ├── manual-checklist.md          # 5 类 manual 兜底清单
│   │   ├── agent-audit-brief.md         # 代理审计 brief 4 段
│   │   ├── 数值台账规范.md     #   ⚡ v1.5.8.2 P0-3 论文数字三来源
│   │   └── 参考文献审计清单.md #   文献逐条核验
│   ├── plot/                  # 绘图层
│   │   ├── 绘图规范与避坑.md   #   ⚡ §〇 第 0 条：图内禁 set_title
│   │   └── 图型选择决策.md
│   ├── data-usage/            # 数据层
│   │   ├── 数据清洗规范.md     #   ⚡ v1.5.8.1 P0-2 趋势数据禁 IQR
│   │   ├── 信息边界原则.md
│   │   └── 合规检查清单.md
│   ├── by-category/           # ⚡ 6 分类专属反模式（物理/优化/数据/交通/生物/经济）
│   ├── design-intent/         # ⚡ 题目设计意图分析 + 5 道防线自检清单
│   ├── aigc/                  # ⚡ AIGC 降重策略 + 去 AIGC 指南
│   ├── preparation/           # ⚡ 赛前学习清单 + 角色 Prompt + 学校国奖画像
│   ├── 技能总结/              # 经验汇总
│   ├── templates/             # 论文模板
│   │   └── example-paper/     #   ⚡ 25 个 .tex = 20 章节 + preamble×2 + 3 入口（figures/ fonts/ format.cls）
│   ├── 获奖论文/              # 5 篇参考论文分析
│   │   └── 板凳龙-南科大-2024国一.md  # 极坐标+运动学+碰撞, 国一第5篇
│   ├── 2026官方答疑/          # 官方 Q&A（2026 试行规范问答）
│   │   └── 20260826-咨询问题解答.md
│   ├── examples/              # 机理题示例（螺线轨迹）
│   │   └── 机理题示例-螺线轨迹.py
│   ├── llm-prompts/           # ⚡ v1.5.0 LLM 工具集成（学生自用, copy-paste）
│   │   ├── README.md         #   5 工具总览 + 96 小时使用流程
│   │   ├── 01-选题推荐.md     #   题面+数据 → 候选模型 Top-3 (JSON)
│   │   ├── 02-代码修复.md     #   traceback → 根因 + 最小修复 + 验证
│   │   ├── 03-自动审稿.md     #   5 维评分 + 改进建议 + AI 痕迹词
│   │   ├── 04-百分制评审.md   # ⚡ v1.5.1 3 模式 (M1字典预查/M2格式自查/M3百分制)
│   │   └── 05-读题提取.md     # ⚡ v1.5.7 LLM 自动从 PDF 提取 15 项读题清单
│   ├── 数模资料/              # ⚡ v1.5.1 BZD 数模社配套资源 (免费公开, 非商业自用)
│   │   ├── README.md         #   12 文件索引 + 与 li-mtrie 其他文档协同地图
│   │   ├── 5年16题训练-官方评阅细则评分要点.zip  # 5年国赛真题 + 评阅细则 + 评分要点
│   │   ├── 数学建模论文自查表.xlsx  # 单 Sheet 团队打印自查
│   │   ├── BZD数模论文AI痕迹自查指南.docx  # 人工 AIGC 自查 + 改写指南
│   │   └── 各板块写作指南/   # 8 PDF (摘要/问题重述/问题分析/模型假设/符号/模型求解/模型总结/参考文献+附录)
│   ├── 板块自查/             # ⚡ v1.5.3 9 板块级自查清单 (借鉴 BZD 12 子 skill)
│   ├── 归档/                 # 开发期历史记录 (开发日志/测试报告/流程审计) — 跑题不用读
│   │   ├── README.md         #   索引 + 借鉴源映射 + 与现有 4 文件关系
│   │   ├── 01-摘要自查.md    #   §0 摘要 7 维诊断 (≥ 8 绿)
│   │   ├── 02-AI声明自查.md  #   §9.0 AI 声明 5 问 + 4 铁律
│   │   ├── 03-问题重述自查.md #  §1 引言 3 段结构
│   │   ├── 04-问题分析自查.md #  §2 总体分析 7 维 + 4 类联动
│   │   ├── 05-模型假设自查.md #  §3 模型假设 5 维/条
│   │   ├── 06-符号说明自查.md #  §4 符号说明 7 维
│   │   ├── 07-模型求解自查.md #  §5 建模求解 + §6 检验 5 段
│   │   ├── 08-参考文献附录自查.md # §9 文献 + §10 附录 P0-P3
│   │   └── 09-AIGC审计.md    #   全文 9+6=15 维 (≥ 80 绿)
│   └── scripts/              # 程序化自检工具 (12 个 .py + 2 个 .md, 速查表见 README.md)
│       ├── dryrun.py         #   ⚡ 赛前 1 天必做 65 项 checkable sign-off（0 red 才放行）
│       ├── bc_check.py       #   ⚡ v1.6.3 表面行守恒校验器（dE/dt ÷ 边界通量 ≈ 1，P0-1 签名 223）
│       ├── fig_sanity.py     #   ⚡ v1.5.9 P1-3 图形内容自检（恒定曲线/全NaN/残留 set_title）
│       ├── check_meta.py     #   ⚡ v1.5.9.4 P1-7 meta.json 3 件套校验
│       ├── number_ledger.py  #   ⚡ v1.5.8.2 P0-3 数值台账生成/核对
│       ├── agent_audit.py    #   ⚡ v1.5.7.38 代理审计 brief 生成
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
├── _archive/                  # 本地归档 (2.7 MB 2024B 例图) — 不进 git / 不进分发包
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

> **维护说明**：本目录结构是**索引**（**以实际文件为准**），SKILL.md 和其他文档需要时引用本段，不要复制粘贴。
> 新增/删除文件后请同步本段；dryrun **check 68** 会校验 SKILL.md 声明的模板 .tex 数量与 `references/templates/example-paper/` 实际文件数是否一致（防"目录树与实际漂移"）。

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

- **v1.5.7**（2026-09-07, 在 v1.5.6 之上 + 2 commit 累计）— 细化读题环节. SKILL.md §Step 0 加 15 项读题清单 (防 2025C 3 P0 错位), 新增 references/read-checklist/读题清单.md (15 项空表模板) + references/llm-prompts/05-读题提取.md (LLM 工具自动从 PDF 提取), dryrun.py check 19 验证 15 项全覆盖. 包大小 23.91 MB (+0.01), 增量几乎无. 审计 8.0/10 不变.
- **v1.5.6**（2026-09-07, 在 v1.5.5 之上 + 1 commit 累计）— 借鉴 BZD 数模社 12 个论文板块模板 (4 色教学法). 14 个 .tex 全部按 BZD 2026 规范重写: 0.摘要 (4 段+关键词) / 1.引言 (3 子节) / 2.总体分析 (5 段+框架图) / 3.模型假设 (9 类) / 4.符号说明 (三线表) / 5.1.1+5.1.2 (建模+求解) / 6.模型检验 (4 类) / 7.模型评价 (4 子节) / 8.改进推广 (4 层面) / 9.参考文献 / 9.0.AI 声明 / 10.0 附录固定说明 / 10.附录 (核心源代码). dryrun.py check 16/17 加 template 状态 yellow 跳过. 包大小 5.12 MB, 增量 < 0.1 MB. 审计 8.0/10 不变.
- **v1.5.4**（2026-09-06, 在 v1.5.3 之上 + 1 commit 累计）— 防"答非所问"强化. 借 2025C 跑题
  失败案例 (other agent 踩 3 P0: 问题 4 选错 sheet / 问题 2-3 自创 BMI 分组 / 10.附录.tex
  残留 2024B 模板), 加 3 道程序化防线: dryrun.py check 15 占位符未替换 / 16 附录文件
  存在 / 17 \includegraphics 图引用存在. SKILL.md 加 4 段必做项 (Step 0 quote 锚定
  + 题面关键判据 grep / Step 3 占位符 grep / Step 4 附录文件 Test-Path) + 顶部
  4 大典型坑警示表. 2 文件改 + 0 文件加. 审计 8.0/10 不变 (4 段必做项是补强, 不增加
  文档边界, 跟 v1.5.2 末 P3-2 3 文档边界一致).
- **v1.5.3**（2026-09-06, 在 v1.5.2 之上 + 3 commits 累计）— 借鉴 BZD 数模社 12 个论文
  自查类子 skill + bzd-problem-translator + bzd-cumcm-school-awards 核心理念.
  产出 11 新文件: `references/板块自查/` (10 文件, 9 板块级自查 + 1 README 索引)
  + `references/read-checklist/题意翻译.md` (3.5 KB) + `references/preparation/学校国奖画像.md` (3.4 KB).
  借鉴源扩到 18 个外部 skill. 审计 7.7/10 (中) → 8.0/10 (P4 patch 整改后恢复 6 维度上限).
- **v1.5.2**（2026-09-03, 在 v1.5.1 之上 + 1 commit 累计）— `fix(scripts)` 兼容 PyMuPDF ≥1.24
  的 fitz deprecate. verify_pdf_metrics.py + visual_qa.py 改 try/except 双 import
  (优先 `import pymupdf as fitz`, fallback `import fitz`). 2 文件, +8/-2 行. 验证
  跑通 24 页 PDF 无警告. 向后兼容 PyMuPDF <1.24.
- **v1.5.1**（2026-09-03, 在 v1.5.0 之上 + 4 commits 累计）— 借鉴 BZD 数模社 3 个核心
  skill: `bzd-model-dictionary` (11 维评估+4档判定) + `bzd-paper-format-checker`
  (12 章节报告+15 分制) + `bzd-review-paper` (100 分+90% 封顶+格式系数+位次估计).
  产出 4 新文件: `references/workflow/模型字典使用指南.md` (6.9KB) + `references/paper/格式自查清单.md`
  (9.5KB) + `references/paper/百分制评审方法.md` (6.5KB) + `llm-prompts/04-百分制评审.md`
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
