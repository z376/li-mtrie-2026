# references/板块自查/ — 9 个论文板块级自查清单 (v1.5.3 新增)

> **借鉴源**: BZD 数模社 `bzd-math-modeling-skills-main/skills/论文自查类/` 12 个子 skill (2026-08-18).
> **本目录**: 9 个独立 references 文档, 每个 2-3.5KB, 按 论文 10 章结构 顺序组织.
> **v1.5.1 已借鉴** 3 个高层: 模型字典 / 格式自查 / 百分制评审 (放 `references/` 根).
> **v1.5.3 新增** 9 个板块级 (本目录).

## 9 个板块自查清单 (按论文写作顺序)

| # | 文件 | 章节 | 何时用 | 维度数 |
|---|------|------|--------|--------|
| 01 | [01-摘要自查.md](01-摘要自查.md) | §0 摘要 | 写完 0.摘要.tex, 终审前 1 小时 | 7 维 |
| 02 | [02-AI声明自查.md](02-AI声明自查.md) | §9.0 AI 声明 | 写完 9.0 + AI详情, 终审前 30 分钟 | 5 问 |
| 03 | [03-问题重述自查.md](03-问题重述自查.md) | §1 引言 后半 | 写完 1.引言.tex | 7 维 |
| 04 | [04-问题分析自查.md](04-问题分析自查.md) | §2 总体分析 | 写完 2.总体分析.tex | 7 维 |
| 05 | [05-模型假设自查.md](05-模型假设自查.md) | §3 模型假设 | 写完 3.模型假设.tex | 5 维/条 |
| 06 | [06-符号说明自查.md](06-符号说明自查.md) | §4 符号说明 | 写完 4.符号说明.tex | 7 维 |
| 07 | [07-模型求解自查.md](07-模型求解自查.md) | §5 建模与求解 + §6 检验 | 写完 5.1.X + 6 | 5 段 |
| 08 | [08-参考文献附录自查.md](08-参考文献附录自查.md) | §9 文献 + §10 附录 | 写完 9+10, 终审前 | P0-P3 8 维 |
| 09 | [09-AIGC审计.md](09-AIGC审计.md) | 全文 | 终审前 1 小时, 跑完 aigc_scan 后 | 9 + 6 = 15 维 |

## 用法

1. **写完每章**: 跑对应编号的 md (例如 写完 0.摘要.tex 后看 01-摘要自查.md)
2. **终审前**: 按 01→09 顺序逐个跑, 每项 ≥ 8 维绿 (或对应阈值)
3. **AI 协作**: 用 `references/llm-prompts/03-自动审稿.md` LLM 5 维评分 + 9 个自查清单互补

## 借鉴源映射 (BZD 12 子 skill → li-mtrie 9 + 3)

```
bzd-math-modeling-skills/skills/论文自查类/
├── bzd-abstract-checker          → 01-摘要自查.md        (v1.5.3)
├── bzd-ai-usage-disclosure       → 02-AI声明自查.md     (v1.5.3)
├── bzd-problem-restatement       → 03-问题重述自查.md   (v1.5.3)
├── bzd-problem-analysis-checker  → 04-问题分析自查.md   (v1.5.3)
├── bzd-model-assumption-checker  → 05-模型假设自查.md   (v1.5.3)
├── bzd-symbol-notation-checker   → 06-符号说明自查.md   (v1.5.3)
├── bzd-model-solution-checker    → 07-模型求解自查.md   (v1.5.3)
├── bzd-reference-appendix-checker→ 08-参考文献附录自查.md (v1.5.3)
├── bzd-paper-aigc-auditor        → 09-AIGC审计.md       (v1.5.3)
├── bzd-model-dictionary          → references/模型字典使用指南.md (v1.5.1)
├── bzd-paper-format-checker      → references/格式自查清单.md    (v1.5.1)
└── bzd-review-paper              → references/百分制评审方法.md  (v1.5.1)
```

## 与现有 4 文件关系

| v1.5.1+2 借鉴 | v1.5.3 板块 | 关系 |
|---|---|---|
| `references/去AIGC指南.md` (14.6KB) | 09-AIGC审计.md | 高层指南, 板块 09 是其精简方法论摘要 |
| `references/受保护片段.md` (3.2KB) | 09-AIGC审计.md § 4 轮降重 | 受保护片段是 4 轮降重的输入 |
| `references/检测平台弱点.md` (5.5KB) | 09-AIGC审计.md § 关联 | 平台弱点是检测原理背景 |
| `references/数模资料/各板块写作指南/*.pdf` (8 PDF) | 01-09 全部 | BZD 详细版 (2.1MB), 板块自查是精简方法论 |

**用法推荐**: 9 个板块自查 (1-3 分钟/个, 共 15-30 分钟) 快速走查, 详版 PDF 按需深读.

## 总结

- v1.5.3 借鉴 BZD 12 个论文自查类子 skill, 提炼为 9 个 references 文档
- 总 ~23KB, 每个 2-3.5KB (BZD 范本精简版, 不复制)
- 借鉴源 9 个 → **18 个** (mma v3.3 + bzd × 12 + 数模陪跑独家 + cumcm-live-workflow + aigc-reduce + scipilot-figure)
- 跟 v1.5.1 借鉴的 3 个高层 (字典/格式/百分制) 互补, 形成"高层 + 板块"两级自查体系
- 学生可在 30 分钟内对论文全文做一次系统自查

## 更新记录

- v1.5.3 (2026-09-06) — 9 个文件 + 1 README 索引新增, 借鉴 BZD 12 子 skill
