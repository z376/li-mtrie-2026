# 更新日志 (Changelog)

本项目遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

## [v1.5.2] - 2026-09-03

**v1.5.2 阶段: fix(scripts) PyMuPDF ≥1.24 fitz deprecate 兼容 (1 commit, 2 文件)**

### Fixed

- **PyMuPDF ≥1.24 deprecate `import fitz`**, 推荐 `import pymupdf` (或 `import pymupdf as fitz`).
  - `references/scripts/verify_pdf_metrics.py` (强制 import) — 改 `try/except` 双 import
  - `references/scripts/visual_qa.py` (可选 import) — 改 `try/except` 双 import
- **新 import 顺序**:
  ```python
  try:
      import pymupdf as fitz  # PyMuPDF ≥1.24 推荐
  except ImportError:
      import fitz  # PyMuPDF <1.24 fallback
  ```
- **API 调用方式不变**: `fitz.open(path)` 在两个分支都可用

### Changed

- 无 (v1.5.2 是 fix-only, 不改 v1.5.1 的 4 个新文件 + 6 个 .tex 模板)

### 验证

- ✓ 2 脚本 py_compile OK
- ✓ pymupdf 1.28.2 实际安装, fitz 警告消失
- ✓ `verify_pdf_metrics.py 论文.pdf` 实际跑通 24 页, 0 fitz deprecate warning

### 向后兼容

- PyMuPDF ≥1.24 (2024+): 用 `pymupdf as fitz` (推荐, 无警告)
- PyMuPDF <1.24 (2023-): fallback `import fitz` (老版本, API 不变, 不会破坏)

### 总结

- 1 commit (087fea2), 2 文件, +8/-2 行
- 借鉴源: 仍是 9 个外部 skill (v1.5.1)
- 包大小: 完整包 27.39 MB / 轻量包 8.65 MB (跟 v1.5.1 几乎相同, 8 行改动对 zip 影响微乎其微)

### 追加 (同一 release, 2 commits, writing-for-agents 二轮审计整改 + LaTeX 全绿)

**审计前**: 7.5/10 (v1.5.1 P0+P1+P2 整改后)
**审计后**: 7.8/10 (P3 4 项整改后, P3-2 留作后续 release 达 8.0 上限)

**fix(论文) 11 Overfull → 0** (commit 9b63e6b, 6 文件 +23/-12):
- 4.符号说明.tex: longtable 列宽 18/62/14% → 16/60/12%
- 5.1.1.分析与准备.tex: 集中优化 aligned 拆 2 个 equation (max + s.t.)
- 5.1.2.建模与求解.tex: enumerate 内联数学 (23.6pt × 3) → align* 块, 简写 d_f
- 6.模型检验.tex: 5 列 longtable 总宽 92%→80% (0.08/0.16/0.14/0.14/0.28)
- 9.参考文献.tex: \begin{sloppypar} 包住 enumerate
- 10.附录.tex: verbatim 60pt 长行手动换行
- **结果**: 论文.pdf (24 页) + 电子版.pdf (22 页) = 0 Overfull sign-off 全绿; AI详情.pdf (6 页) 4 Overfull < 5 判据绿

**P3 writing-for-agents 二轮审计 4 项整改** (commit c7ecb34, 6 文件 +34/-12):
- **P3-4 `green`/`red` 锚定**: SKILL.md 顶部 'checkable 红/绿' → 'green/red 二元' (用 green/red 而非红/绿, 锚定 pretrained 视觉 prior). sign-off 段统一. 强度: pretrained > 自造.
- **P3-3 工具 01 ↔ 04-M1 双向链接**: 01-选题推荐 顶部加 '调用链: 01 粗筛 → 04 §M1 细评'. 04-百分制评审 顶部加 '调用链: 粗筛 (01) → 细评 (§M1) → 格式自查 (§M2) → 终评 (§M3)'.
- **P3-1 绘图规范 vs 绘图避坑 显式分工**: 绘图规范.md 标题加 '(How — 字号/线宽/DPI 怎么写)'. 绘图避坑.md 标题加 '(What Not — 18 条陷阱)'. 协同: 写图前 How → 跑图后 What Not → 提交前 check_figure.py.
- **P3-5 negation 扫描 (只改最高杠杆 角色Prompt.md)**: 5 处 negation 改 positive (等用户确认/用具体传递内容标注/避免返工/遵循模板预设/用深色主线/保持原 figsize). 其他文档 negation 大部分是硬 guardrail 或反例警示, 合理.

**P3-2 未执行** (工作量 0.5 天, 留作后续 release):
- workflow.md 14KB 删 5 步状态机重复段 (-4KB)
- paper-spec.md 33KB 删 5 步状态机重复段 (-3KB)
- 涉及 2 文档大改, 边际收益 0.2 audit 分, 当前 7.8/10 接近 8.0 上限

**总览** (v1.5.2 整个 release):
- 4 commits: 087fea2 (fitz) + 4efe740 (元数据) + 9b63e6b (Overfull) + c7ecb34 (P3 4 项)
- 文件: 8 文件 (+86/-26 行)
- 借鉴源: 9 个外部 skill (不变)
- 包大小: 完整 27.43 MB / 轻量 8.69 MB
- 审计分: 6.83 (v1.5.1 整改前) → 7.5 (P0+P1+P2) → 7.8 (P3)
- sign-off: 全绿 (3 PDF Overfull < 5 判据)

## [v1.5.1] - 2026-09-03

**v1.5.1 阶段: 借鉴 BZD 数模社 3 个核心 skill, 4 个新文件, 闭环 references + llm-prompts**

### Added

**Part A — 3 个 references 方法论**:
- `references/模型字典使用指南.md` (6.9 KB) — 11 维评估 (任务对齐/观测单元/目标输出/数据充分性/假设合理性/泄露因果/约束机理/可验证性/可解释性/计算可行性/论文完整性) + 4 档适配性判定 (合适/有条件合适/不合适/证据不足) + 6 类指标 routing (分类/回归/时序/聚类/优化/评价/机理). 借鉴 BZD `bzd-model-dictionary` v1.0
- `references/格式自查清单.md` (9.5 KB) — 12 章节 Markdown 报告模板 + 100+ 原子检查点 (摘要 5/页面 8/标题/图文/匿名/...) + 15 分逐项扣分制 + 4 个专项表格 (标题密度/建模可读性/优化模型集中陈述/图表重复) + 国赛特殊规则 (无目录/30 页/附录分板块). 借鉴 BZD `bzd-paper-format-checker` v1.0
- `references/百分制评审方法.md` (6.5 KB) — 100 分制 (摘要 10 + 格式 10 + 模型/求解/结果 70-75 + 补充 5-10) + 每问题三块拆解 (建立/求解/结果) + 90% 封顶制 + 1/2/3 档扣分 + 格式质量系数 `(format_score_10 + 10) / 20` + 位次估计 (CUMCM 2025 锚点 / 其他均匀近似). 借鉴 BZD `bzd-review-paper` v1.0

**Part B — 1 个 LLM 工具**:
- `references/llm-prompts/04-百分制评审.md` (12.4 KB) — 3 模式合并为 1 个工具: **M1 字典预查** (选模型, 5-10 分钟) / **M2 格式自查** (写完, 15-25 分钟) / **M3 百分制评审** (终审, 20-40 分钟). 每模式独立 prompt 模板 + 严格 JSON OUTPUT_FORMAT. 学生 copy-paste 自用, 不调外部 API

**Part C — 元数据更新**:
- `SKILL.md` frontmatter `version: "1.5.0" → "1.5.1"`, `history` 字段加 1.5.1 条目
- `README.md` 徽章 `v1.5.0 → v1.5.1` + 新增 v1.5.1 章节 + 版本历史 v1.5.1 条目
- `llm-prompts/README.md` 工具表 3 → 4, 加 04 + 3 模式说明 + 协同表加 04 行 + 使用流程图加 04 节点

### 总览

- 4 个新文件 (3 references + 1 llm-prompt), 总 ~35 KB
- 借鉴源从 6 个扩到 9 个外部 skill (BZD 3 个: model-dictionary + paper-format-checker + review-paper)
- 闭环设计: `references/方法论.md` ↔ `llm-prompts/工具.md` 双向引用, 学生 1 次学方法论 + 1 次用工具, 不重复
- 包大小: 完整包 ~22.5 MB / 轻量包 ~3.8 MB (微小增量, 4 个 md 文件)

### 追加 (同一 release)

- **`references/数模资料/`** (新目录) — BZD 数模社免费公开的 14 文件配套资源:
  - `5年16题训练-官方评阅细则评分要点.zip` (424KB) — 5 年国赛真题 + 官方评阅细则 + 评分要点
  - **`2026年数学建模竞赛模板-BZD数模社(证书签名).pdf` (2.4MB) — 完整 LaTeX 模板 (带证书签名), 备用**
  - **`2026年数学建模竞赛模板-简洁版.docx` (88KB) — 简洁版 Word 模板, 备用**
  - `数学建模论文自查表.xlsx` (30KB) — 单 Sheet 团队打印协作自查
  - `BZD数模论文AI痕迹自查指南.docx` (53KB) — 人工 AIGC 自查 + 改写指南
  - `各板块写作指南/` (8 PDF, 2.1MB) — 8 大板块 (摘要/问题重述/问题分析/模型假设/符号/模型求解/模型总结/参考文献+附录) 详细写作说明
  - `README.md` (3.9KB) — 14 文件索引 + 与 li-mtrie 其他文档协同地图
- **总增量**: 15 文件 (~5.0MB), 大头是 5年16题训练 zip + 8 PDF + 2 模板
- **使用方式**: 学生**自取**, 不二次分发, 不删改 BZD 数模社署名
- **优先级**: 默认仍用 li-mtrie 自带 `论文/format.cls` (思源宋体, 已对齐 2026 规范). BZD 模板作为**对比参考**

### 追加 refactor (同一 release, 3 commits, writing-for-agents 6 维度审计整改)

**审计前**: 6.83/10 (P0+P1+P2 5+5+3 = 13 项问题)
**审计后**: 7.5/10

**P0 (5 项必修)**:
- P0-1: SKILL.md 装包 3 段 (Python 环境 + venv + 必装依赖) 合并为 1 段, 减 50 行, checkable 红/绿锚定
- P0-2: Step 3 写论文 加 checkable 绿判据 (11 章节 ≥30 行 + AI 声明 + 附录固定说明)
- P0-3: workflow.md 头部强化分工 (SKILL=入口, workflow=细节, 冲突以 SKILL 为准)
- P0-4: 锚定 `checkable` 为 SKILL.md 顶部 leading word
- P0-5: 3 份清单 (合规/国奖/验收) 各加关系段 + 使用顺序

**P1 (5 项应修)**:
- P1-1: 3 模式 ↔ 3 references 双向链接 (04 ↔ 3 新 references)
- P1-2: 受保护片段 ↔ 检测平台弱点 双向链接 (而非合并, 主题不同)
- P1-3: 流程审计 19 漏点 → `_archive/` (gitignore 排除, 减 34KB references/ 占用)
- P1-4: (P0-1 已做) 装包 leading word 锚定
- P1-5: README.md 快速上手 顶部加 "先选包 (默认完整包)"

**P2 (3 项选)**:
- P2-1: Step 0 判据精炼 (200 字 + 4 项必备, 去掉不可 checkable 的 "N 题准确")
- P2-2: 测试报告 + 开发日志 → `_archive/` (减 69KB 内部开发记录)
- P2-3: 引入 `sign-off` leading word (Step 4 流程图底部)

**总改动**: 13 文件, 8 commits (P0: 5 files / +49/-66, P1: 8 files / +27/0 + 1 rename, P2: 3 files / +4/-2 + 2 rename)
**新增 leading words**: `checkable` (writing-for-agents 核心), `sign-off` (终审通过)
**新增流程图术语**: 5 步状态机 checkable 判据, 3 份清单使用顺序

## [v1.5.0] - 2026-08-31

**v1.5.0 阶段: LLM 工具集成（学生自用），19 commits 累计，新增 4 个 LLM prompt 工具**

### Added

**Part A — LLM 工具集成**（commit 8ee6555）：
- `references/llm-prompts/01-选题推荐.md`（4.7 KB）— 题面+数据 → 问题分类 + 候选模型 Top-3 + 数据洞察（JSON 输出）
- `references/llm-prompts/02-代码修复.md`（4.9 KB）— **96 小时救星**：traceback → 根因 + 最小修复 + 验证步骤（debug 30% 时间节约 8-10 小时）
- `references/llm-prompts/03-自动审稿.md`（6.6 KB）— 5 维评分（机理/数据/写作/创新/排版）+ 改进建议 + AI 痕迹词
- `references/llm-prompts/README.md`（3.5 KB）— 3 个工具总览 + 96 小时使用流程 + 与 26 条自查表映射

**核心设计原则**：
- **不调外部 API**（学生 copy-paste prompt 到 Mavis/Claude/GPT 即可）
- **结构化 JSON 输出**（避免 LLM 泛泛而谈）
- **三道防线**（工具 02：diff 必读 / 测试必跑 / 备份必留）

### Changed

- `SKILL.md` frontmatter `version: "1.4.4" → "1.5.0"`，加 `history` 字段（v1.5.0 + v1.4.4 摘要）
- `README.md` 徽章 `v1.4.4 → v1.5.0`
- `smoke-test.yml` 加 `data_utils.py` 和 `aigc_scan.py` 到 py_compile 列表（5 → 8 个）；加 SKILL.md version 提取输出
- `llm-prompts/README.md` 标题 "v1.4.5 起" → "v1.5.0 起"

### 总览

- 19 commits 累计（v1.4.0 → v1.5.0 共 4 天）
- 借鉴 6 个外部 skill（数模陪跑独家 + cumcm-live-workflow + aigc-reduce + scipilot-figure + bzd-modeling-ideas + mma v3.3）
- 18 个新文件（6 scripts + 12 references + 4 LLM prompt 工具）
- 包大小: 完整包 22.49 MB / 轻量包 3.75 MB

## [v1.4.4] - 2026-08-27

**v1.4.4 阶段: 借鉴 数模陪跑独家 + cumcm-live-workflow v5.0 + writing-for-agents 6 维度审计, 12 commits 累计 8 个新文件**

借鉴自 2 个外部 skill:
- **数模陪跑独家 v5.0** (2026 LaTeX 模板): 论文/figures/ 示例图 + 教学开关宏
- **cumcm-live-workflow v5.0**: 国奖硬指标 + 去AIGC指南 + 题意红线 + verify_pdf_metrics.py + 跨平台红线 + 代码完整性铁律 + 编号体系 v7

### Added (8 个新文件)

**Part A — 借鉴 数模陪跑独家** (commit efaa2b4):
- `论文/figures/` — 10 张示例图 (流程图/结果图/稳健性图), 来源标注"仅作形式参考, 参赛前必须整图替换"
- `论文/figures/README.md` — 三件必做警告 + 文件清单
- `\showteachingtrue/false` 教学开关 + 3 个 LaTeX 宏 (`\Teach` / `\TeachExample` / `\Placeholder`)

**Part B — 借鉴 cumcm-live-workflow** (commits 9f8a618 + bf58273):
- `references/国奖级硬性指标.md` (9.4 KB) — 6 类硬性指标 (公式≥15/表格≥18/图片≥10/参考文献 15-25/三类检验齐全/正文 25-30 页) + 26 条自查表 6 维度 + PowerShell 一键自检
- `references/去AIGC指南.md` (9.1 KB) — 降重 4 层法 (L1 词汇→L4 证据) + 9 类正文 AI 痕迹 + 6 类代码 AI 特征 + 把 AI 从"代写"改成"审稿人"
- `references/题意红线.md` (4.7 KB) — 4 条题意红线 (题面物理事实必建模 / 解析独立验证 / 后问误差敏感 / 无官方答案 5 步自查)
- `references/scripts/verify_pdf_metrics.py` (5.3 KB) — PDF 6 项程序化体检 (结构 / 4 边越界 / 元数据匿名 / 关键数字 / `??` 未定义引用 / 摘要页判断)

### Changed (5 类)

**A. 论文 LaTeX 模板** (commit efaa2b4):
- 论文.tex + 电子版.tex + AI工具使用详情.tex 顶部插入教学开关宏

**B. 文档一致性 hotfix** (commit 3699840):
- SKILL.md / README.md / CHANGELOG.md / AI工具使用详情.tex 全部 v1.4.3 → v1.4.4
- AI工具使用详情.tex 顶部加宏 (与论文.tex/电子版.tex 一致)

**C. AI 工具使用声明 二者择一模板** (commit 0f678a8):
- 9.0.AI工具使用声明.tex 改为对齐 2026 官方简洁版 Word 模板 (3 段: 二者择一提示 + 未使用 AI 选项 + 使用 AI 选项)
- 用 `\Teach{}` 让"二者择一"红字提示在 showteaching 态可见 / 提交自动隐藏

**D. AI工具使用详情.tex pre-existing warning 修复** (commit f48f476):
- line 177 `\{bug,feature,question\}` → `(bug,feature,question)`, 4 个 `!` 错误全消

**E. v1.4.4 复审 + cumcm-live-workflow 借鉴** (commits c408205 + bf58273):
- `references/流程审计-19漏点-已闭环-2026-08-25.md` 加 v1.4.4 复审段 (3rd round), 19 漏点 16 Closed/3 部分/0 未关
- `references/paper-spec.md` 加 §三.6 编号体系 v7 (章节/列表罗马/公式 三档区分)
- `论文/3.模型假设.tex` 加 `[label=(\roman*)]` 示例
- `论文/10.附录.tex` 顶部加 2 条铁律注释 (代码完整性 + 文件列表一致性)
- `SKILL.md` 加 国奖/AIGC/题意红线/verify_pdf_metrics/跨平台 4 段交叉引用
- `references/scripts/README.md` 3→4 脚本 + Step 5.6 + 依赖加 PyMuPDF

**F. refactor + writing-for-agents 审计** (commits 584e798 + 2942466 + f774c6e + 56360a6 + 6cf77a9):
- `paper-spec.md` §三.6 编号体系 v7 (章节/列表罗马/公式 三档区分) + 章节错位修复 + 3x 重复去重
- `workflow.md` 砍 149 行 (343→194) 重复, 改为"SKILL.md 没说的细节专项" + §4 砍 30 行重复
- `SKILL.md` 4 处 negation 改 positive target (不要/禁止/严禁 → 不自行/统一/用真实/用正斜杠)
- `SKILL.md` Description 4 短语合一, 去英文标签 + Step 0 加 绿 判据 + Failure handling 上移
- `SKILL.md` + `references/合规检查清单.md` 4 处"5 节"→"4 节" doc drift 修 (commit 2d525b6 删 §五 后未同步)
- `.github/workflows/smoke-test.yml` 4 个 bug 修: 硬编码本地路径 → `$GITHUB_WORKSPACE` 相对路径 / pwsh 统一 / 7 个 .py 验证 / 排除规则修正
- `流程审计-19漏点-已闭环 doc` 加 round 5/6/7 段 (writing-for-agents + 4-doc audit + smoke test)

### P2 风险标注
- 10 张示例图来源第三方 (数模陪跑独家 → "2026 华数杯 A 论文" / "26 亚太杯中文赛 B 论文"), PNG 本身无可执行负载
- verify_pdf_metrics.py 越界警告含页脚页码假阳性, 需人工核对真伪
- 8/10 figures 缺 DPI 元数据 (3rd-party 来源固有问题, README 已警告"必须整图替换")

### 四轮审计 + 5-script smoke test 得分
- v1.3.2 baseline: 6.0/10 (19 漏点)
- v1.4.0 复审: 7.5/10 (11+ 修复)
- v1.4.4 复审: 8.0/10 (19 漏点全闭环, E1-E6 新发现)
- writing-for-agents round: 6.5/10 (workflow.md 重复 + negation + 文档结构 bug) → 修后 7.0/10
- 4-doc audit round: 5节→4节 doc drift + 4-script smoke test (全过, 没新 bug)
- **v1.4.4 最终: 8.0/10** (审计维度天花板, 再提需新功能而非文档清理)

### 包大小
- 完整包: 19.05 → 22.43 MB (+13 文件)
- 轻量包: 0.31 → 3.69 MB (+13 文件)

## [v1.4.3] - 2026-08-25

**v1.4.3 阶段: 纯 framework + 求解计划模板**

### Added
- `求解/求解计划.md` 模板 (5.8 KB, 6 段: 题组判定 / 整题联动 / 模型比选 / 8 项自检 / 符号表 / 灵敏度 / 写作检查清单)
- `LICENSE` (MIT)
- `CHANGELOG.md` (本文件)
- `CONTRIBUTING.md` (贡献指南)
- `.github/ISSUE_TEMPLATE/` (bug / feature / question)
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/smoke-test.yml` (CI)

### Changed
- `题目/`, `数据/`, `求解/` 三个目录清空 (学生自己填)
- `pack.py` 注释更新 (空目录说明)

## [v1.4.2] - 2026-08-25

**v1.4.2 阶段: 恢复 题目/数据/ 学生示例**

### Added
- `题目/A题.pdf` (286 KB, 2025 国赛 A 题烟幕)
- `数据/result1.xlsx` / `result2.xlsx` / `result3.xlsx` (国赛附件模板)

## [v1.4.1] - 2026-08-25

**v1.4.1 阶段: v1.4.0 复审 P0 1 + P1 4 全部应用**

### Changed
- Step 4.2 `bash grep` 改 `Select-String` (Windows 一致性, P0 必修)
- Step 4.2 加 green criterion (`! Error`=0, `Overfull`<5)
- SKILL.md 3 处 `§4.0` 指针校准到 `§2 8 项自检`
- `求解/共享/` 6 个 .py 删除 (备份副本, 求解/根 是 source of truth)
- 板凳龙 doc §5+§7 合并 (关联表 + 借鉴代码 合并)

## [v1.4.0] - 2026-08-25

**v1.4.0 阶段: 加 板凳龙-南科大-2024 国一 作为第 5 篇参考论文**

### Added
- `references/获奖论文/板凳龙-南科大-2024国一.md` (6.8 KB, 8 节: 题目背景 / 五题速览 / 7 项关键技术 / 写作范式 / 与 skill 关联 / 物理洞察 / 一句话总结)

### Changed
- SKILL.md: "4 篇" → "5 篇" 参考论文速查 pointer
- README.md: references/ 目录加 `获奖论文/` 子目录

## [v1.3.2] - 2026-08-25

**v1.3.2 阶段: writing-for-agents 审计 P0+P1+P2 全部应用**

### Added
- §Step 1.5 Tracer bullet 探路 (借鉴 *The Practice of Programming* 示踪弹)
- 5 处 red/green 锚 (state machine × 3 + Step 4.1 + 红/绿判据段)

### Changed
- 9 处 negation 改 positive target ("不要 X" → "目标 Y + 反向后果")
- 8 项自检复述 (33 行) → 1 行 pointer
- AI 合规 3 条 (12 行) → 1 行 pointer
- Step 1/2/4 completion 改 checkable (绿: 标记)
- "2027+ (未来)" 行改 actionable
- pack.py 排除: dev 草稿 / 隐私文件

## [v1.3.1] - 2026-08-25

**v1.3.1 阶段: 测试报告 §8.5 5 项 P0/P1 全部闭环**

### Added
- profile_data 时间序列 + 信号建议 (P0-8, P1-6)
- mechanism-template 加 scan_data_dir (P1-5)
- SKILL.md 加规范版本兼容段 (P0-10)
- 模板 GBK 兼容段 (P0-9)

## [v1.3.0] - 2026-08-24

**v1.3 阶段: 24 项 P0/P1/P2 改进 + 去重 2 轮 + 6 个权威源重构**

### Added
- SKILL.md 加 Python 环境就位 (A1)
- SKILL.md 加 venv 虚拟环境段 (A2)
- 论文模板加 AI 工具使用声明 + 附录固定说明 (D1, D2)
- Step 2.Gate 8 项自检门控 (C3)
- profile_data 加 `--all-sheets` (P0-4)
- xlsx 模板加 `astype(object)` (P0-6)
- mechanism-template 加多 sheet 输出 (P0-7)
- xelatex × 2 编译说明 (B1)
- longtable 列宽 1.04−0.04N 公式 (B2)
- profile_data CLI 4 种用法 (B3)
- 跨问题常量 §8 (C4)
- AI 内联标注规范 (D3)
- pack.py v3 修复 GBK

### Changed
- SKILL.md: 580 → 551 行 (-29, 去重轮 1)
- 8 项自检 / 跑题红线 / AI 合规 / Step 4.5 提交物 → 单一权威源
- README.md: 97 → 116 行 (升级为目录权威源)
- 模板树 + 中间产物 + AI 详情 重复删除 (去重轮 2)
- 整体: 2218 → 2197 行 (-21)

### Fixed
- P0 emoji GBK 兼容 (templates 加 INJECT block)
- P0 `✓` 字符 Latin Modern Roman 不存在 → 改 `\checkmark`

## [v1.2] - 2024

**v1.2 阶段: 2026 规范版, 5 篇 2024 获奖论文归纳**

### Added
- 2026 论文格式规范 + AI 工具使用规定 适配
- 摘要中文、不要目录、正文 ≤ 30 页
- 附录两段固定说明
- AI 声明在参考文献之前, 详情 PDF 在支撑材料

## [v1.0] - 2024

**v1.0 阶段: 2024 高教社杯 4 篇获奖论文归纳**

### Added
- 5 步状态机 (读题 → 求解计划 → 逐题求解 → 写论文 → 编译终态)
- 4 篇参考论文: B159 / B195 / B196 / D039
- 10 章论文结构模板
- LaTeX 模板 (format.cls + 思源宋体)
- 必装依赖清单

[Unreleased]: https://github.com/z376/li-mtrie-2026/compare/v1.4.4...HEAD
[v1.4.4]: https://github.com/z376/li-mtrie-2026/compare/v1.4.3...v1.4.4
[v1.4.3]: https://github.com/z376/li-mtrie-2026/compare/v1.4.2...v1.4.3
[v1.4.2]: https://github.com/z376/li-mtrie-2026/compare/v1.4.1...v1.4.2
[v1.4.1]: https://github.com/z376/li-mtrie-2026/compare/v1.4.0...v1.4.1
[v1.4.0]: https://github.com/z376/li-mtrie-2026/compare/v1.3.2...v1.4.0
[v1.3.2]: https://github.com/z376/li-mtrie-2026/compare/v1.3.1...v1.3.2
[v1.3.1]: https://github.com/z376/li-mtrie-2026/compare/v1.3.0...v1.3.1
[v1.3.0]: https://github.com/z376/li-mtrie-2026/compare/v1.2...v1.3.0
[v1.2]: https://github.com/z376/li-mtrie-2026/compare/v1.0...v1.2
[v1.0]: https://github.com/z376/li-mtrie-2026/commits/v1.0
