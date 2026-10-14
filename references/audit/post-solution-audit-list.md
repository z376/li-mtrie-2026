# 跑题后 16 层审计清单 (v1.5.7.41 拆段自 SKILL.md)

> **拆段原因**: v1.5.7.41 SKILL.md 1500 行临界缓解, 把 v1.5.7.35 加的 32 行表格段拆到本文件. SKILL.md 留 1 行指针 → 本文件.

## 16 层审计清单 (L1-L16)

| 层 | 检查内容 | 类型 | dryrun check | 跑题后必做 |
|---|---|---|---|---|
| L1 | 占位符未替换 | auto | check 15 + check 38 (强化) | dryrun |
| L2 | 编号对应 | auto | check 36 | dryrun |
| L3 | AI 工具禁列 | auto | check 37 (v1.5.7.35 强化) | dryrun |
| L4 | 真实性 spot-check | manual 12 步 | — | 30 min |
| L5 | 数字一致性 | manual 4 步 + check 39 留位 | check 39 (留位) | 10 min |
| L6 | result 文件 ↔ 论文数字 | auto | check 40 | dryrun |
| L7 | 附件 ↔ 正文 mtime | auto | check 41 | dryrun |
| L8 | 灵敏度表 ↔ 代码 | manual | — | 10 min |
| L9 | SOC 末值合理性 | manual | — | 10 min |
| L10 | 假设 ↔ 代码 | manual | — | 15 min |
| L11 | 旧图 ↔ result mtime | auto | check 45 | dryrun |
| L12 | 口径混用 (334/365) | auto | check 46 | dryrun |
| L13 | AI 工具条目强化 | auto | check 37 关键词扩 | dryrun |
| L18 | AIGC 2-gram TTR | auto | check 51 (v1.5.7.44 新增) | dryrun |
| L19 | AIGC 3-gram 重复率 | auto | check 52 (v1.5.7.44 新增) | dryrun |
| L20 | FVM Robin 边界离散式 | auto + manual 两道校验 | check 53 (v1.5.8 新增) | dryrun (10 min) |
| L21 | 趋势数据 IQR 误用 | auto | check 54 (v1.5.8.1 新增) | dryrun (5 min) |
| L14 | 幻觉文献 | manual (L4 步骤 2-7 覆盖) | — | (L4 内) |
| L15 | 双向题 vs 4h 窗口 | manual | — | 5 min |
| L16 | Q1 表1/表2 格式 | manual | — | 10 min |

**v5 P1 教训**: 9.0.AI工具使用声明.tex L4 仍带【简要用途】模板占位符 (check 15 漏报).
**v17 复审教训**: claude2025 AI 修复时把自己写进参考文献 [14] + li2018/zhang2022 幻觉文献 (作者/期刊/年份/卷期全错) + 表9 编造拆分 + 表q1_robust 全表编造.
**v15 终审教训**: g_adj 无上界 → 14,797 格物理不可行值 + 附件5 旧版.

## 跑题后必做顺序

dryrun sign-off 绿 (L1/L2/L3/L6/L7/L11/L12/L13 auto) → L4 (12 步, 30 min) → L5 (4 步, 10 min) → L8 (10 min) → L9 (10 min) → L10 (15 min) → L15 (5 min) → L16 (10 min), 16 层全过才交卷.

**总耗时约 90 分钟**, 比评委扣分划算.

## 详细 16 层描述

**完整 L1-L16 描述 + 常见错误修复对照表 + v15/v17 反例** 见 `references/audit/参考文献审计清单.md` (v1.5.7.35 创建 27 KB, v1.5.7.41 保持不动).

## 引用

- `SKILL.md` 1 行指针 → 本文件
- `references/audit/参考文献审计清单.md` (27 KB, L1-L16 详细描述)
- `references/audit/auto-check-list.md` (v1.5.7.41, check 45/47/48/49/50 简表)
- `references/audit/agent-audit-brief.md` (v1.5.7.41, 代理审计 brief 说明)
- `references/audit/manual-checklist.md` (v1.5.7.42 新增, 5 类 manual 兜底 L8/L9/L10/L15/L16 详细步骤 + PowerShell 命令 + 实战反例)