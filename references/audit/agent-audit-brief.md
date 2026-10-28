# 跑题后 mavis 代理审计 brief (v1.5.7.41 拆段自 SKILL.md)

> **拆段原因**: v1.5.7.41 SKILL.md 1500 行临界缓解, 把 v1.5.7.38-39 加的 3 行段拆到本文件. SKILL.md 留 1 行指针 → 本文件.

## 何时用

self-audit 47 项 hardcode 抓不到内容级问题:
- v15 P0-1 §5.3 表9 365天值冒名 334 天
- v17 P0-A 表9 编造拆分 (凑"行和=总费用"凭空构造)
- v17 P0-C claude2025 列为正式文献 [14] (AI 修复时把自己写进参考文献)
- v17 P0-D li2018/zhang2022 幻觉文献 (标题真, 作者/期刊/年份/卷期全错)
- v17 P0-B 表q1_robust 全表编造 (38,823 ≈ 36,272 × 1.07 编造痕迹)

这类问题需要上下文推理 + LP 复现 + cross-file 比对, 必须靠 mavis worker 代理审计.

## 用法 (v1.5.7.39 默认 agent 模式)

```bash
py -3 references\scripts\dryrun.py [--mode agent] --paper-dir <论文目录>
# 输出 mavis worker 代理审计 brief (含 14 类 P0 反例 + 文件清单 + 报告输出格式)
```

复制 brief 到 mavis 主对话 → mavis spawn mavis worker sub-session (独立 fresh context) 实际审计.

## 三种模式 (v1.5.7.39)

| 模式 | 行为 |
|---|---|
| `--mode agent` (默认) | agent_audit.py brief + mavis worker 代理 |
| `--mode self` | 47 项 hardcode self-audit (旧 v1.5.7.34-37 行为) |
| `--mode both` | 双重 (brief + self check) |

## 核心约束

- **每次审计 fresh 调用**, 不缓存; worker 用独立 context, 不复用主对话历史
- worker 实际读 paper + result + LP 复现 + 比对, 写报告, 返回 mavis 主对话

## 引用

- `SKILL.md` 1 行指针 → 本文件
- `references/scripts/agent_audit.py` (v1.5.7.38 完整 brief 模板源, 含 14 类 P0 反例 + 报告输出格式)
- `references/audit/post-solution-audit-list.md` (v1.5.7.41, 16 层总览)