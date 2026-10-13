# CHANGELOG (v1.5.7.42 — 5 类 manual 兜底清单 L8/L9/L10/L15/L16)

> **v1.5.7.20 之前 15 个 hotfix** (v1.5.7.5 ~ v1.5.7.19) → [`CHANGELOG-archive.md`](CHANGELOG-archive.md).
>
> **拆分原因**: 392 行累积, human 翻历史困难. 主文件只留最新 4 个 (writing-for-agents 审计 hotfix).
>
> **查找旧版本**: 用 grep 搜 `CHANGELOG-archive.md` (e.g. `grep -n v1.5.7.10 CHANGELOG-archive.md`).

## v1.5.7.42 — 5 类 manual 兜底清单 L8/L9/L10/L15/L16 (v1.5.7.41 hotfix, user 指令 "继续" → B manual 兜底)

**核心**: dryrun 47 项 hardcode 是 mechanical 防线, 5 类留位 manual (L8 灵敏度 / L9 SOC 末值 / L10 假设 vs 代码 / L15 双向题 vs 4h 窗口 / L16 Q1 表1/表2 格式) 之前只在 `references/audit/参考文献审计清单.md` 简述, 缺详细步骤 + PowerShell 命令 + 实战反例. v1.5.7.42 新建独立文件, 5 类 manual 详细描述.

**新建 `references/audit/manual-checklist.md`** (14.2 KB):

- **L8 灵敏度表 ↔ 代码** (manual, 10 min): 4 步法 (提 §6/§7/§8 表 / grep noise_injection / sweep / sensitivity / 跑 .py 验证 / 补写或删表) + 修复命令 (脚本存在但数字对不上 / 脚本不存在) + 结果图文献 §3.5 反例
- **L9 SOC 末值合理性** (manual, 10 min): 4 步法 (提 §5.X 四季表 / grep result SOC 末值 / 比对 ≤ SOC_max / 改论文) + 修复命令 (论文 SOC 末 ≠ 实际 / > SOC_max / 跨日 SOC 连续性) + 结果图文献 §3.3 反例 (SOC 13424 > 10800)
- **L10 假设 ↔ 代码** (manual, 15 min): 4 步法 (读 planner.py 找方法名 / 读 §3 假设 / 验证 1:1 对应 / 检查关键参数) + 修复命令 (方法名不一致 / 参数不一致 / §3 写"完美预测"但代码鲁棒) + v15 P0-2 + 论文综合 §3.1 反例
- **L15 双向题 vs 4h 窗口** (manual, 5 min): Q3 双向罚验证 (读 .py over_price/under_price / 跑 result over_total/under_total / §5.3 总费 = 调整购电费 + 双向罚) + Q1 6 时段验证 (result1.xlsx 合规 sheet) + 修复命令 + 论文综合 §2.3 反例
- **L16 Q1 表1/表2 格式** (manual, 10 min): 4 步法 (找合规 sheet "表1-指定时段购电" / 提取 6 个 10 分钟时段 / §5.1.2 表 2 4 小时窗口) + 修复命令 (自定义分时段 / 论文表与 result 不符 / SOC 最小值错误) + 结果图文献 §3.4 反例

**总耗时**: 50 min (L8 10 + L9 10 + L10 15 + L15 5 + L16 10)

**5 类 manual 优先级**:
- **高 (一票否决级)**: L9 SOC 末值 / L10 假设 / L15 双向罚
- **中 (扣分级)**: L8 灵敏度 / L16 Q1 格式

**改 SKILL.md** (1473 → 1474, +1 行, ≤ 1500 ✓):

- §跑题后审计清单 段加 1 行指针: "5 类 manual 兜底清单 (L8/L9/L10/L15/L16) → references/audit/manual-checklist.md (v1.5.7.42 新增, 详细步骤 + PowerShell 命令 + 实战反例)"

**影响文件**:

- 新建 `references/audit/manual-checklist.md` (14.2 KB, 5 类 manual 详细描述)
- 改 `references/audit/post-solution-audit-list.md` (引用区加 1 行 manual-checklist.md 指针)
- 改 SKILL.md (+1 行)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 30/47 green + 17 yellow + 0 red (check 35 green SKILL.md 1474 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**v1.5.7.42 配套 design pattern**: 5 类 manual 兜底集中到一个文件 (`manual-checklist.md`) 而非散在多个 sub-document, 用户跑题后 manual 阶段单点访问. 优势: 一次读完所有 manual, 5 类反例交叉对照 (e.g. L9 SOC 末值反例 + L10 假设反例 同源). 缺点: 单文件大, 后续 v1.5.7.X 可拆.

**v1.5.7.34 → v1.5.7.42 累计 9 hotfix** (跨 5 session, 4 个日历日):

- 47 项 dryrun check: 31 → 47 (净增 16 项)
- 文档: 经验汇总 13 KB, 参考文献审计清单 27 KB, 绘图规范 36 KB, references/audit/ 6 个子文件 (post-solution-audit-list / auto-check-list / agent-audit-brief / manual-checklist / 参考文献审计清单 / post-solution-audit)
- 代码: agent_audit.py 10.9 KB
- 审计架构: 单一 self → self + agent 双层 (默认 agent)
- 跑题后必做总耗时: dryrun 1 min + manual 5 类 50 min + 跨文件比对 L4 30 min = 81 min (vs 之前 90 min, manual 集中 → 节省 9 min)

---

## v1.5.7.39 — 改 dryrun 默认走代理审计, self 模式 opt-in (v1.5.7.38 hotfix)

**核心**: v1.5.7.38 默认跑 47 项 self-audit + `--agent-audit` flag 触发 mavis 代理审计. v1.5.7.39 反转默认: 跑题后**模型自主审计也调代理**, 47 项 self-audit 改为 `--mode self` opt-in.

**设计**:
- `--mode agent` (默认): 调 agent_audit.py 生成 brief, 复制到 mavis 主对话触发 worker 审计. 不跑 47 项 self check.
- `--mode self`: 跑 47 项 hardcode self-audit (mechanical 防线). 等价于旧默认行为.
- `--mode both`: 先输出 brief, 再跑 47 项 self-audit (双重审计).
- `--agent-audit` flag 向后兼容 (= agent 模式).

**改 `references/scripts/dryrun.py`** (改 main() 入口解析, +30 行):
- `--mode {agent, self, both}` 解析
- 默认 mode = "agent" (v1.5.7.39 改)
- 向后兼容 `--agent-audit` flag

**改 SKILL.md** (1500 ≤ 1500 ✓, 临界):
- §跑题后 mavis 代理审计 段加"v1.5.7.39 改为默认" + 三种模式说明

**影响文件**:
- 改 `references/scripts/dryrun.py` (+30 行)
- 改 SKILL.md (改 1 段, 0 行变化)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 30/47 green + 17 yellow + 0 red (check 35 green SKILL.md 1500 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓). `--mode self` 行为不变.

**v1.5.7.34 → v1.5.7.39 审计架构最终状态**:

| 版本 | 审计层 | 默认模式 |
|---|---|---|
| v1.5.7.34-37 | self-audit 47 项 hardcode check | 唯一模式 |
| v1.5.7.38 | + agent-audit (mavis worker 代理) | self-audit (47 项) 默认, agent opt-in via `--agent-audit` |
| **v1.5.7.39** | **同 v1.5.7.38, 改默认** | **agent 默认, self opt-in via `--mode self`** |

**用法对比**:

```bash
# v1.5.7.39 默认 = v1.5.7.38 --agent-audit
python references\scripts\dryrun.py --paper-dir <论文目录>
# 复制 brief 到 mavis 主对话 → spawn mavis worker fresh 审计

# 跑 47 项 self check (旧 v1.5.7.34-37 行为)
python references\scripts\dryrun.py --mode self --paper-dir <论文目录>
# 30/47 green + 17 yellow + 0 red

# 双重审计 (agent brief + self check)
python references\scripts\dryrun.py --mode both --paper-dir <论文目录>
```

**为何改默认**: 用户原话 "模型自主审计也调用代理" — self-audit 47 项 hardcode 是 mechanical 防线 (DPI/格式/语法), 抓不到内容级问题 (v15 P0-1 / v17 P0-A / v17 P0-C 都需要上下文推理 + LP 复现 + cross-file 比对). 默认走代理才能每次审计 fresh 抓到真问题.

---

## v1.5.7.38 — 改审计逻辑: 用户要求审计时调 mavis 代理 (v1.5.7.37 hotfix)

**核心**: dryrun self-audit 47 项 hardcode 是 mechanical 防线 (DPI/格式/语法), 抓不到内容级问题 (v15 P0-1 表9 365冒334 / v17 P0-A 编造拆分 / v17 P0-C claude2025 误列 / 数字级 LP 复现 等). 这类问题需要上下文推理 + cross-file 比对, 必须靠 mavis worker sub-session 代理审计.

**设计**:
- self-audit 47 项保留 (mechanical 防线, 防止明显 syntax/DPI/格式问题)
- **用户要求审计时**, 跑 `python references/scripts/dryrun.py --agent-audit --paper-dir <论文目录>`, 输出 markdown brief (含 14 类 P0 反例 + 文件清单 + 报告输出格式约定)
- 复制 brief 到 mavis 主对话 → mavis spawn mavis worker sub-session (独立 fresh context, **不缓存**)
- worker 实际读 paper + result + LP 复现 + 比对, 写报告, 返回 mavis 主对话 → 用户

**新建 `references/scripts/agent_audit.py`** (10.9 KB, 327 行):
- 扫 paper dir + 关键文件 (13 章节 .tex / figures/ / 求解/ / 数据/) 自动列清单
- 生成 markdown brief (含 14 类 P0 实战反例: v15 P0-1~4, v17 P0-A~E, 论文综合 §2.4/§六.1/§六.2, 结果图文献 §3.4/§3.5)
- 报告输出格式模板 (P0/P1/P2 + 数字一致性比对表 + 参考文献核验表)
- **重要约束**: 不缓存, 每次 fresh, worker 用独立 context, 不复用主对话历史

**改 `references/scripts/dryrun.py`** (+30 行):
- `--agent-audit` flag 解析: 调 agent_audit.py 生成 brief, 不跑 47 项 check
- 修 3 处 `\includegraphics` SyntaxWarning (raw string `r"""`)

**改 SKILL.md** (1500 行 ≤ 1500 ✓, 临界):
- 合并 §绘图自检 + §AIGC 扫描增强 → §跑题后自动检查 (省 6 行)
- 新增 §跑题后 mavis 代理审计 (5 行): 何时用 / 用法 / fresh 约束 / brief 模板指针

**影响文件**:

- 新建 `references/scripts/agent_audit.py` (327 行)
- 改 `references/scripts/dryrun.py` (+30 行)
- 改 SKILL.md (净 -1 行, 1500 ≤ 1500 ✓)

**dryrun**: 30/47 green + 17 yellow + 0 red (check 35 green SKILL.md 1500 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**v1.5.7.34 → v1.5.7.38 审计架构演进**:

| 版本 | 审计层 | 内容 |
|---|---|---|
| v1.5.7.34 | 参考文献 L1-L5 self-audit (4 check) | 机械: 编号对应 / AI 禁列 / 占位符强化 / 数字留位 |
| v1.5.7.35 | 赛后审计扩 L1-L16 self-audit (4 new + 词扩 14 项) | +L6 result 文件 / L7 附件 / L11 旧图 / L12 口径 + 14 AI 关键词 |
| v1.5.7.36 | 绘图自检 L14/L15 self-audit (2 check) | +L14 冗余图 / L15 图注 vs axes |
| v1.5.7.37 | AIGC 扫描 L16/L17 self-audit (2 check) | +L16 段首重复率 / L17 连接词密度 |
| **v1.5.7.38** | **+ 用户要求审计时调 mavis 代理 (fresh, 不缓存)** | **新层: 上下文推理 + LP 复现 + cross-file 比对, 抓硬编码抓不到的内容级问题** |

self-audit 47 项保留 (mechanical 防线), 用户主动要求审计时走代理 (deep audit).

---

---

## v1.5.7.34 — 参考文献 4 层审计 L1-L5 (v1.5.7.33 hotfix, 2025C v5 报告实战提炼)

**核心**: 2025C 跑题 v5 报告 P0 (摘要-§5 数字自相矛盾, 红) + P1 (9.0.AI工具使用声明.tex L4 模板占位符漏报, 红) + 教训: 参考文献审计缺自动防线. 加 4 项 check + 1 个 references 文档:

- **check 36 (L2 编号对应, auto)**: `\\cite` 与 `\\item` 互查, A-B 红 cite 不存在, B-A 黄孤儿
- **check 37 (L3 AI 工具禁列, auto)**: 扫 26 关键词 (ChatGPT/DeepSeek/Claude/Copilot/文心一言/通义千问/GPT-4/Kimi/豆包/元宝/Gemini/Llama/Qwen/Baichuan/ChatGLM/Spark/ERNIE/...), 命中红 (BZD 2026 规范)
- **check 38 (L1 占位符强化, auto, v5 P1 防御)**: 扫 9.参考文献.tex + 9.0.AI工具使用声明.tex 的 `\\textbf{【...】}` (item 内 GB/T 7714 字段占位符) + GB/T 7714 字段占位符 28 项 (【作者】/【论文题名】/【期刊名】/【出版地】/【简要用途】 等)
- **check 39 (L5 数字一致性, 留位 yellow)**: 摘要-§5 章节-Q 表互查, auto 实现复杂度高 (需解析 LaTeX 数学环境 + 跨文件 grep), 永久 yellow 留位, 短期 SKILL.md §参考文献审计清单 手动兜底

**新建 `references/audit/参考文献审计清单.md`** (11.6 KB, 4 层 L1-L5):

- **L1 占位符** (auto, dryrun check 15 + check 38)
- **L2 编号对应** (auto, check 36)
- **L3 AI 工具禁列** (auto, check 37)
- **L4 真实性 spot-check** (**manual, 12 步骤**: 文献数量 5-15 / 作者真实 / 题名真实 / 期刊真实 / 年份真实 / 卷期页码 / 类型标识 / DOI 网址 / 引用覆盖 / AI 工具未误列 / 与 result 一致 / 格式统一)
- **L5 数字一致性** (manual + 兜底清单 + check 39 留位)

**SKILL.md 加 §参考文献审计清单** (19 行): 紧跟 Post-Solution Audit, 4 层概览 + 跑题后必做顺序

**影响文件**:

- 改 `references/scripts/dryrun.py` (+163 行: AI_TOOL_FORBIDDEN_KEYWORDS 26 项 + GB_T_7714_TEMPLATE_FIELDS 28 项 + check_ref_number_consistency + check_ai_tool_in_refs + check_template_placeholders_v2 + check_39_numeric_consistency_reserved + CHECKS 4 行)
- 新建 `references/audit/参考文献审计清单.md` (11.6 KB)
- 改 SKILL.md (+19 行, 总 1483 ≤ 1500 ✓)
- 改 CHANGELOG.md (主文件移 v1.5.7.30 → archive)

**dryrun**: 29/39 green + 10 yellow + 0 red (check 35 green SKILL.md ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**v5 报告 P0/P1 防御映射**:

| v5 报告问题 | 防御 check |
|---|---|
| v5 P1 9.0.AI工具使用声明.tex L4【简要用途】 | check 38 (扫【简要用途】/【简要填】/【这里填】) |
| v5 P0 摘要 Q3 节约 5.7% vs §5.3 反贵 5.4% | check 39 留位 + SKILL.md 手动清单 |
| v5 P0 摘要 Q4-2 = 1504万 vs §5.4 = 2183万 vs 文件 = 1843万 | check 39 留位 + SKILL.md 手动清单 |
| v5 P0 §5.1.2 鲁棒差额 +2552 vs +9648 | check 39 留位 + SKILL.md 手动清单 |
| v5 P0 §5.2 紧急购电 11.6 vs 110.9 vs 589 万 | check 39 留位 + SKILL.md 手动清单 |
| v4 P1 9.参考文献.tex han/wang 作者错 | L4 步骤 2 真实作者 spot-check |
| v4 P1 6 条未引用 | check 36 (cite 与 item 互查) |
| v5 验证 AI 工具未误列 ✓ | check 37 (L3 强化, 防止以后误列) |

---

## v1.5.7.31 — check 34 扩到验 18 sub-directory (v1.5.7.30 hotfix)

**核心**: writing-for-agents 审计 v1.5.7.30 发现 check 34 只验 10 个新建 sub-directory (v1.5.7.25-26 拆分), **漏 8 个原有** (2026官方答疑/examples/llm-prompts/scripts/templates/数模资料/板块自查/获奖论文). 修复:

- **check 34 扩到 19 个** (10 拆分 + 8 原有 + 1 v1.5.7.30 新建 技能总结):
  - 缺 → 红 + 提示"按 git log 看是何时删的"
  - 空 → 黄 + 提示"删除或补文件"
- **check 34 描述更新**: 加 "v1.5.7.31" 标识 + "原有 8 个被忽略" 警示

**影响文件**: dryrun.py (check 34 改 19 行 + CHECKS 改 1 行).

**dryrun**: 27/34 green + 7 yellow + 0 red (v1.5.7.31 修后, 6 维度从 4 green + 2 yellow → 5 green + 1 yellow — 仅 SKILL.md 1581 行略超 1500 仍是 yellow, 边际收益低保留).

---

## v1.5.7.29 — Q3 跑题 4 方案验证, 改写 §4.3 期望方向 (v1.5.7.28 hotfix)

**核心**: 跑题 4 方案对比 (Q2 + Q3 v1 + v4 + v5), 实战验证后改写 `references/design-intent/题目设计意图分析.md §4.4`:

| 方案 | 2.1-12.31 总费 | 紧急购电 |
|---|---:|---:|
| Q2 (全天前一天实际, 无滚动) | 1405.7 万 | 259 万 |
| Q3 v1 (附件 3 PV + 4 滚动, 原) | — | **329.7 万** |
| Q3 v4 (前一天实际 + 4 滚动) | 1310.1 万 | 698.8 万 |
| **Q3 v5 (前一天实际 + 不滚动)** | **1268.7 万** | 674.6 万 |

**关键发现**:

1. **滚动调整物理上无法压缩紧急购电** (紧急购电来自"今天 vs 昨天预测误差", 滚动不改变预测). Q3 v4 (4 滚动) e=698.8 万 > Q2 (无滚动) e=259 万, **反而更大** (分段拼接非全天最优 LP).
2. **附件 3 滚动预报 PV 有害**: v1 e=329.7 > Q2 e=259. 用前一天实际全天 PV 最优.
3. **Q3 真正最优 = Q3 v5** (前一天实际 + 不滚动 = Q2 全天 LP): 总费 1268.7 万, 比 Q2 1405.7 万省 137 万 (全天电池最优调度).
4. **修正期望方向**: Q3 设计意图 "e < Q2 e" **物理上不可达**, 应改为 "Q3 总费 ≤ Q2 总费" (通过全天电池调度优化).

**结论**: 跑题用户遇到 Q3 e > Q2 e 时, **不要尝试用滚动调整压低 e** (无效), 应该接受 "Q3 = Q2 全天" 然后优化总费用. **滚动调整是政治正确但物理上无效**.

**影响文件**: `references/design-intent/题目设计意图分析.md` (§4.4 新增, 4 方案对比表 + 4 条关键发现 + 修正期望方向).

**dryrun 不变**: 27/34 green + 7 yellow + 0 red.

---

## v1.5.7.28 — 加 3 dryrun check 护 writing-for-agents 约束 (v1.5.7.27 hotfix)

**核心**: 加 3 个 dryrun check 把 writing-for-agents 硬约束程序化护住, 防止后续 hotfix 误破:

- **check 32** (v1.5.7.28): SKILL.md description 行数 ≤ 6 (writing-for-agents 硬约束). 红时给提示 "合并触发器 + 砍冗余 5 道防线版本号串".
- **check 33** (v1.5.7.28): SKILL.md leading words 锚定 10 词全在 (green/red/sign-off/checkable/探路弹/check N/5 道防线 + 反模式/陷阱/踩坑/避坑). 红时给提示 "在 §Step 0 顶部 '📌 核心 leading words' 表加这 N 个词".
- **check 34** (v1.5.7.28): references/ 10 sub-directory 全在 (by-category/data-usage/design-intent/read-checklist/workflow/paper/plot/aigc/audit/preparation), 且非空. 缺 → 红, 空 → 黄.

**影响文件**: dryrun.py (3 check 函数 + CHECKS 3 行).

**dryrun**: 24/31 → **27/34 green** + 7 yellow + 0 red (3 check 全 green, 0 破现有 check).

---

## v1.5.7.27 — 修 SKILL.md + CHANGELOG stale references + leading words 统一表 (v1.5.7.26 hotfix)

**核心**: v1.5.7.26 拆分 sub-directory 后, SKILL.md + CHANGELOG.md 还有 47 处 stale 平铺引用 (`references/xxx.md` 应为 `references/subdir/xxx.md`), 批量替换 + 1 处 leading word 锚定:

**修 1**: SKILL.md 44 处 + CHANGELOG.md 3 处 平铺引用批量替换 sub-directory prefix.

**修 2**: SKILL.md line 1131 stale ref (`绘图避坑.md` 历史文件名) → 加 "(两文件已删除, 详版含审稿人视角 + 代码示例)" 说明, 避免 reader 误解"这文件还在".

**修 3**: SKILL.md §leading words 锚定表 (v1.5.7.22 加的) 扩 4 个词:
- **`反模式`** (anti-pattern) — 技术/BZD 文档, 抽象方法错误
- **`陷阱`** (trap) — 可视化/scipilot, 具体可视化错误
- **`踩坑`** — 历史**案例** (踩坑案例/教训), 替代"过去反例/真实失败"
- **`避坑`** — 前瞻**体系** (避坑体系/规范), 替代"防错指南"

之前 SKILL.md 9 处混用踩坑/避坑, 经扫确认各上下文匹配 (踩坑=历史案例, 避坑=前瞻体系), 实际不需要统一, **但通过 leading words 表明确分工**, AI 后续写作时不混用.

**未动 (合理保留)**:
- CHANGELOG-archive.md 24 处平铺引用 — 是 v1.5.7.18 合并等**历史事实**, 旧路径应保留 (历史不能改写).

**dryrun 不变**: 24/31 green + 7 yellow + 0 red.

---

## v1.5.7.26 — references/ 拆 9 个 sub-directory (v1.5.7.25 hotfix)

**核心**: 27 个平铺 .md 按用途归类到 9 个新 sub-directory + 1 个已存在 (by-category/):

| sub-directory | 文件数 | 文件 |
|---|---|---|
| `data-usage/` | 2 | 信息边界原则, 合规检查清单 |
| `design-intent/` | 2 | 题目设计意图分析, 5道防线自检清单 |
| `read-checklist/` | 4 | 读题清单, 红线与失败模式, 题意红线, 题意翻译 |
| `workflow/` | 5 | workflow, 模型字典使用指南, 模型决策树, 整题建模模式, 导入规范 |
| `paper/` | 4 | paper-spec, 国奖级硬性指标, 格式自查清单, 百分制评审方法 |
| `plot/` | 2 | 绘图规范与避坑, 图型选择决策 |
| `aigc/` | 2 | AIGC降重策略, 去AIGC指南 |
| `audit/` | 2 | 验收清单, post-solution-audit |
| `preparation/` | 4 | 赛前学习清单, 角色Prompt, 策略输出规范, 学校国奖画像 |

**影响**:
- SKILL.md §Step 0 索引表 10 类用途引用全改 sub-directory 路径
- SKILL.md §Step 0 类目适配段引用 (line 389-399)
- SKILL.md line 1121 AIGC 引用
- dryrun.py 21 处 `REFS_DIR / "xxx"` 路径改 `REFS_DIR / "subdir" / "xxx"`
- 42 references 文件 156 处交叉引用改 sub-directory 前缀 (含 llm-prompts/ 板块自查/ scripts/ templates/ 数模资料/ examples/)

**dryrun 不变**: 24/31 green + 7 yellow + 0 red (v1.5.7.25 的 by-category/ 路径继承,不需要新 check).

---

## v1.5.7.25 — references/by-category/ sub-directory (v1.5.7.24 hotfix)

**核心**: 6 个类目 references (物理/数据/优化/经济/生物/交通) 从 `references/` 平铺 → `references/by-category/` sub-directory:
- 物理机理类典型反模式.md
- 数据分析类典型反模式.md
- 优化类典型反模式.md
- 经济金融类典型反模式.md
- 生物医疗类典型反模式.md
- 交通运筹类典型反模式.md

**影响**:
- SKILL.md §Step 0 类目适配段 6 行引用改 `references/by-category/xxx.md` (line 389-399)
- SKILL.md §Step 0 索引表 7 类题专属行加 "(v1.5.7.25 移到 sub-directory)"
- dryrun.py check 26 + 27 路径改 `REFS_DIR / "by-category" / "xxx类典型反模式.md"` (4 处 tuple)

**dryrun 不变**: 24/31 green + 7 yellow + 0 red.

---

## v1.5.7.24 — 拆 CHANGELOG (v1.5.7.23 hotfix)

**核心**: CHANGELOG.md 392 行累积, 拆为:
- `CHANGELOG.md`: 76 行 (最新 4 entries: v1.5.7.21-23 + 本次 v1.5.7.24)
- `CHANGELOG-archive.md`: 349 行 (v1.5.7.5 ~ v1.5.7.19 共 15 条历史 hotfix)

**影响文件**: CHANGELOG.md (392 → 76) + CHANGELOG-archive.md (新建 349).

**dryrun 不变**: 24/31 green + 7 yellow + 0 red.

---


## v1.5.7.23 — stale references 清理 (v1.5.7.22 hotfix)

**核心**: 扫描所有 .md 文件找 stale references (引用已删除的旧文件), 修 2 处:

- **SKILL.md line 1130**: 引用 `references/绘图避坑.md` (v1.5.7.19 已合并删除) → 改 `references/plot/绘图规范与避坑.md §2`
- **绘图规范与避坑.md line 9-12**: 顶部 "与 references/绘图避坑.md 显式分工" (文件已不存在, "显式分工" 不再成立) → 加 "(v1.5.7.23 已废弃 — 两文件合并到本文件, 此段留作版本历史)"

**未动 stale (归因保留, 非 stale)**:
- AIGC降重策略.md "来自 受保护片段.md §X" — 这是合并过程的归因 (类似参考文献), 保留说明来源

**影响文件**: SKILL.md (-1 行) + 绘图规范与避坑.md (+1 段说明).

**dryrun 不变**: 24/31 green + 7 yellow + 0 red.

---

## v1.5.7.22 — writing-for-agents 审计 P2 收尾 (v1.5.7.21 hotfix)

**核心**: writing-for-agents 审计最后一项 P2 — leading word 锚定 + 中文化:
- **`tracer bullet` → `探路弹`** (5 处替换): §Step 1.5 标题 + 解释 + "30 分钟探路流程" + "没跑探路弹" 踩坑教训 + 完成判据. 中文 prior 强 (学生都打过枪/知道"先打一发试路径").
- **加 SKILL.md leading words 锚定段** (line 46 之后): 6 个核心 leading word 统一表 (green/red/sign-off/checkable/探路弹/check N/5 道防线), 后续写作按此表.

**影响文件**: SKILL.md (5 处替换 + 1 段新增).

**dryrun 不变**: 24/31 green + 7 yellow + 0 red.

---

## v1.5.7.21 — writing-for-agents 审计 P1 收尾 (v1.5.7.20 hotfix)

**核心**: v1.5.7.20 P0 修复后的 3 项 P1:
- **description 砍 "5 道防线" 行** — 该行是 cache (版本号串 v1.5.7.5-9), AI 决策不需要. description 从 5 行内容变 4 行内容, ~200 chars 节省.
- **"4 处 注意: no-op 删" — 实际不存在**. v1.5.7.5 修剪已清掉大部分 no-op 标签 (注意/警告/重要), 搜了 6 种模式无结果. 跳过该项.
- **加 references/ 索引表** — §Step 0 末尾加 10 类用途索引 (数据使用/设计意图/7 类题专属/跑题前自检/跑题中参考/写论文/绘图/AIGC/赛后验收/模板+脚本), human 索引负担 ↓↓↓.

**影响文件**: SKILL.md (description -200 chars + 索引表 +16 行).

**dryrun 不变**: 24/31 green + 7 yellow + 0 red.

---

## v1.5.7.20 — writing-for-agents 审计 P0 修复 (v1.5.7.19 hotfix)

**核心**: 用户用 `writing-for-agents` skill 审计 li-mtrie-2026 skill, 报告 6 维度 12 项问题 (P0/P1/P2). 用户选 P0 全修: **拆 SKILL.md 1609 行 → 1549 行 (-60 行) + 补 3 个缺失的完成判据**.

**P0 拆 SKILL.md 3 处**:
- **§Step 0 4 大典型坑自查** (line 614-632): 表格 + 说明保留 (brief 经验 cache), 但补指针 → `references/read-checklist/红线与失败模式.md` (互补不重复)
- **§Step 4.1/4.2 xelatex 编译命令** (line 1304-1376): 命令块 (~50 行) 推进新文件 `references/scripts/check_tex_compile.md` (2.6 KB). SKILL.md 只留红/绿判据 + why ×2 解释.
- **§Step 4 开头清理命令 + 5GB 空间清单** (line 1228-1254, ~27 行): 推进 `references/scripts/check_tex_compile.md` §0 (清理命令) + §5 (空间清单, 隐含在 §1 上下文). SKILL.md 只留指针.

**P0 补 3 个完成判据** (之前缺,AI 跑题时"以为完结"风险):
- **🟢 Step 1.5 完成判据** (Tracer bullet): 数据读入 + 计算 + 出图 + 论文占位 + 编译 0 error, 全流程 ≤ 30 min. 任一 ≥ 60 min 卡住 = `red`.
- **🟢 Step 2 完成判据** (逐题求解): 5 问题 `result.xlsx` 落盘 + 每问题都进 §Step 2.Gate 8 项全勾.
- **🟢 Step 2.Gate 完成判据** (门控): 8 项 (`references/paper/paper-spec.md §2 8 项自检`) 全 `green` + 3 条跨问题常量反问全勾. 任 1 项空 = `red` = 返工本问题.

**影响文件**:
- 新建 `references/scripts/check_tex_compile.md` (2.6 KB)
- 改 SKILL.md (-60 行)
- 整 CHANGELOG + version bump 1.5.7.19 → 1.5.7.20

**dryrun 不变**: 24/31 green + 7 yellow + 0 red (没破坏任何 check).

---

