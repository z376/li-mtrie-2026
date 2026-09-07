# CHANGELOG (v1.5.7.5 — 从 SKILL.md frontmatter 拆出)

> v1.5.7.5 writing-for-agents 6 维度审计后, history 9 entries 从 SKILL.md frontmatter 推到本文件, 减轻 SKILL.md context load. GitHub release notes 同源, 网页端也能看.

---

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
