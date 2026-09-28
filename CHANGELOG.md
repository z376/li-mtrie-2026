# CHANGELOG (v1.5.7.31 — check 34 扩到验 18 sub-directory (原 10 漏 8 原有))

> **v1.5.7.20 之前 15 个 hotfix** (v1.5.7.5 ~ v1.5.7.19) → [`CHANGELOG-archive.md`](CHANGELOG-archive.md).
>
> **拆分原因**: 392 行累积, human 翻历史困难. 主文件只留最新 4 个 (writing-for-agents 审计 hotfix).
>
> **查找旧版本**: 用 grep 搜 `CHANGELOG-archive.md` (e.g. `grep -n v1.5.7.10 CHANGELOG-archive.md`).

## v1.5.7.31 — check 34 扩到验 18 sub-directory (v1.5.7.30 hotfix)

**核心**: writing-for-agents 审计 v1.5.7.30 发现 check 34 只验 10 个新建 sub-directory (v1.5.7.25-26 拆分), **漏 8 个原有** (2026官方答疑/examples/llm-prompts/scripts/templates/数模资料/板块自查/获奖论文). 修复:

- **check 34 扩到 19 个** (10 拆分 + 8 原有 + 1 v1.5.7.30 新建 技能总结):
  - 缺 → 红 + 提示"按 git log 看是何时删的"
  - 空 → 黄 + 提示"删除或补文件"
- **check 34 描述更新**: 加 "v1.5.7.31" 标识 + "原有 8 个被忽略" 警示

**影响文件**: dryrun.py (check 34 改 19 行 + CHECKS 改 1 行).

**dryrun**: 27/34 green + 7 yellow + 0 red (v1.5.7.31 修后, 6 维度从 4 green + 2 yellow → 5 green + 1 yellow — 仅 SKILL.md 1581 行略超 1500 仍是 yellow, 边际收益低保留).

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

