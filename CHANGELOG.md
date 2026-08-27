# 更新日志 (Changelog)

本项目遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

## [v1.4.4] - 2026-08-27

**v1.4.4 阶段: 借鉴 数模陪跑独家 模板, 添加 figures/ + 教学开关宏**

### Added
- `论文/figures/` — 10 张示例图 (流程图/结果图/稳健性图), 来源标注"仅作形式参考, 参赛前必须整图替换"
- `论文/figures/README.md` — 三件必做警告 (整图替换 / 删图题来源 / 检查图例) + 文件清单
- `\showteachingtrue/false` 教学开关 (默认 false) + 3 个 LaTeX 宏
  - `\Teach{...}` 红色填写提示
  - `\TeachExample{...}` 红色示例
  - `\Placeholder{...}` 黑色加粗占位符

### Changed
- `论文/论文.tex` + `论文/电子版.tex` + `论文/AI工具使用详情.tex` 顶部插入教学开关宏 (3 个文件保持一致)
- `论文/AI工具使用详情.tex` 顶部注释版本号 v1.4.3 → v1.4.4
- `SKILL.md` 顶部 metadata version v1.4.3 → v1.4.4
- `README.md` 徽章 version v1.4.3 → v1.4.4

### P2 风险标注
- 10 张示例图来源第三方 (数模陪跑独家 → "2026 华数杯 A 论文" / "26 亚太杯中文赛 B 论文"),
  PNG 本身无可执行负载, 但 `figures/README.md` 已明确警告"必须整图替换并删除图题元信息"

### 包大小
- 完整包: 19.05 → 22.41 MB (+10 张图, +13 文件)
- 轻量包: 0.31 → 3.68 MB (+10 张图, +13 文件)

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
