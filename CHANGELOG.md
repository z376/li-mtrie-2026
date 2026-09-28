# CHANGELOG (v1.5.7.25 — references/ 拆 by-category/ sub-directory, 6 类目 references 归类)

> **v1.5.7.20 之前 15 个 hotfix** (v1.5.7.5 ~ v1.5.7.19) → [`CHANGELOG-archive.md`](CHANGELOG-archive.md).
>
> **拆分原因**: 392 行累积, human 翻历史困难. 主文件只留最新 4 个 (writing-for-agents 审计 hotfix).
>
> **查找旧版本**: 用 grep 搜 `CHANGELOG-archive.md` (e.g. `grep -n v1.5.7.10 CHANGELOG-archive.md`).

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

- **SKILL.md line 1130**: 引用 `references/绘图避坑.md` (v1.5.7.19 已合并删除) → 改 `references/绘图规范与避坑.md §2`
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
- **§Step 0 4 大典型坑自查** (line 614-632): 表格 + 说明保留 (brief 经验 cache), 但补指针 → `references/红线与失败模式.md` (互补不重复)
- **§Step 4.1/4.2 xelatex 编译命令** (line 1304-1376): 命令块 (~50 行) 推进新文件 `references/scripts/check_tex_compile.md` (2.6 KB). SKILL.md 只留红/绿判据 + why ×2 解释.
- **§Step 4 开头清理命令 + 5GB 空间清单** (line 1228-1254, ~27 行): 推进 `references/scripts/check_tex_compile.md` §0 (清理命令) + §5 (空间清单, 隐含在 §1 上下文). SKILL.md 只留指针.

**P0 补 3 个完成判据** (之前缺,AI 跑题时"以为完结"风险):
- **🟢 Step 1.5 完成判据** (Tracer bullet): 数据读入 + 计算 + 出图 + 论文占位 + 编译 0 error, 全流程 ≤ 30 min. 任一 ≥ 60 min 卡住 = `red`.
- **🟢 Step 2 完成判据** (逐题求解): 5 问题 `result.xlsx` 落盘 + 每问题都进 §Step 2.Gate 8 项全勾.
- **🟢 Step 2.Gate 完成判据** (门控): 8 项 (`references/paper-spec.md §2 8 项自检`) 全 `green` + 3 条跨问题常量反问全勾. 任 1 项空 = `red` = 返工本问题.

**影响文件**:
- 新建 `references/scripts/check_tex_compile.md` (2.6 KB)
- 改 SKILL.md (-60 行)
- 整 CHANGELOG + version bump 1.5.7.19 → 1.5.7.20

**dryrun 不变**: 24/31 green + 7 yellow + 0 red (没破坏任何 check).

---

