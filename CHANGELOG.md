# 更新日志 (Changelog)

本项目遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

## [v1.4.4] - 2026-08-27

**v1.4.4 阶段: 借鉴 数模陪跑独家 + cumcm-live-workflow v5.0 + writing-for-agents 6 维度审计, 12 commits 累计 8 个新文件**

借鉴自 2 个外部 skill:
- **数模陪跑独家 v5.0** (2026 LaTeX 模板): figures/ 示例图 + 教学开关宏
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
