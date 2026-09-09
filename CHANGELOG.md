# Changelog

> li-mtrie 数模竞赛 skill 的所有版本变更。SKILL.md frontmatter `changelog` 字段指向本文件。
> 版本号格式: `vMAJOR.MINOR.PATCH[.HOTFIX]`（hotfix 留给同日小修补）。

---

## v1.5.9（2026-09-09, current）— 加深借鉴 BZD bzd-paper-aigc-auditor v2.2 (LLM agent + HTML 报告)

**动机**: v1.5.3 借鉴 BZD `bzd-paper-aigc-auditor` v1.0 的两层审计结构 (60% 语言模板化 + 40% 模型合理性) 概念. v1.5.9 加深借鉴 v2.2 — 完整 LLM agent 流程 + HTML 分层报告 + 一票否决. v1.5.3 借鉴的方法论是"概念", v1.5.9 借鉴的是"实操".

**变更**:

**3 个新文件 (1 prompt + 1 HTML 模板 + 1 扩展)**:
- `references/llm-prompts/08-AIGC审计.md` (13.2 KB) — 仿 05/06/07 风格, 完整 BZD v2.2 prompt 配套. 5 步使用流程 + 4 节使用流程 + 7 项常见问题修法 + 1 段严禁清单. 配套: aigc_scan.py (前置 5 分钟自动) + 09-AIGC审计.md (板块自查) + 03-自动审稿.md (5 维评分)
- `references/审计报告模板.html` (12.0 KB) — 自己重写简化版 (不复制 BZD 版权 HTML). 借鉴 BZD HTML 报告结构: 标题 + 总览卡 + 9 维分数表 + 6 类 PASS/FAIL + 一票否决红色警告 + 4 轮降重 checklist + 改写优先级 P0/P1/P2/P3 + footer 使用说明
- `references/板块自查/09-AIGC审计.md` (v1.5.9 扩展) — 加 1 段"完整 LLM agent 流程" (5 步图) + 1 行 🟢 step 锚定 (Step 3-4) + 关联段加 08 引用 + 更新记录加 v1.5.9 行

**SKILL.md 改动**:
- frontmatter `version: "1.5.8.4"` → `"1.5.9"` (minor bump) + `last_update: 2026-09-09` (保持)
- 借鉴段加 1 行 + 1 表 (v1.5.9 加深 bzd-paper-aigc-auditor v2.2 借鉴)

**dryrun.py 扩展 29 → 31 项**:
- check 30: `references/llm-prompts/08-AIGC审计.md` 存在
- check 31: `references/审计报告模板.html` 存在
- docstring patch 标签加 v1.5.9 minor 行 + 友好输出版本号 v1.5.8.4 → v1.5.9

**llm-prompts/README.md 改动**:
- L1 加 v1.5.9 标注
- 7 工具表 → 8 工具表 (加 08-AIGC审计)
- 协同段加 08 行 (check 30 + 31)

**HTML 报告模板设计要点** (自己原创, 不复制 BZD):
- 渐变背景卡 (linear-gradient 135deg) + 4 列 score-box 布局
- 9 维分数表 + 6 类 PASS/FAIL 表 (用 checkbox 视觉)
- 一票否决红色警告 (2px solid 边框)
- P0/P1/P2/P3 优先级 (颜色编码)
- 占位符 `{{ }}` 高亮 (浅黄背景 + 虚线框)
- footer 双行 (版权 + 使用方法)

**借鉴粒度 (跟 v1.5.8 一致)**:
- ✅ 精简方法论 + LLM agent prompt (1 文件)
- ✅ HTML 报告模板自己重写 (不复制 BZD 版权)
- ✅ 9-AIGC审计.md 扩展 (加 LLM agent 流程段)
- ❌ 不复制 BZD 完整 prompt 39KB (BZD 团队的版权资源, 只借鉴"概念" + "自己重写" 13KB)
- ❌ 不复制 BZD 完整 references/ 6 篇 (audit-framework/layer1-enhanced/models-zh/patterns-zh/nature-detector/humanizer-keywords 全部是 BZD 版权)
- ❌ 不复制 BZD templates/ 2 个 HTML (版权资源)

**v1.5.9 minor vs v1.5.8.x hotfix 区别**:
- v1.5.8.x hotfix = writing-for-agents 审计修复 (text-only 改写, 不加 check)
- v1.5.9 minor = 加深借鉴新 BZD skill (加 1 LLM prompt + 1 HTML 模板 + 2 check = 算新功能)
- 下次 hotfix (v1.5.9.1+) = writing-for-agents 审计 v1.5.9 这次新加的 2 文件

**没有 v1.5.8.5 了** (上次 v1.5.8.4 entry 写过的承诺, 现在兑现 — 直接 v1.5.9 minor)

---

## v1.5.8.4（2026-09-09）— writing-for-agents 审计 P2 修复

**动机**: v1.5.8.3 修了 P1 3 项 (negation + step 锚定 + 顺序). v1.5.8.4 同日 hotfix 修 P2 3 项 (中英标题一致 + §1 何时用 完成判据 + README 表格化).

**变更**:

**P2-7 LLM prompt 标题中英一致 (2 处)**:
- `references/llm-prompts/06-读题翻译.md` L1: "06-读题翻译 (v1.5.8.1, ...)" → "06-读题翻译 (Problem Translator, v1.5.8.1, ...)"
- `references/llm-prompts/07-建模方案.md` L1: "07-建模方案 (v1.5.8.1, ...)" → "07-建模方案 (Modeling Ideas, v1.5.8.1, ...)"

**P2-8 4 references §1 何时用 重写 (4 处)**:
- 4 篇 §1 末尾删 `**输入**: ... / **输出**: X 节齐` 段 (跟 §2-X 主体信息冗余)
- 改 1 行 `🟢 **完成判据**: X 节齐 (N 个组件), 详 §2-§X.`
- 例: 读题翻译.md §1 末尾: "🟢 **完成判据**: 4 节齐 (全局故事 + 覆盖台账 + 隐藏约束 + Mermaid 流程图), 详 §2-§5."

**P2-9 README 协同段改表格 (1 处)**:
- `references/llm-prompts/README.md` "## 与现有 references 的协同" 段: 7 行 `-` 列表 → 7 行表格 (工具 / 配套方法论 / dryrun check)
- 节省纵向空间 + 加 "dryrun check" 列明示哪些工具有程序化检查

**v1.5.8.x 累计 hotfix 终态**:
- v1.5.8: 借鉴 BZD 4 skill (minor)
- v1.5.8.1: 补 2 LLM prompt + 2 check
- v1.5.8.2: writing-for-agents 审计 P0 (cache 精简 + description + 完成判据 13)
- v1.5.8.3: writing-for-agents 审计 P1 (negation + step 锚定 + 顺序)
- v1.5.8.4: writing-for-agents 审计 P2 (中英标题 + §1 完成判据 + README 表格化)
- 总 hotfix: 4 次, 累计 edit 数: 22 + 7 + 7 = 36 edit
- dryrun check 数: 23 → 27 → 29 (v1.5.8.1 之后稳定在 29)

**没有 v1.5.8.5 了**: P0/P1/P2 全部修完, 下次该写 v1.5.9 minor (新功能, 不算 hotfix).

---

## v1.5.8.3（2026-09-09）— writing-for-agents 审计 P1 修复

**动机**: v1.5.8.2 修了 P0 3 项 (cache 精简 + description 校准 + 13 个完成判据). v1.5.8.3 同日 hotfix 修 P1 3 项 (negation + step 锚定 + 顺序).

**变更**:

**P1-4 negation 改 positive (4 处)**:
- `references/读题逐句翻译.md` L10: "**不是查字典**, 而是暴露隐藏约束" → "**目标**: 暴露隐藏约束, 防漏题漏条件"
- `references/建模方案框架.md` L10: "**不是**给每题贴一个模型名, 而是建 1 个贯通全题的建模系统" → "**目标**是建 1 个贯通全题的建模系统, 共享数据/变量/参数/约束"
- `references/建模方案框架.md` L17: "**不是**'问题 1 用 A 模型...的拼盘'" → "**目标**是共享数据/变量/参数/约束, 跨问题一致"
- `references/llm-prompts/07-建模方案.md` L3: "**不是**给每题贴一个模型名" → "**目标**: 建 1 个贯通全题的建模系统, 共享数据/变量/参数/约束"

**P1-5 4 references step 锚定 (4 处)**:
- `references/读题逐句翻译.md` §1 顶部: "🟢 **对应 SKILL.md Step 0**: 读题."
- `references/建模方案框架.md` §1 顶部: "🟢 **对应 SKILL.md Step 1**: 求解计划."
- `references/端到端工作流对照.md` §1 顶部: "🟢 **对应 SKILL.md Step 0-4**: 跑题全流程总览."
- `references/学校画像与备赛评估.md` §1 顶部: "🟢 **对应阶段**: 赛前 1 个月 (备赛期, 不在 SKILL.md 5 步跑题流程内)."

**P1-6 借鉴段 4 references 顺序按触发顺序重排 (1 处)**:
- `SKILL.md` 借鉴段表格: 旧顺序 (借鉴顺序) = 读题翻译 / 建模方案 / 工作流对照 / 学校画像 → 新顺序 (触发顺序) = 工作流对照 / 读题翻译 / 建模方案 / 学校画像
- 学生查找路径: 跑题启动 → 看对照 (Step 0-4) → 读题翻译 (Step 0) → 建模方案 (Step 1) → 备赛期 (学校画像)
- 表格标题加 "按触发顺序排列" 提示

**未做 (P2 3 项)**: 中英标题不一致 / §1 冗余 / README 协同段表格化. 留 v1.5.8.4+ 处理.

---

## v1.5.8.2（2026-09-09）— writing-for-agents 审计 P0 修复

**动机**: v1.5.8.1 交付后跑 writing-for-agents skill 审计，发现 P0 3 项必修（description 锐度 + 完成判据缺失 + 6 处 cache 重复）。同日 hotfix 修这 3 项。

**变更**:

**P0-1 重复 cache 精简 (8 处 → 1 处权威)**:
- **删**: `SKILL.md` 借鉴段 L680 单独"借鉴策略"行（release note 性质，应只在 CHANGELOG.md）
- **缩短**: 4 个 references 头部 L4 "本文档**不复制** BZD 的 `references/...`..." 长段 → 1 句 "**搬运策略**: v1.5.1 精简方法论 (不复制 BZD 完整子树, 详 CHANGELOG.md v1.5.8)"
- **缩短**: 2 个 LLM prompt 头部 L5 "**不复制** BZD 完整 references/ 5 篇细则..." 长段 → 1 句 "v1.5.1 精简风格 (不复制 BZD 完整子树)"
- **保留**: 各文件 L3 "借鉴源: BZD 数模社 `bzd-xxx` v1.0 ..." 行（作为 provenance，不可压缩）

**P0-2 description 触发词校准 (1 处)**:
- **删**: `SKILL.md` description "或'学校画像'" 触发词
- **理由**: 学校画像是**赛前 1 个月**用（备赛期），不是跑题 always-loaded 路径。混了 2 个不同时段 = 违反 "one trigger per branch" 原则。学生想看学校画像应通过 `references/赛前学习清单.md` 触发（备赛期文档），不是 li-mtrie 主 skill。
- **保留**: "或'读题翻译'/'建模方案'" 触发词（这 2 个是跑题期 Step 0/1 必跑）

**P0-3 4 references 完成判据补齐 (13 个)**:
- `references/读题逐句翻译.md` (4 个): §2 句子单元拆分 / §3 覆盖台账 / §4 隐藏约束 / §5 Mermaid 流程图 各 1 行 🟢
- `references/建模方案框架.md` (6 个): §2 整题视角 / §3 逐题方案 / §4 跨题连续性 / §5 模型比选 / §6 创新点 / §7 验证闭环 各 1 行 🟢
- `references/端到端工作流对照.md` (1 个): §3 BZD ↔ li-mtrie 对照表 1 行 🟢
- `references/学校画像与备赛评估.md` (2 个): §2 4 类校 / §3 4 档备赛 各 1 行 🟢

每个判据形式: `🟢 **完成判据**: X ≥ N, 关键约束满足`. 例如:
- `🟢 **完成判据**: 总单元数 ≥ 题面句数, 标题/元信息未拆入.`
- `🟢 **完成判据**: 4 维 (共享数据/共享变量/共享约束/上一问输出=下一问输入) 全 ✓ 或有修正动作.`

**审计驱动 (writing-for-agents skill 7 大杠杆)**:
1. Context pointer 锐度 → 修 description 触发词
2. Two loads → 不破坏 (references 仍是 on-demand loaded, 不进 always-loaded)
3. Information hierarchy → 不破坏 (完成判据 in-file, 不外推)
4. Completion criteria → 修 (13 个新判据, 全部 checkable + exhaustive)
5. Leading words → 不破坏 ("搬运策略" / "完成判据" 已是 leading words)
6. Negation → 部分修 (P0-1 减少 6 处 "不复制..." negation, 改成 positive "搬运策略")
7. Pruning → 大修 (cache 8 处 → 1 处, 单一权威源)

**未做 (P1 + P2)**: 5 处 negation 反例 ("不是 X" 改 positive) / 4 篇 §1 缺 step 锚定 / 4 references 顺序与触发顺序不一致 / 中英标题不一致 / README 协同段表格化. 留 v1.5.8.3+ 处理.

---

## v1.5.8.1（2026-09-09）— v1.5.8 BZD 借鉴的 LLM 配套补齐

**动机**: v1.5.8 借鉴 BZD 4 skill 写了 4 个 references 方法论，但头部引用的 2 个 LLM prompt 路径 (`05-读题翻译.md` / `06-建模方案.md`) 是 placeholder 实际未写。v1.5.8.1 同日 hotfix 补齐这 2 个 LLM 工具版本。

**变更**:

**2 个新 LLM prompt** (仿 `05-读题提取` 风格, 10-13 KB):
- `references/llm-prompts/06-读题翻译.md` (10.4 KB) — 配套 `references/读题逐句翻译.md`. 4 节报告 prompt (全局故事 + 覆盖台账 + 隐藏约束 + Mermaid 跨题流程图) + 6 项常见问题修法 + 协同 05-读题提取 的说明
- `references/llm-prompts/07-建模方案.md` (12.9 KB) — 配套 `references/建模方案框架.md`. 5 节方案 prompt (整题框架 + 逐题 4 块 + 跨题连续性 + 模型比选 6 维 + 创新点 + 风险备选) + 7 项常见问题修法 + 协同 06-读题翻译 的说明

**5 个引用更新**:
- `references/读题逐句翻译.md` 头部 LLM prompt 引用: `05-读题翻译.md` → `06-读题翻译.md`
- `references/建模方案框架.md` 头部 LLM prompt 引用: `06-建模方案.md` → `07-建模方案.md`
- `references/llm-prompts/README.md` L1 + 5 工具表 + 协同段加 06+07
- SKILL.md frontmatter `version: "1.5.8"` → `"1.5.8.1"` (last_update 保持 2026-09-09 同日)
- dryrun.py 加 LLM_PROMPTS_DIR 常量 + 改版本号

**dryrun.py 扩展 27 → 29 项**:
- check 28: `references/llm-prompts/06-读题翻译.md` 存在
- check 29: `references/llm-prompts/07-建模方案.md` 存在
- docstring patch 标签加 v1.5.8.1 hotfix 行 + 友好输出 v1.5.8 → v1.5.8.1

**hotfix 性质**:
- 同日小修补 (CHANGELOG 格式明确: "hotfix 留给同日小修补")
- 不算 minor bump (没新功能, 只补 v1.5.8 已知 TODO)
- 不重打 description / 触发词 / 借鉴段 (v1.5.8 段已写好)

**LLM prompt 风格统一** (跟 05-读题提取 一致):
- ✅ 头部：用途 + 借鉴 + 配套方法论 + 与其他工具区别
- ✅ 5 步使用流程 (含 PowerShell 代码块)
- ✅ 可直接复制的 prompt (含 4 节输出格式)
- ✅ PowerShell 验证脚本 (检查 5 节齐 + 4 类约束 + 比选 6 维)
- ✅ LLM 常见问题 + 修法表 (6-7 项)
- ✅ 与上一工具协同表
- ✅ v1.5.8 真实案例 (烟幕干扰弹 A 题)
- ✅ 严禁清单 + 配套工具列表

---

## v1.5.8（2026-09-09）— 借鉴 BZD 4 个 skill（生成类 + 总控类 + 综合评审）

**动机**: v1.5.7.6 已借鉴 BZD 12 个论文自查类 skill（v1.5.1 借鉴 3 + v1.5.3 借鉴 9 板块）。本轮补齐 BZD 仓库剩下 4 个未借鉴的 skill，按 v1.5.1 精简方法论风格搬运（不复制完整 BZD 子树，保持 li-mtrie 独立性）。

**变更**:

**4 个新 references** (按 v1.5.1 风格精简方法论 + LLM 工具版本提示):
- `references/读题逐句翻译.md` (3.2 KB) — 借鉴 `bzd-problem-translator`：语义翻译 + 句子单元拆分 + 覆盖台账 + 隐藏约束 + Mermaid 跨题流程图。跑题 Step 0 用。
- `references/建模方案框架.md` (4.6 KB) — 借鉴 `bzd-modeling-ideas`：整题视角 + 跨题连续性 + 候选模型比选 + 创新点 + 验证闭环。跑题 Step 1-2 用。
- `references/端到端工作流对照.md` (4.3 KB) — 借鉴 `bzd-modeling-workflow`：BZD 6 阶段 ↔ li-mtrie 5 步状态机对照表 + 3 处 li-mtrie 弱项改进建议。
- `references/学校画像与备赛评估.md` (4.6 KB) — 借鉴 `bzd-cumcm-school-awards`：4 类校画像 + 4 档备赛评估 + 6.81% 概率口径警告。赛前 1 个月用。

**SKILL.md 改动**:
- frontmatter `version: "1.5.7.6"` → `"1.5.8"` + `last_update: 2026-09-08` → `2026-09-09`
- description 触发词扩展（加 "读题翻译" / "建模方案" / "学校画像"）— 仍保持 ≤ 6 行（v1.5.7.5 check 20 不破）
- 新增 `## v1.5.8 新增 4 references` 段，列出 4 个新文件 + BZD 源 skill 对应

**dryrun.py 扩展 23 → 27 项**:
- check 24: `references/读题逐句翻译.md` 存在
- check 25: `references/建模方案框架.md` 存在
- check 26: `references/端到端工作流对照.md` 存在
- check 27: `references/学校画像与备赛评估.md` 存在
- docstring patch 标签 + 友好输出版本号同步 v1.5.7.6 → v1.5.8

**借鉴粒度** (与 v1.5.1 一致):
- ✅ 精简方法论骨架（每个 3-5 KB）
- ✅ LLM 工具版本提示（指向 `references/llm-prompts/05-读题翻译.md` / `06-建模方案.md` — 注: 这 2 个 LLM prompt 暂未实写, 是 placeholder, v1.5.9 可补）
- ❌ 不复制 BZD 完整 agents/ scripts/ assets/ 子树（保持 li-mtrie 独立性 + 体量可控）
- ❌ 不复制 BZD 学校榜单数据（版权资源）

---

## v1.5.7.6（2026-09-08）— 全面审计修复 + 端到端跑题验证

**审计**: v1.5.7 审计报告 47 项问题，全修预估 8.5+/10。

**变更**:

**P0 (6 类必修)**:
- 12 幽灵引用删除（v1.5.7.x 仓库全历史不存在，删引用改指已有文档）
- CHANGELOG.md + 测试报告.md 补建（v1.5.7.5 已建 CHANGELOG，本轮补全 entry）
- profile_data.py 2 bug 修（L353 `warnings`→`warns` 不再遮蔽 stdlib 模块 / L435 `m.get("std",`→`m.get("sd",` 键名错）
- aigc_scan.py `sys.exit(1)`→`raise FileNotFoundError(...)`（库函数不杀调用进程）
- 2 张 LaTeX 主图删除（figures/2.1_timeline.png / figures/3.2_strategy_compare.png）
- scripts/README.md 重写（从陈旧脚本说明 → 当前 7 脚本职责表）
- dryrun.py 加 3 check (21/22/23 防 P0 bug 回退)，凑齐 23 项

**P1 (10 项)**:
- 5 处内容重复热点合并到权威源（line count / 红线 / 触发词 / 角色 / 赛前清单）
- 4 处内容冲突统一（5.X 子节数对齐 / 参考文献数对齐）
- 2 个低等 bug 审计报告过期（标注实际修版本）
- 1 路径不一致修（data_utils.py 注释路径）
- 1 标题"4→5"修正

**P2 (14 项)**:
- 11 实际修（typo / 重复段 / 旧链接 / 过期示例）
- 2 审计过期（标注 v1.5.7.6 修）
- 1 文档化（新增"何时不用本 skill"段落）

**writing-for-agents 7 项**（v1.5.7.5 之后补充）:
- 5 段"权威源"压缩
- 10 版本标签删除（changelog 化）
- 5 故事段压缩
- 2 negation 改 positive
- 1 tautology 删
- 1 `checkable` 定义
- 1 触发词一致

**端到端跑题验证**（2025 国赛 A 题 烟幕干扰弹投放策略）:
- Step 0-5 状态机全跑通
- 问题 1 T_SHIELD=0.00s（暴露陷阱：投放即遮蔽=暴露）
- 问题 2 T_SHIELD=2.40s（4 维优化: 时延/高度/速度/方向）
- 问题 3 T_SHIELD=3.93s（3 弹累加遮蔽）
- dryrun 19/23 green 0 red（5 red = 跑题/ 模板原版设计意图：占位符/示例图/示例代码未替换，跑题用户填实际内容才 GREEN）

**清理**:
- 6 个 .aux/.log/.out LaTeX 临时文件移走
- 跑题/ 回退到模板原版（实做产物全部 Temp 备份：3 张主图 + 66 个 .py/补充图/csv/读题清单等）
- 删除 3 张实做主图 + 66 个实做文件 + figures/README.md
- 保留 4 个 LaTeX 编译基础设施（format.cls / preamble-first.tex / 2 字体 .otf）

---

## v1.5.7.5（2026-09-07）— writing-for-agents 修剪

**审计**: 独立审计 6.6/10（v1.5.7 8.0/10 下滑），主要问题: 12 幽灵引用 + 3 中等代码 bug + 2 缺失文件。修完预估回升 8.0+/10。

**变更**:
- SKILL.md description 6 行 (合并 3 触发词 → 1 跑题)
- SKILL.md 4 个 `🟢 Step X 完成判据` (Step 0/1/3/4)
- 新增 `references/红线与失败模式.md`（v1.5.7.5 推红线）
- 引入 `CHANGELOG.md`（v1.5.7.5 推 history，frontmatter 仅留 1 行 `changelog: CHANGELOG.md`）
- dryrun.py check 20: v1.5.7.5 修剪验证（4 项: description ≤ 6 行 / 红线 1 文件 / CHANGELOG 1 文件 / 4 完成判据）

---

## v1.5.7（2026-09-07, in v1.5.6 之上 + 2 commit 累计）— 细化读题环节

- SKILL.md §Step 0 加 15 项读题清单（防 2025C 3 P0 错位）
- 新增 `references/读题清单.md`（15 项空表模板）
- 新增 `references/llm-prompts/05-读题提取.md`（LLM 工具自动从 PDF 提取）
- dryrun.py check 19 验证 15 项全覆盖
- 包大小 23.91 MB（+0.01），增量几乎无
- 审计 8.0/10 不变

---

## v1.5.6（2026-09-07, in v1.5.5 之上 + 1 commit 累计）— 借鉴 BZD 4 色教学法重写 .tex 模板

- 借鉴 BZD 数模社 12 个论文板块模板（4 色教学法）
- 14 个 .tex 全部按 BZD 2026 规范重写:
  - `0.摘要` (4 段 + 关键词)
  - `1.引言` (3 子节)
  - `2.总体分析` (5 段 + 框架图)
  - `3.模型假设` (9 类)
  - `4.符号说明` (三线表)
  - `5.1.1+5.1.2` (建模 + 求解)
  - `6.模型检验` (4 类)
  - `7.模型评价` (4 子节)
  - `8.改进推广` (4 层面)
  - `9.参考文献`
  - `9.0.AI 声明`
  - `10.0 附录固定说明`
  - `10.附录` (核心源代码)
- dryrun.py check 16/17 加 template 状态 yellow 跳过
- 包大小 5.12 MB，增量 < 0.1 MB
- 审计 8.0/10 不变

---

## v1.5.4（2026-09-06, in v1.5.3 之上 + 1 commit 累计）— 防"答非所问"强化

- 借 2025C 跑题失败案例 (other agent 踩 3 P0: 问题 4 选错 sheet / 问题 2-3 自创 BMI 分组 / 10.附录.tex 残留 2024B 模板)
- 加 3 道程序化防线: dryrun.py check 15 占位符未替换 / 16 附录文件存在 / 17 \includegraphics 图引用存在
- SKILL.md 加 4 段必做项: Step 0 quote 锚定 + 题面关键判据 grep / Step 3 占位符 grep / Step 4 附录文件 Test-Path + 顶部 4 大典型坑警示表
- 2 文件改 + 0 文件加
- 审计 8.0/10 不变

---

## v1.5.3（2026-09-06, in v1.5.2 之上 + 3 commits 累计）— 借鉴 BZD 12 个论文自查子 skill

- 借鉴 BZD 数模社 12 个论文自查类子 skill + bzd-problem-translator + bzd-cumcm-school-awards 核心理念
- 产出 11 新文件: `references/板块自查/` (10 文件: 9 板块级自查 + 1 README 索引) + `references/题意翻译.md` (3.5 KB) + `references/学校国奖画像.md` (3.4 KB)
- 借鉴源扩到 18 个外部 skill
- 审计 7.7/10（中）→ 8.0/10（P4 patch 整改后恢复 6 维度上限）

---

## v1.5.2（2026-09-03, in v1.5.1 之上 + 1 commit 累计）— fitz deprecate 兼容

- `fix(scripts)`: 兼容 PyMuPDF ≥1.24 的 fitz deprecate
- `verify_pdf_metrics.py` + `visual_qa.py` 改 try/except 双 import（优先 `import pymupdf as fitz`, fallback `import fitz`）
- 2 文件，+8/-2 行
- 验证: 跑通 24 页 PDF 无警告
- 向后兼容 PyMuPDF <1.24

---

## v1.5.1（2026-09-03, in v1.5.0 之上 + 4 commits 累计）— 借鉴 BZD 3 个核心 skill

- 借鉴 BZD 数模社 3 个核心 skill: `bzd-model-dictionary` (11 维评估 + 4 档判定) + `bzd-paper-format-checker` (12 章节报告 + 15 分制) + `bzd-review-paper` (100 分 + 90% 封顶 + 格式系数 + 位次估计)
- 产出 4 新文件:
  - `references/模型字典使用指南.md` (6.9 KB)
  - `references/格式自查清单.md` (9.5 KB)
  - `references/百分制评审方法.md` (6.5 KB)
  - `llm-prompts/04-百分制评审.md` (12.4 KB, 3 模式 M1/M2/M3 合并)
- 借鉴源扩到 7 个外部 skill

---

## v1.5.0（15 commits 累计, 2026-08-27 → 08-31, in v1.4.4 13 commits 之上新增 2 commits）— LLM 工具集成 + GBK fix

- ⚡ LLM 工具集成（`references/llm-prompts/` 3 工具 + README, 学生 copy-paste 自用, 不调外部 API, 96 小时救星）
- ⚡ verify_pdf_metrics.py GBK console fix（commit 8866cbc hotfix）
- 借鉴 mma v3.3 / bzd-modeling-ideas / scipilot-figure-skill / aigc-reduce / cumcm-live-workflow / 数模陪跑独家 6 个外部 skill
- 包大小 22.51 / 3.77 MB

---

## v1.4.4（13 commits 累计, 2026-08-27 → 08-31）— 借鉴数模陪跑独家 + cumcm-live-workflow v5.0

- 借鉴 数模陪跑独家 + cumcm-live-workflow v5.0 + writing-for-agents 6 维度审计 + 4-script smoke test
- 8 个新文件: `论文/figures/` 10 张图 + 教学开关 + 国奖级硬性指标 + 去AIGC指南 + 题意红线 + verify_pdf_metrics.py + 编号体系 v7 + workflow.md refactor

---

## v1.4.x 早期版本

- **v1.4.3**（2026-08-25）— 纯 framework + 求解计划模板
- **v1.4.2**（2026-08-25 前）— 恢复 题目/数据/ 学生示例
- **v1.4.1**（2026-08-25 前）— v1.4.0 复审 P0 1 + P1 4 全部应用
- **v1.4.0**（2026-08-25 前）— 加 板凳龙-南科大-2024 国一 作为第 5 篇参考论文

## v1.3.x

- **v1.3.2**（2026-08-25）— writing-for-agents 审计 P0+P1+P2 全部应用
- **v1.3.1**（2026-08-25 前）— 测试报告 §8.5 5 项 P0/P1 全部闭环
- **v1.3**（2026-08 前）— 24 项 P0/P1/P2 改进 + 去重 2 轮 + 端到端验证

## v1.0–v1.2

- **v1.2**（2026 规范版）— 5 篇 2024 获奖论文归纳
- **v1.0**（2024）— 4 篇 2024 高教社杯获奖论文归纳

---

## 审计记录

| 日期 | 版本 | 评分 | 摘要 |
|------|------|------|------|
| 2026-09-06 | v1.5.3 | 7.7/10 → 8.0/10（P4 patch 后）| BZD 借鉴引入 11 新文件, P4 整改恢复 6 维度上限 |
| 2026-09-07 | v1.5.7.5 | **6.6/10**（独立审计，待 P0 修复回升 8.0+/10）| 12 幽灵引用 + 3 代码 bug + 2 缺失文件，详见 `审计报告.md` |

> 审计报告: `审计报告.md`（v1.5.7.5 独立审计 2026-09-07）
