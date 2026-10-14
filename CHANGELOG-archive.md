# CHANGELOG-archive (v1.5.7.44 — v1.5.7.43 check 40 完整版入档, v1.5.7.19 及之前)

> **历史归档** — v1.5.7.30 之前的 hotfix. 最新 hotfix 见 [`CHANGELOG.md`](CHANGELOG.md).
>
> **保留原位说明**: 拆 CHANGELOG 不删历史 (git log 仍在, 文件仍在). 这个 archive 文件让 human 不需要 scroll 392 行.

---

## v1.5.7.43 — check 40 完整版: LaTeX 数学环境解析 + 偏差分级 (v1.5.7.42 hotfix, user 指令 "继续" → A 完整 L6)

**核心**: v1.5.7.35 check 40 简化版只做数量级比对 (0.5-2.0x green), 抓不到 v15 P0-1 / 论文综合 10 处 P0 数字偏差. v1.5.7.43 升级为完整版, 解析 LaTeX 数学环境 + 按问题编号配对 + 偏差分级阈值.

**改 `references/scripts/dryrun.py`** (+110 行, check 40 完整重写):

- **解析 LaTeX 数学环境**: regex 提取 `$...$` (行内) + `\[...\]` (显示) + `\begin{equation}...\end{equation}` + `\begin{align}...\end{align}` 4 种环境
- **数字 + 单位推断**: 数学环境内提取 `1,234,567 / 1234 / 1234.56 / 1.2e5` 模式, 上下文 (前 20 字符) 推断单位 (元/万元/百万/亿)
- **按问题编号配对**: 章节 → result key 映射 (5.1 → result1, 5.2 → result2, 5.3 → result3, 5.4 → result4-2, 0.摘要 → all)
- **取论文数字中位数 vs result max 列**: 对每个 result key (1/2/3/4-2), 取该章节论文数字中位数, 跟 result 对应 sheet 最大数字列比对
- **3 级偏差阈值**:
  - < 1% green (高精度匹配)
  - 1-5% yellow (可接受, 人工核对)
  - > 5% red (v15 P0-1 / 论文综合 10 处 P0 防御, 需修复)
- **结果文件最大数字列**: 替代简化版"前 3 列求和", 改用"每 sheet 最大数字"避免求和误差

**v1.5.7.35 简化版 → v1.5.7.43 完整版对比**:

| 维度 | v1.5.7.35 简化版 | v1.5.7.43 完整版 |
|---|---|---|
| 论文 .tex 提取 | 行内 `数字+元/万` regex | 解析 4 种 LaTeX 数学环境 + 单位推断 |
| result 提取 | 每行前 3 列求和 | 每 sheet 最大数字列 |
| 配对 | 数量级 (论文均值 / result 总和) | 按问题编号 (5.1 → result1, ...) |
| 阈值 | 0.5-2.0x green, 否则 yellow | < 1% green / 1-5% yellow / > 5% red |
| 抓 v15 P0-1 (3197.7 万 vs 1843 万) | ✗ (数量级都在) | ✓ (按 result3 max 比对, 偏差 73%) |
| 抓 v17 P0-A (表9 编造拆分) | ✗ (单看数字看不出) | ✓ (按 5.3 章节 + result3, 总费偏差必暴露) |

**改 SKILL.md** (1474 → 1474, +0 行, 描述不变):

- §跑题后审计清单 段 check 40 描述更新 (via dryrun CHECKS list 内部)

**影响文件**:

- 改 `references/scripts/dryrun.py` (check 40 +110 行, CHECKS list +1 行)
- 改 SKILL.md (frontmatter bump v1.5.7.42 → v1.5.7.43)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 30/47 green + 17 yellow + 0 red (check 35 green SKILL.md 1474 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**v1.5.7.43 check 40 实战价值**:

- v15 P0-1 (§5.3 表9 3197.7 万 vs result3 实际 2918.3 万): 偏差 9.6% → **red**
- 论文综合 §2.4 (Q4 论文数与任一口径都不符): 按 5.4 章节 result4-2 配对 → 偏差大 → **red**
- 真实跑题论文 (result 与 §5.X 一致): < 1% → **green**
- 跑题用户写论文时随时跑 dryrun check 40, 立即看到 result vs 论文 偏差

**v1.5.7.43 后续优化方向** (留位):

- check 40 当前用每 sheet 最大数字, 复杂论文可能 sheet 名含"调整"等关键词, 误选. v1.5.7.X 可加 sheet 名启发式 (e.g. "总费用"/"购电费"/"成本" 优先)
- 论文数字可能单位混用 (e.g. "31,288,350 元" vs "3,128.8 万"), 当前单位推断有 edge case. 可加二次扫描 (e.g. 找数字最近的"万/亿"字符)
- result 多 sheet 时, 取最大数字可能跨 sheet. 可加 cross-sheet 校验 (e.g. 计划购电费 + 紧急购电费 ≈ 总费用)

---

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

## v1.5.7.41 — SKILL.md 拆段, 1500 行临界缓解 (v1.5.7.40 hotfix, user 指令 "继续" → A 拆段)

**核心**: v1.5.7.40 SKILL.md 1500 行 (临界, check 35 护栏 ≤ 1500). v1.5.7.41 拆 3 段 (37 行) → `references/audit/` 子文件, 留 6 行指针, **净减 27 行 (1500 → 1473)**, 留 27 行 buffer 给后续 hotfix.

**拆段设计** (3 段 → 3 子文件 + 1 指针段):

| SKILL.md 拆出段 (行数) | 拆到文件 | 子文件大小 |
|---|---|---|
| §参考文献与赛后审计清单 (32 行, v1.5.7.35 加, 16 层表) | `references/audit/post-solution-audit-list.md` | 2.5 KB |
| §跑题后自动检查 (3 行, v1.5.7.36-37 合并) | `references/audit/auto-check-list.md` | 2.2 KB |
| §跑题后 mavis 代理审计 (3 行, v1.5.7.38-39 加) | `references/audit/agent-audit-brief.md` | 1.8 KB |
| **合 1 段指针 (6 行)** | 留 SKILL.md | — |

**新建 3 个 references/audit/ 子文件**:

- `post-solution-audit-list.md` (2.5 KB): 16 层总表 + 跑题后必做顺序 + 90 min 总耗时 + v5/v15/v17 教训 + 引用
- `auto-check-list.md` (2.2 KB): 绘图自检 3 check (45/47/48) + AIGC 扫描 2 check (49/50) + Sep 13 报告阈值映射 + 引用
- `agent-audit-brief.md` (1.8 KB): self vs 代理分层 + 用法 + 3 模式 (agent/self/both) + 核心约束 + 引用

**改 SKILL.md** (1500 → 1473 行, 净减 27 行):

- §参考文献与赛后审计清单 (32 行) + §跑题后自动检查 (3 行) + §跑题后 mavis 代理审计 (3 行) → 合并为 1 段指针 (6 行)
- 净 -32 行 + 6 行 = -27 行 ✓

**改 SKILL.md 1500 行硬约束护栏 (check 35) 缓解**:

- 后续 hotfix 加新章节时, 不必先拆旧章节腾空间, 直接加 ≤ 27 行
- 历史 v1.5.7.20-39 累计加 ~80 行, 拆 -27 行, 缓冲 27 行, 后续 hotfix 仍有 ~50 行空间可加 (按当前平均每次 +10 行算, 5 个 hotfix 不拆)

**影响文件**:

- 新建 `references/audit/post-solution-audit-list.md` (2.5 KB)
- 新建 `references/audit/auto-check-list.md` (2.2 KB)
- 新建 `references/audit/agent-audit-brief.md` (1.8 KB)
- 改 SKILL.md (-27 行)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 30/47 green + 17 yellow + 0 red (check 35 green SKILL.md 1473 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**v1.5.7.41 配套拆段后续 hotfix 设计模式** (可复用):

- SKILL.md 1500 行临界是 writing-for-agents 硬约束 (check 35 护栏)
- 每次加新章节先评估: 现有内容能否拆到 references/? (e.g. §审计清单 → references/audit/, §绘图规范 → references/plot/, §AIGC 策略 → references/aigc/)
- 拆段准则: SKILL.md 留 1 段指针 (~5-10 行) + references/ 留完整文档. 用户查找成本可接受
- 不拆: 单文件大文档 (e.g. paper-spec.md 33 KB, 主题独立); SKILL.md 核心流程 (流程必须 inline, 不能拆)

---

## v1.5.7.40 — 收匠期 v2: 跨 v1.5.7.34-39 实战提炼 6 类方法论 (user 指令 "继续" → A 收匠期)

**核心**: v1.5.7.30 收匠期 (跨 v1.5.7.10-29) 之后, v1.5.7.34-39 又跨 3 session (Oct 3 × 2 + Oct 14 × 1) 完成 6 个 hotfix, 加 14 项 check + 改审计逻辑 (self → agent 默认). 把 v1.5.7.34-39 实战提炼 3 大类方法论加到现有经验汇总, 同时同步 user.md 跨项目方法论.

**3 大新方法论** (在 v1.5.7.30 经验汇总的 A/B/C 3 类基础上, 扩展为 6 类):

- **D. 实战反例驱动 check 设计** (v1.5.7.34-37 实战): 跑题后审计历史 6 份关键报告 (Sep 11-13) → 提炼 18 类 P0 反例 → 14 项 auto check. 4 步法: 找 P0 反例 / 分类映射 L1-L16 / 决定 check 类型 (mechanical auto / 上下文 manual / 跨文件 brief) / 加阈值 (报告实测值作基准)
- **E. self-audit vs 代理审计分层** (v1.5.7.38-39 实战): self-audit 47 项 hardcode = mechanical 防线, mavis worker 代理 = 内容级. user 原话"模型自主审计也调用代理" → 改默认走代理, self 模式 opt-in (`--mode self`)
- **F. 代理审计 brief 模板设计** (v1.5.7.38 实战): agent_audit.py brief 4 段结构 (审计目标 / 文件清单 / checklist / 报告格式) + 14 类 P0 反例清单 + 关键设计原则 (每次 fresh / 不要省略数字 / 不要给模糊建议 / 不要只看封面 / 报告 ≤ 30 KB)

**改 documents**:

- 扩 `references/技能总结/经验汇总.md` (5.8 KB → ~13 KB, 178 → ~330 行): v1.5.7.30 A/B/C → v1.5.7.40 A/B/C/D/E/F 6 类
  - C.1 版本演进表加 v1.5.7.30 + v1.5.7.34-39 共 7 行
  - C.3 dryrun 终极状态更新 (47 项, 30/47 green + 17 yellow + 0 red, 默认 agent 模式)
  - D. 实战反例驱动 check 设计: 18 类 P0 反例 → check 映射表 + 4 步法 + 高频复用表
  - E. self-audit vs 代理审计分层: 两层分工 + 改默认逻辑 + 3 模式 + agent vs self check 阈值差异
  - F. 代理审计 brief 模板设计: 4 段结构 + 关键原则 + 14 类 P0 反例 + mavis 主对话 orchestration
  - G. 引用 (v1.5.7.40 增): CHANGELOG + 5 个新 references 文档
- 改 `user.md` (46 → 81 行, +35 行): 加 "赛后审计分层 + 代理审计 brief 设计 (2026-10-14, v1.5.7.34-39 实战提炼)" 跨项目方法论摘要, 涵盖核心问题 / 两层分工 / 4 步法 / brief 4 段 / 关键原则 / --mode 三种 / SKILL.md 行数预算 / 6 hotfix 总览
- 改 SKILL.md (frontmatter bump v1.5.7.39 → v1.5.7.40)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 30/47 green + 17 yellow + 0 red (check 35 green SKILL.md 1500 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**跨项目适用性** (user.md 摘要):
- 适用于所有需要 self-audit vs 代理审计分层的 AI agent / 数模 skill
- 实战反例 → auto check 设计 4 步法, 适用于任何"赛后审计 → 下次防"循环
- brief 模板 4 段结构 + 关键设计原则, 适用于任何"调 LLM 代理做内容审计"流程
- SKILL.md ≤ 1500 行硬约束 + 每次加新章节必须先合并/拆旧章节, 适用于所有 writing-for-agents skill

**v1.5.7.34 → v1.5.7.40 累计 hotfix 7 个** (vs v1.5.7.10-29 共 20 个):
- 47 项 dryrun check 增长: 31 (v1.5.7.29) → 47 (v1.5.7.40), 净增 16 项
- 文档: 经验汇总 5.8 → 13 KB (D/E/F 3 大类新增), 参考文献审计清单 11.6 → 27 KB (L1-L16), 绘图规范 33 → 36 KB (R1-R5)
- 代码: agent_audit.py 10.9 KB 新建
- 审计架构: 单一 self-audit → self + agent 双层 (默认 agent, fresh worker)
- 6 session 跨 4 个日历日 (Sep 28, Oct 3 × 2, Oct 14) 累计

---

## v1.5.7.37 — AIGC 扫描增强 L16/L17 (v1.5.7.36 hotfix, Sep 13 AIGC 报告实战提炼)

**核心**: Sep 13 AIGC 报告 §2.1-2.2 (连接词密度 7.5%, 段首重复率 39.6%) 实战提炼, 加 2 项 dryrun check 自动扫 AIGC 痕迹.

- **check 49 (AIGC 段首重复率 L16, auto)**: 扫论文 13 个章节 .tex 段首 2 字符, 算重复率 (总段数 - 唯一段首数) / 总段数. <30% green / 30-50% yellow (Sep 13 报告 39.6% 同等) / >50% red (偏高, AIGC 风险). 防 Sep 13 报告 §4 优化建议: "问题" ×12 偏多, 替换为"本问/该问题/此问题".
- **check 50 (AIGC 连接词密度 L17, auto)**: 扫同时/然而/因此/此外/更进一步/与此同时/综上所述/可以看出/值得注意的是/由此可见 等 10 项关键词, 计算连接词数 / 句子数. <10% green (Sep 13 报告 7.5% 同级) / 10-15% yellow / >15% red. 防 Sep 13 报告 §2.1 "同时" ×8 偏多.

**改 SKILL.md** (1497 → 1501, ⚠️ 接近 check 35 上限 1500 — 后续 hotfix 应先拆已有段):

- §AIGC 扫描增强 (4 行): Sep 13 报告实战 + check 49/50 简表 + 桌面路径指针

**影响文件**:

- 改 `references/scripts/dryrun.py` (+170 行: AIGC_CONNECTOR_KEYWORDS 10 项 + check_segment_opener_repetition + check_connector_density + CHECKS 2 行)
- 改 SKILL.md (+4 行)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 30/47 green + 17 yellow + 0 red (check 35 green SKILL.md 1501 ≤ 1500? ⚠️ 略超, 需后续 hotfix 拆段; check 33 green leading words 11 个全在 ✓).

**Sep 13 AIGC 报告阈值映射**:

| 报告维度 | Sep 13 阈值 | check 49/50 阈值 | 防御动作 |
|---|---|---|---|
| 段首重复率 | 39.6% (可接受) | <30% green / 30-50% yellow / >50% red | 分散段首为变体 (本问/该问题/此问题) |
| 连接词密度 | 7.5% (低) | <10% green / 10-15% yellow / >15% red | 替换"同时/然而/因此"为"且/并/另一方面" |
| "同时" 偏多 | ×8 | check 50 子项 top3 | 替换 2-3 处为"且/并" |
| "问题" 段首 | ×12 (因"问题一/二/三/四") | check 49 段首重复率 | 改为"本问/该问题/此问题" |
| "本文" 段首 | ×6 | check 49 段首重复率 | 改为"本研究/笔者" |

---

## v1.5.7.36 — 绘图自检 3 类实战图问题 (v1.5.7.35 hotfix, v15/v17/论文综合 §六提炼)

**核心**: v15 终审 (Sep 13) + v17 复审 (Sep 13) + 论文综合 (Sep 12) + 结果图文献 (Sep 11) 4 份实战报告 P0/P1 暴露 3 类图问题, dryrun 已加 check 47/48 自动防御, §八 自检清单扩 3 条 + §十 实战反例加新章节.

- **check 47 (冗余图 L14, auto)**: 调 `references/scripts/check_figure.py:find_unused_figures` 扫 figures/ 中未被任何 .tex `\\includegraphics` 引用的 .png/.pdf/.svg. 防论文综合 §六.2 反例 (8 张冗余未引用图残留: q2_季节PV箱线图.png / q2_累计费用.png / q2_梅雨敏感性.png 等).
- **check 48 (图注 vs axes L15, auto)**: 调 `references/scripts/visual_qa.py:check_caption_axes_consistency` 扫 PDF 中 caption 含多面板语义 ("上/下/(a)/(b)/左/右") 与 figure 实际 axes 数是否一致. 防论文综合 §六.1 反例 (图注称"上:购电量与电价, 下:储能SOC", 实际只有单面板).

**改 documents**:

- 扩 `references/plot/绘图规范与避坑.md`:
  - §八 自检清单加 3 条 (图注 vs axes / 冗余图 / 旧图)
  - 新增 §十 实战反例 (R1 旧图 + R2 冗余图 + R3 图注不符 + R4 中文方块 + R5 文字越界), 每类配反例 + 防御 + 修复命令
  - §六 版本历史加 v1.5.7.36 entry
- 改 `references/scripts/check_figure.py` (+50 行): 新加 `find_unused_figures()` 函数, 供 check 47 调用
- 改 `references/scripts/visual_qa.py` (+80 行): 新加 `check_caption_axes_consistency()` 函数 + 模块 docstring 更新, 供 check 48 调用

**改 SKILL.md** (1492 → 1497 行, ≤ 1500 ✓):

- §绘图自检 (5 行): 简表 + 3 类实战图问题 + 跑题后必跑 dryrun 指针

**影响文件**:

- 改 `references/scripts/dryrun.py` (+115 行: check_unused_figures + check_caption_axes_consistency + CHECKS 2 行)
- 改 `references/scripts/check_figure.py` (+50 行)
- 改 `references/scripts/visual_qa.py` (+80 行)
- 改 `references/plot/绘图规范与避坑.md` (+~120 行 §八 + §十 + §六)
- 改 SKILL.md (+5 行)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 29/45 green + 16 yellow + 0 red (check 35 green SKILL.md 1497 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**v15/v17/论文综合 P0/P1 反例防御映射**:

| 报告问题 | 防御 check / docs |
|---|---|
| v15 P0-3 §5.4 图7/图8 是 g_adj 修复前旧图 | check 45 (L11) + 绘图规范 §十 R1 |
| v17 P0-E 图7/8/q1_不确定性分配 旧图 | check 45 (L11) + 绘图规范 §十 R1 |
| 论文综合 §六.1 图1 SOC 子图缺失 (图注不符) | check 48 (L15) + 绘图规范 §十 R3 |
| 论文综合 §六.2 8 张冗余未引用图残留 | check 47 (L14) + 绘图规范 §十 R2 |
| 结果图文献 §四 图3 英文标签 (v4 P1 已修, 防回腐) | 绘图规范 §十 R4 + visual_qa.check_layout |

---

## v1.5.7.35 — 赛后审计扩到 16 层 L1-L16 (v1.5.7.34 hotfix, v17 复审+论文综合+结果图文献实战提炼)

**核心**: 比赛时审计历史 27 个报告 (Sep 11-13) 揭示 5 类 L1-L5 之外的新检查点. 加 4 项 auto check + 1 项关键词扩 + 扩 documents。

- **check 40 (L6 result 文件 ↔ 论文数字, auto 简化版)**: regex 提取 .tex "数字+元/万" + resultX.xlsx 各 sheet 求和, 数量级比对 (0.5-2.0x green). 防 v15 P0-1 (§5.3 表9 365天冒名334天) + 论文综合 10 处 P0 数字偏差 + v17 P0-A 表9 编造拆分.
- **check 41 (L7 附件 ↔ 正文 mtime, auto)**: 数据/附件/附件N/*.xlsx mtime vs 论文最新 mtime vs 求解/最新 mtime. 附件旧于求解 2h+ 红, 旧于论文 2h+ 黄. 防 v15 P0-4 + v17 P0-E 附件5 旧版.
- **check 45 (L11 旧图 ↔ result mtime, auto)**: includegraphics 引用的 .png vs 求解/最新 mtime. 旧于求解 12h+ 红, 2h+ 黄. 防 v15 P0-3 §5.4 图7/图8 + v17 P0-E.
- **check 46 (L12 口径混用, auto)**: 扫摘要 + §5.X 含 334 天/365 天/2.1-12.31/1.1-12.31/2025.2.1/2025.1.1 关键词. ≥ 2 种口径 红. 防 v15 P0-1 + 论文综合 §2.4 Q4 论文数与任一口径都不符.
- **check 37 关键词扩 (L13 AI 工具条目强化, 26 → 40 项)**: 加 Claude Sonnet/Anthropic/OpenAI/GPT-4 Turbo/GPT-4V/o1-preview/o3-mini/Sora/Mistral/Mixtral/Claude Opus/Claude Haiku/Claude 3.5/Claude 4. 防 v17 P0-C claude2025 AI 修复时把自己写进参考文献 [14].

**改 documents**:

- 扩 `references/audit/参考文献审计清单.md` (11.6 KB → 27 KB): 从 L1-L5 扩到 L1-L16, 加 L6/L7/L11/L12 auto + L8 灵敏度 / L9 SOC末值 / L10 假设vs代码 / L15 双向题vs窗口 / L16 Q1表1表2 manual 兜底. 每层 8 类 v15/v17 反例对照表.

**改 SKILL.md** (1463 → 1492 行, ≤ 1500 ✓):

- §参考文献审计清单 改名为 §参考文献与赛后审计清单 (17 行 → 32 行), 加 16 层表 + 跑题后必做顺序 + 总耗时 90 min.

**影响文件**:

- 改 `references/scripts/dryrun.py` (+310 行: AI_TOOL_FORBIDDEN_KEYWORDS 26→40 + check_result_vs_paper_numeric + check_attachments_vs_paper_mtime + check_figure_mtime_vs_solve + check_calendar_window_consistency + CHECKS 4 行)
- 改 SKILL.md (+29 行)
- 改 CHANGELOG.md (主文件更新标题 + 移 v1.5.7.30 → archive 在 v1.5.7.34 已做)
- 改 `references/audit/参考文献审计清单.md` (11.6 KB → 27 KB)

**dryrun**: 29/43 green + 14 yellow + 0 red (check 35 green SKILL.md 1492 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

---

## v1.5.7.33 — check 35 加 SKILL.md ≤ 1500 行护栏 (v1.5.7.32 hotfix)

**核心**: writing-for-agents 6 维度全 green 后, **加 check 35 防止 sprawl 回腐** (后续 hotfix 加 inline reference 又把 SKILL.md 撑 > 1500 行).

- **check 35** (v1.5.7.33): SKILL.md 行数 ≤ 1500
  - ≤ 1500 → green
  - > 1500 → red + 提示"拆 inline reference 到 references/<sub-dir>/<topic>.md, 范本: v1.5.7.32 把 §Step 3 + §Step 4.1 117 行拆到 references/paper/写作与附录检查.md"

**影响文件**: dryrun.py (check 35 + CHECKS 1 行).

**dryrun**: 27/35 green + 7 yellow + 0 red (check 35 green, 当前 SKILL.md 1464 行).

**check 32/34/35 现状** (v1.5.7.28 + v1.5.7.31 + v1.5.7.33 三个 writing-for-agents 护栏):
- check 32: SKILL.md description ≤ 6 行 (always-loaded 体积)
- check 34: references/ 18 sub-dir 全在 (架构)
- check 35: SKILL.md ≤ 1500 行 (Two loads)

---

## v1.5.7.32 — SKILL.md 1581 → 1464 行 (-117, 拆 inline reference 到 references/paper/) (v1.5.7.31 hotfix)

**核心**: writing-for-agents 2 yellow → 1 yellow (Two loads 修复, Pruning 已在 v1.5.7.31 修复). 把 §Step 3 末尾 + §Step 4.1 共 ~117 行 inline reference 拆到新文件:

- **新建 `references/paper/写作与附录检查.md`** (4.2 KB):
  - §1 LLM 工具集成 (3 prompt + 核心原则 + 协同)
  - §2 题意红线 4 条 (用真实几何 / 解析验证 / 验证链 / 5 步自查)
  - §3 PDF 成品结构体检 (verify_pdf_metrics.py)
  - §4 占位符 grep 自检 (PowerShell 命令 + dryrun check 15)
  - §5 附录文件存在性自检 (PowerShell 命令 + 2025C 反例 + dryrun check 16)
- **SKILL.md §Step 3 末尾** 5 段 inline 改 1 行指针
- **SKILL.md §Step 4.1** 附录检查 inline 改 1 行指针

**影响文件**: 新建 `references/paper/写作与附录检查.md` (4.2 KB) + 改 SKILL.md (-117 行).

**dryrun**: 27/34 green + 7 yellow + 0 red.

**writing-for-agents 6 维度最终状态**:

| 维度 | v1.5.7.31 | v1.5.7.32 |
|---|---|---|
| 1. Context pointer | ✅ green | ✅ green |
| 2. Two loads | ⚠️ yellow (1581) | ✅ green (1464 ≤ 1500) |
| 3. Information hierarchy | ✅ green | ✅ green |
| 4. Steps + completion | ✅ green | ✅ green |
| 5. Leading words | ✅ green | ✅ green |
| 6. Pruning | ✅ green (v1.5.7.31) | ✅ green |

**6 green + 0 yellow** — 全维度 green.

---

## v1.5.7.30 — 收匠期 (v1.5.7.29 hotfix, 跨 2 session 经验汇总)

**核心**: v1.5.7.10 → v1.5.7.29 共 20 hotfix 跨 Sep 18 + Sep 28 两 session 收尾. 用户说"收集一下经验", 3 处全存:

1. **`references/技能总结/经验汇总.md`** (8.6 KB, 新文件):
   - **A. skill 维护方法论** (writing-for-agents 6 维度 / 抽象化 3 步 / 拆分决策 / dryrun 3 check)
   - **B. 数模答题方法论** (设计意图 4 步 / 数据隔离 3 类 / Q3 物理边界发现 / 跑题工作流)
   - **C. 项目特定决策** (v1.5.7.10-29 版本表 / 最终结构 / dryrun 终极状态)
   - **D. 引用** (CHANGELOG + 题目设计意图 §4.4 + 本目录)

2. **`user.md` 加 2 条** (跨项目方法论):
   - **Skill 维护方法论** (writing-for-agents 6 维度 / 抽象化 / 拆分 / dryrun 3 check)
   - **数模滚动决策题物理边界** (滚动调整无效 / 前一天实际最优 / 期望方向修正)

3. **本 CHANGELOG entry** (v1.5.7.30 收匠期记录).

**影响文件**: 新建 `references/技能总结/经验汇总.md` (8.6 KB) + 改 user.md.

**dryrun 不变**: 27/34 green + 7 yellow + 0 red.

---

## v1.5.7.19 — 绘图文档合并 (v1.5.7.18 hotfix)

**核心**: 用户提议合并 "去AIGC指南 + 板块自查 9 板块" / "角色Prompt + 模型字典使用", 但**两个候选都不合适合并**:
- 去AIGC指南 + 板块自查/09-AIGC审计: 板块自查本就是精简版 (README 表格已明示"板块 09 是去AIGC指南的精简方法论摘要"), 合并会失去分层价值 (9 板块自查变 50 KB 单文件, 反扫描效率下降)
- 角色Prompt + 模型字典使用: 主题不重叠 (一个 LLM prompt 模板, 一个 BZD 模型字典用法)

按 v1.5.7.18 "How + What Not" 模式找真正可合并的, 找到 **绘图规范 + 绘图避坑**:
- `references/绘图规范.md` (21.4 KB) = "How" (字号/线宽/DPI/字体/颜色/机理题专用图型 怎么写对) — 顶部已显式声明分工
- `references/绘图避坑.md` (15.9 KB) = "What Not" (18 条陷阱 — 主动拦截)
- 同 v1.5.7.18 AIGC 合并的 "什么不能改 + 怎么改有效" 模式

合并方案:

- **新建 `references/绘图规范与避坑.md`** (~22 KB):
  - §1 画图前决策三轴 (来自 绘图规范 §0 — 选对图型)
  - §2 18 条画图陷阱清单 (来自 绘图避坑 — 完整版权威源, P1-P18)
  - §3 出图后程序自检 + 完整 matplotlib 设置 (来自 绘图规范 §1+ — 字号/线宽/DPI/字体/配色)
  - §4 协同路径 (How → What Not → check_figure.py)
  - §5 与现有文档协同 (paper-spec / AIGC降重策略 / check_figure.py)
  - §6 版本历史
- **删除** `references/绘图规范.md` + `references/绘图避坑.md` (内容已合并)
- **保留** 板块自查/9 板块 + 角色Prompt + 模型字典使用 (主题独立, 不动)

**dryrun 加 check 31**: 验证 绘图规范与避坑.md 3 关键章节齐 + 绘图规范/绘图避坑 不应存在.

**影响文件**: 1 新文件 + 2 删除 + dryrun.py (check 31).

**dryrun**: 23/30 → **24/31 green** + 7 yellow + 0 red.

---

## v1.5.7.18 — AIGC 文档合并 (v1.5.7.17 hotfix)

**核心**: 用户要求合并 `references/红线与失败模式.md` + `references/受保护片段.md` + `references/检测平台弱点.md`. 但**红线与失败模式.md 主题独立** (跑题失败/代码/合规 — 跟 AIGC 无关), 不动. 真正可合并的是 **受保护片段.md (3.5 KB) + 检测平台弱点.md (5.7 KB)**, 主题都是 AIGC 降重:

- `受保护片段.md` = "什么不能改" (5 类禁改 + 核心铁律 + 改写前预检)
- `检测平台弱点.md` = "怎么改有效" (4 平台 + 3 档修改率 + 实战策略)

合并方案:

- **新建 `references/AIGC降重策略.md`** (9.4 KB, 总 KB 减少 10%):
  - §1 核心铁律 (来自受保护片段)
  - §2 5 类禁改片段 (来自受保护片段)
  - §3 4 大检测平台对比 (来自检测平台弱点)
  - §4 知网 3.0 详细原理 (来自检测平台弱点)
  - §5 PaperPure 详细原理 (来自检测平台弱点)
  - §6 3 档修改率 (来自检测平台弱点)
  - §7 实战策略 (合并 改写前预检 + 3 轮协议 + 6 件不能做)
  - §8 心态校准
  - §9 与现有文档协同表 (合并 受保护片段 §4 + 检测平台弱点 §7)
  - §10 版本历史
- **删除** `references/受保护片段.md` + `references/检测平台弱点.md` (内容已合并, 留旧文件会引混乱)
- **保留** `references/红线与失败模式.md` (2.2 KB, 主题独立, 不合并)
- **更新引用**:
  - SKILL.md §Step 4 AIGC 段 (合并 5 类禁改 + 4 平台引用为 1 行 AIGC降重策略.md)
  - `references/去AIGC指南.md` §第一轮/§引用 (2 处)
  - `references/板块自查/README.md` + `09-AIGC审计.md` 表格 (2 处)

**dryrun 加 check 30**: 验证 AIGC降重策略.md 4 关键章节齐 + 受保护片段/检测平台弱点 不应存在 (yellow if 旧文件残留).

**影响文件**: 1 新文件 + 2 删除 + 5 引用更新 + dryrun.py (check 30).

**dryrun**: 22/29 → **23/30 green** + 7 yellow + 0 red.

---

## v1.5.7.17 — 信息边界 + 题目设计意图 重复段合并 (v1.5.7.16 hotfix)

**核心**: 信息边界原则.md (v1.5.7.6) 和 题目设计意图分析.md (v1.5.7.7) 有两处重复:
1. **"数据物理真实性 / 缩 g / 人造梅雨季 / 加噪声" 反模式 — 两份都讲**. 信息边界 §2 反模式 2 含完整缩 g 代码; 题目设计意图 §7 整个段 (含反模式 1-3 + 评阅对应章节引用).
2. **Q2 数据隔离 4 方案 + Q3 滚动调整实战** — 信息边界 §4 实战案例 与 题目设计意图 §4.1 调度类实战 有部分重叠.

合并方案:
- **信息边界原则.md §2 反模式 2** 删除完整缩 g 代码块,改为引用 → "→ 见 references/题目设计意图分析.md §7 数据物理真实性标注". 信息边界文档瘦身 (~ 200 字).
- **信息边界原则.md §4 实战案例**: 删 Q3 滚动调整实战 (跟题目设计意图 §4.1 重叠), 改为指针 → "Q3 滚动调整实战 → 见 references/题目设计意图分析.md §4.1". Q2 4 方案保留 (核心数据隔离案例).
- **题目设计意图分析.md §7** 完整保留 — 它是合并后唯一含完整缩 g/Luca 反模式 + 论文 §5.2.2 标注模板 的权威源.

**dryrun 加 check 29**:
- 信息边界 §2 反模式 2 不含完整缩 g 代码 (应引用 §7, 不重复)
- 信息边界 §2 反模式 2 含 "§7" + "题目设计意图分析" 引用
- 题目设计意图 §7 仍存在 + 含 "数据物理真实性"

**影响文件**: 信息边界原则.md (~1 KB 瘦身) + dryrun.py (check 29 新增).

**dryrun**: 21/28 → **22/29 green** + 7 yellow + 0 red.

---

## v1.5.7.16 — 周期起点决策概念升级 (v1.5.7.15 hotfix, 防 0:00 锚定陷阱)

**核心**: 用户反馈 "0:00 决策就有很强的 c 题优化性, 通用性不强, 你可以优化; 删除, 或者合并". v1.5.7.6 信息边界原则 用 "0:00 决策" / "0:00 LP" 等概念 — 0:00 本身就是 C 题 (调度类) 每日决策的典型时刻, 锚定到调度类. 修复: 概念升级为**周期起点决策 (Period-Start Decision)**, 任何滚动决策题 (每日 0:00 / 班次开始 / 月初 / 期货开盘) 都适用, 0:00 仅作调度类典型例子.

**改动**: 12 文件 73 处 0:00 概念批量替换为 "周期起点":
- "0:00 决策" → "周期起点决策"
- "0:00 制定计划" → "周期起点制定计划"
- "0:00 LP" → "周期起点 LP"
- "0:00 信息边界" → "周期起点信息边界"
- "0:00 用当期实际" → "周期起点用当期实际"
- 保留 `day_idx` 代码示例中的具体数值 (代码示例细节保留, 概念名升级)
- 信息边界原则.md: 30 处 (核心文档, 概念升级最彻底)
- SKILL.md: 18 处 (顶部 5 道防线速查表 + §Step 0/1)
- 题目设计意图分析.md / 5道防线自检清单.md / 读题清单.md / 5 份类目 references: 各 1-6 处

**dryrun 配套修复**:
- check 21: 改检测 "周期起点信息边界" (原 "0:00 信息边界原则") + 描述升级 "0:00 → 周期起点"
- 新加 **check 28**: 验证 信息边界原则.md + SKILL.md + 5道防线自检清单.md 都用 "周期起点" 概念 (green if 全替换)

**影响文件**: 10 markdown + dryrun.py (check 21 升级 + check 28 新增).

**dryrun**: 20/27 → **21/28 green** + 7 yellow + 0 red.

---

## v1.5.7.15 — 7 类目 references (v1.5.7.14 hotfix, 扩 3 类)

**核心**: v1.5.7.14 覆盖 4 类题 (调度/物理/数据/优化), 但**经济金融/生物医疗/交通运筹**这 3 类 (MCM/ICM 美赛常考, 本科 B/A 题也可能考) 没专属 references. 修复: 加 3 份独立 references.

- **新建 references/经济金融类典型反模式.md** (5.8 KB):
  - §1 经济金融类典型反模式 (10 行: 数据来源不标/单位基点错误/时序用未来信息/风险度量选错/市场有效过头/没考虑极端/黑盒无解释/历史回测不报告/监管合规忽略/滚动决策用未来信息)
  - §2 跑题前自检 checklist (9 项, 含数据来源完整 + 单位基点统一 + 风险度量 + 压力测试 + 回测计划)
  - §3 跑完后期望对照表 (6 项: 时序严格/超额收益/风险度量准确/极端场景/可解释性/合规约束)
  - §4 滚动决策 vs 单时点决策 子类分叉
- **新建 references/生物医疗类典型反模式.md** (5.7 KB):
  - §1 生物医疗类典型反模式 (10 行: 自创机理/个体差异忽略/单位错误/伦理隐私/基线不齐/样本量不足/多重比较未校正/因果vs相关/临床指标选错/跨问题数据混用)
  - §2 跑题前自检 checklist (9 项, 含机理引用 + 个体差异 + 临床单位 + 数据脱敏 + 基线比较 + 功效分析)
  - §3 跑完后期望对照表 (6 项: 模型拟合/临床指标/个体差异/极端场景/灵敏度/多重校正)
  - §4 与物理机理类 的差异表 (6 维度: 机理来源/单位/个体差异/隐私/多重比较/因果)
- **新建 references/交通运筹类典型反模式.md** (6.6 KB):
  - §1 交通运筹类典型反模式 (10 行: 网络结构漏标/流量单位混淆/动态静态混淆/路径假设"最短"/算法不适用/容量约束漏写/时空约束漏写/多目标加权随意/计算时间缺失/可执行性忽略/滚动决策用未来信息)
  - §2 跑题前自检 checklist (10 项, 含网络结构完整 + 流量单位统一 + 动态/静态 + 算法选择 + 容量时空约束表)
  - §3 跑完后期望对照表 (8 项: 算法适用性/gap/约束满足/计算时间/Pareto/整数化/时空一致/滚动预测)
  - §4 动态调度 vs 静态规划 子类分叉 + §5 与优化类/调度类 关系表
- **SKILL.md §Step 0 顶部** 类目适配段 4 类扩到 **7 类** (调度/物理/数据/优化 + 经济/生物/交通)
- **dryrun.py 加 check 27**: 验证 3 新类目 references 全在 + 含类目专属术语 (经济=基点/生物=多重校正/交通=Pareto)

**影响文件**: 3 新文件 + SKILL.md (类目适配扩 7 类) + dryrun.py (check 27).

**dryrun**: 19/26 → **20/27 green** + 7 yellow + 0 red.

---

## v1.5.7.14 — 4 类目专属 references (v1.5.7.13 hotfix)

**核心**: v1.5.7.13 加了类目适配段 (调度/物理/数据/优化 4 类), 但**只标了适配度**, 没给类目专属 references. 跑题用户遇到物理题/数据题/优化题时, 仍需**自己拼凑**类目专属反模式. 修复: 加 3 份独立 references.

- **新建 references/物理机理类典型反模式.md** (4.5 KB):
  - §1 物理机理类典型反模式 (8 行: 自创方程/边界条件漏写/单位不一致/模型假设过头/数值方法选错/网格细化/守恒律验证/不找借口)
  - §2 跑题前自检 checklist (9 项, 含物理定律引用 + 模型假设清单 + 单位声明 + 数值方法)
  - §3 跑完后期望对照表 (5 项: 物理量守恒/网格收敛/解析解对比/极限情况/参数灵敏度)
  - §4 与 5 道防线引用关系 + §6 引用 BZD 模型字典
- **新建 references/数据分析类典型反模式.md** (5.7 KB):
  - §1 数据分析类典型反模式 (10 行: 预处理不报告/划分不报告/指标选错/特征堆砌/模型对比缺失/训练-测试 gap/类别不平衡/置信区间缺失/可解释性缺失/数据泄露)
  - §2 跑题前自检 checklist (9 项)
  - §3 跑完后期望对照表 (6 项: gap/关键指标/类别不平衡/异常值检测/特征 importance/随机种子稳定性)
  - §4 数据使用纪律 (变体 — 时序严格性, 不是 0:00 决策但仍是数据使用)
- **新建 references/优化类典型反模式.md** (4.8 KB):
  - §1 优化类典型反模式 (10 行: 决策变量定义不清/目标函数简化/约束漏写/算法选错/黑盒无验证/灵敏度缺失/权重随意/不可行解处理缺失/数据使用违规/整数化忽略)
  - §2 跑题前自检 checklist (9 项)
  - §3 跑完后期望对照表 (6 项: 算法适用性/gap/约束满足/灵敏度/Pareto/整数化)
- **SKILL.md §Step 0 顶部**: 5 道防线速查表下加 "类目适配" 段 (4 行: 调度/物理/数据/优化 → 对应 references)
- **dryrun.py 加 check 26**: 验证 3 类目 references 全在 + 含类目专属术语 (物理=网格收敛/数据=训练-测试/优化=gap)
- **修复 SKILL.md frontmatter BOM 问题** (Python Set-Content 加 BOM, 导致 check 7/20 失败): 移除 BOM + 修 description 后空行

**影响文件**: 3 新文件 + SKILL.md (顶部类目适配) + dryrun.py (check 26).

**dryrun**: 18/25 → **19/26 green** + 7 yellow + 0 red.

---

## v1.5.7.13 — 类目适配说明 (v1.5.7.12 hotfix, 防通用性陷阱)

**核心**: 用户反馈 "新增的几个文件还是对 c 题的优化, 通用性还是有问题". v1.5.7.10-12 抽象化"包装" (去 "2026 C 题" 字符串), 但**内容仍是 C 题 (调度类) 专属案例** — 物理机理题/数据分析题/优化题 完全跑不通. 修复:

- **5道防线自检清单.md**:
  - 顶部加 "⚠️ 类目适配" 段 (新章节, 在 §1 前): 4 类题适配度表 + 替换方式
  - §2 反模式速查表 12 行 加 [通用]/[调度类]/[物理]/[数据] tag
  - §3 自检 checklist 拆 "通用项 (6)" + "调度类专属 (4)", 调度类项末尾加"物理题/数据题跳过, 替换为本类目检查"
  - §4 期望对照表 加 "调度类示例" 警告, 末尾给物理题/数据题替代示例 (相对误差 < 5% / 训练-测试 gap < 10% 等)
- **信息边界原则.md** 顶部加 "⚠️ 适用题类: 滚动调度/滚动决策类题" 段: 明确不适用于物理机理题/数据分析题 (这类题无 0:00 决策结构)
- **题目设计意图分析.md §6 三口径铁律** 顶部加 "⚠️ 适用题类: 调度/滚动决策类题专属" 段
- **题目设计意图分析.md §7 数据物理真实性** 顶部加 "⚠️ 适用题类: 通用" 段 (这章节所有题类都适用)
- **dryrun.py 加 check 25**: 验证 3 份 references 顶部都含类目适配说明 (red if 缺)

**影响文件**: references/5道防线自检清单.md (顶部 + §2 + §3 + §4) + references/信息边界原则.md (顶部) + references/题目设计意图分析.md (§6 + §7 顶部) + references/scripts/dryrun.py (check 25).

**dryrun**: 17/24 → **18/25 green** + 7 yellow + 0 red.

---

## v1.5.7.12 — description 锐化 (v1.5.7.11 hotfix)

**核心**: 按 writing-for-agents 6 维度审计 v1.5.7.11 的 SKILL.md description (7 行), 锐化到 4 行:

- **必读指针扩 2 → 3**: 加 v1.5.7.11 新增的 `references/5道防线自检清单.md` (中心索引 + 反模式 + checklist)
- **5 道防线锚定**: 新增 1 行明确列 5 个防线 + 版本号, 让 AI 第一眼知道"5 道防线"框架
- **触发器尖锐化**: "pastes 数模赛题 PDF 并说开始跑题" → "用户贴题目 PDF + '开始跑题'/求解后'出论文 PDF'/验本 skill"
- **反 trigger 收紧**: "general data analysis, one-off Python scripts" → "普通数据分析 / one-off Python / 非论文交付的研究问题"

**审计 6 维度** (writing-for-agents 原则):
1. **触发清晰**: ✓ "用户贴 PDF + 3 个动作" 一行讲清
2. **必读指针**: ✓ 3 references + 各自用途
3. **核心规则**: ✓ 5 道防线 + 版本号 (强化防线 4)
4. **反 trigger**: ✓ "非论文交付"
5. **行数**: ✓ 4 行 (≤ 6 约束)
6. **尖锐度**: ✓ "防数据泄露 / 防按字面跑不解题 / 5 道防线"

**影响文件**: SKILL.md (description + metadata.version 1.5.7.9 → 1.5.7.12).

**dryrun**: 17/24 green + 7 yellow + 0 red (check 7 frontmatter + check 20 description ≤ 6 行 全绿).

---

## v1.5.7.11 — 5 道防线集中索引 (v1.5.7.10 hotfix)

**核心**: 5 道防线是**被动文档**, AI 跑题时容易漏. 集中索引让"被动 → 主动必读":

- **新建 references/5道防线自检清单.md** (6.5 KB):
  - §1 5 道防线总览表 (防线/版本/触发/文档/check)
  - §2 反模式速查表 (12 行: 反模式 + 防线 + 修法 + dryrun)
  - §3 跑题前自检 checklist (10 项, 5 分钟)
  - §4 跑完后期望对照 checklist (5 项, 10 分钟)
  - §5 引用关系 + §6 版本演进
- **SKILL.md §Step 0 顶部加 5 道防线速查表** (6 行: 防线/触发/规则/文档/check)
- **dryrun.py 加 check 24**: 验证 `references/5道防线自检清单.md` 存在 + 4 章节齐全 + SKILL.md 引用

**影响文件**: references/5道防线自检清单.md (新, 6.5 KB) + SKILL.md (顶部速查表) + references/scripts/dryrun.py (check 24).

**dryrun**: 16/23 → **17/24 green** + 7 yellow + 0 red.

---

## v1.5.7.10 — 通用化抽象清理 (v1.5.7.9 hotfix)

**核心**: v1.5.7.9 提交后本地未 commit 的 3 文件残留 (SKILL.md / 信息边界原则.md / 题目设计意图分析.md), 抽象化替换**不干净**, 留下占位符 ("验证基线" / "调整后紧急购电 (万 kWh 量级, > 基线 = 方向错)") 反而更乱. 修复策略:

- **通用化**: "2026 C 题" → "调度类", "微电网" → "调度类", "评阅要点 §2.6" → "评阅要点对应章节 '数据使用' 条款 (每年 4 月公布, 跑题前查最新)"
- **反例数字保留**: e=259.0 万 / 329.7 万 / 315/334 / 362/365 / 333.8 万 这些是"方向错"的反例证据, 抽象掉就失去警示价值
- **占位符清除**: "验证基线" / "调整后紧急购电 (万 kWh 量级, > 基线 = 方向错)" 等占位符全部还原成具体数字
- **"2024 C 题" → "2024 调度类"**: 年份具体 + 类目通用, 不双重抽象
- **文件末尾补换行**: 信息边界原则.md 补 LF

**影响文件**: SKILL.md / references/信息边界原则.md / references/题目设计意图分析.md (3 文件 21 行 +/- 平衡, 0 占位符残留)

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
