# CHANGELOG (v1.5.7.6 — 数据隔离原则, 防 0:00 数据泄露)

> v1.5.7.6 2026 C 题实战暴露: 我 (Mavis) 之前 Q2 3 次方案全错 (用附件 2 当天实际 / 用附件 3 预报 / 缩 g 上界). 评阅要点 §2.6 明确禁止 "使用当天及以后的实际数据". 这是 CUMCM 历年最大踩坑之一, 必须文档化作为跑题核心规则.

---

## v1.5.7.9 — 三口径铁律 + 数据物理真实性 (v1.5.7.7 hotfix)

**核心**: 补 2 个未文档化的盲点, 来自 2026 C 题实战 catch:
- **总费 ≠ 紧急购电费 ≠ 调整偏差**: 3 个口径独立, 不能混算或错位对比 (Q3 总费不一定比 Q2 低, 但紧急购电一定低)
- **数据物理真实性标注**: 附件 2 全年无阴雨, 论文 §5.2.2 诚实说, 不能"修正数据"

- references/题目设计意图分析.md 加 §6 三口径铁律 (计划/紧急/调整 三独立口径 + 写论文模板)
- references/题目设计意图分析.md 加 §7 数据物理真实性 (3 反模式: 人造数据/缩 g/加噪声, 全是造假)
- SKILL.md §Step 0 必读 3 文件提示更新 (题目设计意图分析.md 8.5 KB, 含 §6/§7)
- dryrun.py 加 check 23: 验证 §6 三口径章节存在 + §7 数据物理真实性章节存在 + 扫 .py 物理造假关键词 (yellow 警告)
- 更新 §8 核心问题: "解对 = 期望命中 + 方法合理 + 数据隔离 + 三口径正确 + 数据物理真实标注"

## v1.5.7.8 — references/ 指针强化 (v1.5.7.7 hotfix)

**核心**: v1.5.7.7 新增的 references/信息边界原则.md 和 references/题目设计意图分析.md 是**被动文档**, AI 跑题时**不一定主动读**. 按 writing-for-agents "sharpen wording" 原则, 必须**显式强制** AI 必读.

- SKILL.md frontmatter description 加 1 行 "**AI 跑题前必读 references/信息边界原则.md + 题目设计意图分析.md, 否则会数据泄露 + 误读题面**" (always-loaded, AI 第一眼看到)
- SKILL.md §Step 0 顶部加 "AI 跑题前必读 3 文件" 提示段 (含 description 触发 + 3 文件 + 建议执行顺序)
- description 行数: 2 → 3 (符合 ≤ 6 行约束)

## v1.5.7.7 — 题目设计意图分析 (hotfix on v1.5.7.6)

**核心**: 跑题前必识别 **N 个问题间的递进关系 + 每个问题测什么 + 期望结果方向**, 跑完后**对照期望**, 不达预期 = 方法错, 回头改.

**实战触发**: 2026 C 题 Q3 跑出来紧急购电**比 Q2 还多** (329.7 万 vs 259.0 万 kWh), **滚动调整没起到压缩作用** — 之前测 skill 只看"流程跑通", 没看"解题是否对". Skill 必须教 agent 看穿题目设计意图.

- SKILL.md §Step 0 加 "题目设计意图分析" 章节 (递进关系 + 期望方向 + 2026 C 实战复盘)
- SKILL.md §Step 1 加 "递进关系分析" 段落 (4 步法: 画递进图 → 每个问题测什么 → 期望方向 → 跑完验证)
- references/题目设计意图分析.md (新, 6.6 KB) — 4 步法 + 3 反模式 + 2026 C 实战案例 (Q3/Q4 不达期望根因分析 + 修正方案)
- references/读题清单.md 改 5 列 (加 "题目设计意图" 第 5 列, e.g. "Q3 紧急购电应 < Q2, 否则方法错")
- dryrun.py 加 check 22 (扫描 .py 检测是否有"递进 / 设计意图 / 期望方向" 注释, yellow 警告)

## v1.5.7.6 — 数据隔离原则 (hotfix on v1.5.7.5)

**核心**: 0:00 制定计划时, **只能**基于已知信息 (历史数据 / 预报), **不能**用当天及以后实际数据 (评阅要点 §2.6).

- SKILL.md §Step 0 加 "0:00 信息边界原则" 章节 (三类信息边界表 + 反模式 + dryrun check 21 引用)
- SKILL.md §Step 1 加 "预测方法选择" 表格 (前一天实际 / N 天平均 / 同类型日平均 / ARIMA / 附件 M 预报 5 种 + 评阅要点 §2.4 分类要求)
- references/信息边界原则.md (新, 5.9 KB) — 核心规则文档化: 三类信息 + 4 反模式 + 实战案例 (2026 C Q2 踩坑复盘)
- references/读题清单.md 改 4 列 (加 "题面禁项", 防 0:00 数据泄露)
- dryrun.py 加 check 21 (扫描 .py 检测 `loads_actual[day_idx]` 无 -1 修饰, yellow 警告)
- 实战成果: 2026 C 题工作区 Q1+Q2+Q3 跑通, Q1 跟官方评阅要点参考结果一致 (59482.70 kWh, 35126.95 元)

## v1.5.7.5 — writing-for-agents 修剪 (从 SKILL.md frontmatter 拆 history)

## v1.5.7.1 — 外审 P0 + P1 修复 (hotfix on v1.5.7)

- P0 加 4 个 *Slot 宏空定义 (论文.tex/电子版.tex/AI详情.tex) 防 xelatex 编译崩
- dryrun check 15 加 \*Slot 宏扫描
- 创建 references/模型决策树.md (修复 4 处断裂引用)
- .gitignore 取消 求解/共享/*.py 排除
- 创建 求解/共享/.gitkeep
- README badge v1.5.6→v1.5.7 + 加 v1.5.7 段
- dryrun 5 处版本号更新
- check_overfull 改用 get_paper_dir()
- check_fitz_compat 加 doc 长度守卫
- SKILL.md 代码块格式修复
- README 目录结构加 v1.5.7 新文件

## v1.5.7 — 细化读题环节 (防 2025C 3 P0 错位)

- SKILL.md §Step 0 加 15 项读题清单 (防 2025C 3 P0 错位)
- 新增 references/读题清单.md (15 项空表模板)
- 新增 references/llm-prompts/05-读题提取.md (LLM 工具自动从 PDF 提取)
- dryrun.py check 19 验证 15 项全覆盖 (3 列: 题面原话 + 你的解读 + 对应代码/论文)
- 4 项跑题后对照 (项 4/5/7/14) 防 sheet 错/漏判据/自创分组/附录残留

## v1.5.4 — 防"答非所问"强化 (2025C 跑题 other agent 踩 3 P0 错后增量补强)

- SKILL.md §Step 0 加 题面 quote 锚定 + 题面关键判据 grep
- §Step 1 加 数据 sheet 选错警示
- §Step 3 加 占位符 grep 自检
- §Step 4 加 附录文件存在性自检
- 顶部加 4 大典型坑警示表
- references/scripts/dryrun.py 加 3 checkable: 15 占位符未替换 (【 TODO) / 16 10.附录.tex 文件存在 / 17 \includegraphics 图引用存在

## v1.5.3 — 借鉴 BZD 数模社 12 个论文自查类子 skill (核心理念)

- 新增 references/板块自查/ (9 文件 + 1 README) + references/题意翻译.md + references/学校国奖画像.md
- 借鉴源 9 → 18 (BZD 12 子 skill + bzd-problem-translator + bzd-cumcm-school-awards 核心理念)
- 不复制 BZD 累积数据 (版权)

## v1.5.2 — fix(scripts) 兼容 PyMuPDF ≥1.24 的 fitz deprecate

- verify_pdf_metrics.py + visual_qa.py 改 try/except 双 import

## v1.5.1 — 借鉴 BZD 数模社 bzd-model-dictionary + bzd-paper-format-checker + bzd-review-paper v1.0

- 新增 3 个 references (模型字典使用指南 / 格式自查清单 / 百分制评审方法)
- 新增 1 个 LLM 工具 04 百分制评审 (3 模式 M1/M2/M3)
- 追加 refactor P0+P1+P2 13 项 (审计 6.83→7.5/10)

## v1.5.0 — 新增 LLM 工具集成 (3 个结构化 prompt 工具) — 学生自用

## v1.4.4 — 借鉴 6 个外部 skill (数模陪跑独家 + cumcm-live-workflow + aigc-reduce + scipilot-figure + bzd-modeling-ideas + mma v3.3)
