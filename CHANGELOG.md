# CHANGELOG (v1.5.8.4 — 支撑材料超限预案 L24 (P0-5 防御) + 验收清单 G 段)

## v1.5.8.4 — 支撑材料超限预案 check 57 + Step 4.4 段 + 验收清单 G 段 (2026A 复盘 v1.1 §P0-5 防御)

**核心**: 2026A 实跑复盘 v1.1 §P0-5 — result2.xlsx 达 35→36MB, 单文件即超 20MB 包限. 方案: gzip CSV (两 sheet 约 5.6MB) + 包内说明 + 脚本一键重生. v1.5.8.4 加 1 项 auto check + SKILL.md §Step 4.4 新段 + 验收清单 G 段 5 项.

**改 `references/scripts/dryrun.py`** (+75 行, 1 个新 check 函数):

- **check 57 (支撑材料超限 L24, auto)**: 扫用户跑题根的 `支撑材料/` 目录, 找 >10MB 单文件 + 总 >20MB. 判断:
  - >10MB 单文件 + 总 >20MB → **red** (P0-5 翻车, 2026A result2 36MB)
  - >10MB 单文件但未配套 csv.gz/npz → **red** (触发预案第一步)
  - 大文件已配套 csv.gz/npz → **yellow** (提示同步附录 A/D/J 引用)
  - 全部 <10MB → **green**
  - 支撑材料/ 不存在 → **yellow** (跑前 skip)
- 检测大文件是否有 `.csv.gz` / `.npz` / `.xlsx.gz` 配套压缩

**改 `references/audit/验收清单.md`** (+30 行, §G 支撑材料包):

- **G1**: 支撑材料/ 任一文件 ≤ 10MB (P0-5 硬约束)
- **G2**: 支撑材料/ 总包 ≤ 20MB (竞赛硬规则)
- **G3**: 大文件已配套 csv.gz / npz 压缩 (P0-5 改进)
- **G4**: 附录 A/D/J 列表与包内文件一致 (P0-6 联动)
- **G5**: 重跑后 csv.gz 已重新生成 (P0-7 联动, 防"打包忘重生")
- 完整 PowerShell 预案命令 (4 步) + 2026A 踩坑案例

**改 SKILL.md** (1486 → 1487, +1 行):

- §Step 4.4 打包支撑材料 +1 段 (超限预案 3 步 + check 57 引用 + 实证 + G 段指针)
- §5 道防线速查表段补 "v1.5.8.4 加 check 57 (L24) 扫 支撑材料/ 找 >10MB 单文件 + 总包 >20MB"

**改 `references/audit/auto-check-list.md`** (+9 行, §支撑材料超限预案节):

- **§L24 段**: check 57 描述 + 3 步预案 + 阈值

**改 `references/audit/post-solution-audit-list.md`** (16 层表 +1 行 L24):

- **L24**: 支撑材料超限预案, auto, dryrun 5 min

**影响文件**:

- 改 `references/scripts/dryrun.py` (+75 行: check_support_overlimit + CHECKS 1 行)
- 改 `references/audit/验收清单.md` (+30 行: §G 段 5 项 + PowerShell 预案)
- 改 `references/audit/auto-check-list.md` (+9 行: §L24 段)
- 改 `references/audit/post-solution-audit-list.md` (+1 行: L24)
- 改 SKILL.md (+1 行)
- 改 CHANGELOG.md (主文件更新标题 + v1.5.8.4 entry)

**dryrun**: 32/53 → 32/54 green + 21→22 yellow + 0 red (待 commit 后跑实数) → **目标 33/54 green + 21 yellow + 0 red**.

**v1.5.8.4 后续方向**:

- v1.5.8.5 P0-6 (附录 ↔ 压缩包内容一致性, check 58): 解压支撑材料包 + 验证附录 \texttt{路径} 真实存在 + 表号引用一致
- v1.5.8.6 P0-7 (重跑影响面清单, SKILL.md Step 4 新清单 + 验收清单新节)
- v1.5.8.7 P0-8 (含反斜杠内容批量改写, SKILL.md 工具规范段 + pack 规则)
- v1.5.9 P1 8 项 (评阅对齐 / 绘图双标题 / fig_sanity / 文献流程 / 移动边界反证 / 耗时落盘 / 表格组表头 / 跨文档一致)
- v1.6.0 P2 9 项 (Python 探测 / GBK reconfigure / heredoc 反斜杠 / 波浪号中文 / 模板 4 问化 / pack 忽略 / Read 尺寸校验 / Overfull 案例 / rename 列名)

---



## v1.5.8.3 — resultX 结构 vs 附件3 模板 check 56 + 读题清单 §10 细化 (2026A 复盘 v1.1 §P0-4 防御)

**核心**: 2026A 实跑复盘 v1.1 §P0-4 — 4 个 result 的 A 列名写成 `时间` (模板为 `时间\到药材中心的距离`); result4 多插"半径/cm"列导致距离列右移且为字符串列名; 论文表5 用了 0.1cm 21 列 (题面要求 0.5cm 5 列). 均为提交前审计才发现. v1.5.8.3 加 1 项 auto check + 读题清单第 10 项细化 (论文表步长 vs result 完整序列步长分别登记).

**改 `references/scripts/dryrun.py`** (+110 行, 1 个新 check 函数):

- **check 56 (resultX 结构 vs 附件3 模板 L23, auto)**: 用 openpyxl 打开附件3 模板 (`数据/附件/附件3/*.xlsx`) + 产出 `求解/**/result*.xlsx`, 逐项比对 4 维度:
  1. **sheet 名集合**: result 应包含模板所有 sheet 名
  2. **A 列名精确匹配**: 模板 `时间\到药材中心的距离` vs result `时间` → red
  3. **距离列 dtype 数值**: 不能是字符串 (e.g. `r/cm` 列误为 str)
  4. **result4 末列 = "药材表面"**: 题面要求, 不能漏
- 阈值: 列名不匹配 red / dtype 错 red / 找不到附件3 模板 yellow / resultX 不存在 yellow

**改 `references/read-checklist/读题清单.md`** (+30 行, §10 输出形式细化):

- **§10.1 论文表步长**: 报给评委的最终输出 (e.g. 0.5cm 5 行) — dryrun check 19 + 56
- **§10.2 result 完整序列步长**: 保存到 resultX 的全部数据 (e.g. dt=60s, t=0 到 205906s ≈ 3433 行)
- **§10.3 resultX 列名严格按附件3 模板**: A 列必须写 `时间\到药材中心的距离`, 不能简写 `时间` 或 `t` — dryrun check 56 openpyxl 逐列比对

**改 SKILL.md** (1486 → 1487, +1 行):

- §5 道防线速查表段补 "v1.5.8.3 加 check 56 (L23) 用 openpyxl 逐列比对附件3 模板 vs resultX"

**改 `references/audit/auto-check-list.md`** (+11 行, §resultX 结构 vs 附件3 模板节):

- **§L23 段**: check 56 描述 + 4 维度比对 + 论文表步长 vs result 完整序列步长

**改 `references/audit/post-solution-audit-list.md`** (16 层表 +1 行 L23):

- **L23**: resultX 结构 vs 附件3 模板, auto + manual 读题清单 §10, dryrun 5 min

**影响文件**:

- 改 `references/scripts/dryrun.py` (+110 行: check_result_struct + CHECKS 1 行)
- 改 `references/read-checklist/读题清单.md` (+30 行: §10 三段细化)
- 改 `references/audit/auto-check-list.md` (+11 行: §L23 段)
- 改 `references/audit/post-solution-audit-list.md` (+1 行: L23)
- 改 SKILL.md (+1 行)
- 改 CHANGELOG.md (主文件更新标题 + v1.5.8.3 entry)

**dryrun**: 32/52 → 32/53 green + 20→21 yellow + 0 red (待 v1.5.8.3 commit 后跑实数) → **目标 33/53 green + 20 yellow + 0 red**.

**v1.5.8.3 后续方向** (Sep 28 改进意见 25 项, 留位):

- **v1.5.8 剩余 P0** (P0-5 支撑材料超限 / P0-6 附录一致性 / P0-7 重跑影响面 / P0-8 反斜杠批量改写) 等用户确认
- **v1.5.9 P1 8 项** (评阅对齐 / 绘图双标题 / fig_sanity / 文献流程 / 移动边界反证 / 耗时落盘 / 表格组表头 / 跨文档一致) 等用户确认
- **v1.6.0 P2 9 项** (Python 探测 / GBK reconfigure / heredoc 反斜杠 / 波浪号中文 / 模板 4 问化 / pack 忽略 / Read 尺寸校验 / Overfull 案例 / rename 列名) 等用户确认

---



## v1.5.8.2 — 论文数字三来源 check 55 + §红线 7 + 数值台账 (2026A 复盘 v1.1 §0 P0-3 防御)

**核心**: 2026A 实跑复盘 v1.1 §0 P0-3 — 5.2.2 节 ρ/cp/k 起止值系**目视读图臆造** (实 976.4→667.3 等); 5.4.1"前 10h→1.424cm、占 78%"**同为目测错** (实 5h、71.8%); **本轮新增**: 连"手算的关键判据"也会错 — `Bi_m` 被算成 32 (实 3.24, 差 10 倍), 决定性证据: 评审找代理公式复算时全部暴露, 评"模型不严谨" 0 分. v1.5.8.2 加 1 项 auto check + §红线 7 + 2 个新文件 (数值台账规范 + number_ledger 脚本).

**改 `references/scripts/dryrun.py`** (+95 行, 1 个新 check 函数):

- **check 55 (关键判据来源标记 L22, auto)**: 扫论文 11 章节 .tex, 找 5 类关键判据 (Bi / Fo / 收缩率 / Re / Pr) 出现位置, 检测紧邻 100 字符内是否含可信来源标记 (`实算/print/resultX.xlsx/solver 算/公式/\\begin{equation/align/台账/solve_*.py/代码/由.*计算/根据.*公式/代入.*得`). 判断:
  - 关键判据 + 含来源 → **green** (P0-3 防御)
  - 关键判据 + 无来源 → **yellow** (P0-3 警告, 提示补公式 + 二次复算)
  - 找不到关键判据 → **yellow** (非机理题, 跳过)

**新建 `references/audit/数值台账规范.md`** (4.6 KB, 6 节, P0-3 权威源):

- **§1 三来源约束**: 论文数字只准 3 类 (1=脚本 print 落盘 / 2=resultX.xlsx 程序读 / 3=公式现场算 + 关键判据二次复算)
- **§2 数值台账.csv 4 列结构**: 符号 / 值 / 来源 / 生成脚本. Step 3 起手必建
- **§3 4 道防线时序**: Step 3 起手 init / 每章写完 add / Step 4.3 check / Step 4.5 dryrun
- **§4 反例对照**: 5.2.2 ρ/cp/k + 5.4.1 收缩率 + Bi_m=32 三个反例 (vs 正确做法)
- **§5 dryrun check 55 协同**: 关键判据 + 来源标记 → green
- **§6 引用**: 跨 4 文件协同

**新建 `references/scripts/number_ledger.py`** (8.3 KB, 4 子命令 init/add/check/show):

- **init**: 建空台账 + 扫描现有 result*.xlsx 提数字 (限 3 result × 2 sheet × 5 行 × 5 列 = 150 数字)
- **add**: 单条添加 (--sym, --val, --source, --script, 来源必须 1/2/3)
- **check**: 扫论文 .tex, 提所有数字, vs 台账匹配率, 匹配率 < 70% return 1 (红)
- **show**: 打印台账

**改 `references/read-checklist/题意红线.md`** (+50 行, §红线 7):

- **§红线 7 (Step 3 必做)**: 论文数字三来源红线 + 数值台账
  - **3 类可信来源**: 1=solver print / 2=resultX.xlsx / 3=公式现场算
  - **3 类禁止**: 凭图读数 / 一次性心算 / AI 写数字
  - **数值台账 4 列结构**: 符号/值/来源/生成脚本
  - **4 道防线时序**: Step 3 起手/每章/Step 4.3/Step 4.5
  - 2026A 反例: 5.2.2 ρ/cp/k + 5.4.1 收缩率 + Bi_m=32 三个 P0 翻车

**改 SKILL.md** (1476 → 1478, +2 行):

- §Step 3 +1 段 (数字三来源红线 + 数值台账 4 列 + 3 禁止 + 2026A 3 反例 + 4 道防线 + check 55)
- §5 道防线速查表段补"v1.5.8.2 加 check 55 (L22)"

**改 `references/audit/auto-check-list.md`** (+12 行, §关键判据数字三来源节):

- **§L22 段**: check 55 描述 + 3 类可信来源列表 + 3 类禁止 + 配套工具 (数值台账 + number_ledger.py + 规范)

**改 `references/audit/post-solution-audit-list.md`** (16 层表 +1 行 L22):

- **L22**: 关键判据数字三来源, auto + manual 数值台账, dryrun + number_ledger.py check (15 min)

**影响文件**:

- 改 `references/scripts/dryrun.py` (+95 行: check_number_source + CHECKS 1 行)
- **新建** `references/audit/数值台账规范.md` (4.6 KB, 6 节权威源)
- **新建** `references/scripts/number_ledger.py` (8.3 KB, 4 子命令)
- 改 `references/read-checklist/题意红线.md` (+50 行: §红线 7)
- 改 `references/audit/auto-check-list.md` (+12 行: §L22 段)
- 改 `references/audit/post-solution-audit-list.md` (+1 行: L22)
- 改 SKILL.md (+2 行)
- 改 CHANGELOG.md (主文件更新标题 + v1.5.8.2 entry)

**dryrun**: 32/51 → 32/52 green + 19→20 yellow + 0 red (待 v1.5.8.2 commit 后跑实数) → **目标 33/52 green + 19 yellow + 0 red**.

**v1.5.8.2 后续方向** (Sep 28 改进意见 25 项, 留位):

- **v1.5.8 剩余 P0** (P0-4 check_struct / P0-5 支撑材料超限 / P0-6 附录一致性 / P0-7 重跑影响面 / P0-8 反斜杠批量改写) 等用户确认
- **v1.5.9 P1 8 项** (评阅对齐 / 绘图双标题 / fig_sanity / 文献流程 / 移动边界反证 / 耗时落盘 / 表格组表头 / 跨文档一致) 等用户确认
- **v1.6.0 P2 9 项** (Python 探测 / GBK reconfigure / heredoc 反斜杠 / 波浪号中文 / 模板 4 问化 / pack 忽略 / Read 尺寸校验 / Overfull 案例 / rename 列名) 等用户确认

---



## v1.5.8.1 — 趋势数据 IQR 误用 check 54 + §红线 6 + 数据清洗规范 (2026A 复盘 v1.1 §0 P0-2 防御)

**核心**: 2026A 实跑复盘 v1.1 §0 P0-2 — 首版清洗用 `IQR(k=3) = Q3 + 3×IQR / Q1 - 3×IQR` 把附件 1 升温段 (27 行) + 附件 2 收缩段 (23 行) 全部判异常, **边界条件被腰斩**. 趋势数据的四分位距天然覆盖不了分布尾部的"过程段", IQR 不适用于过程段检测. v1.5.8.1 加 1 项 auto check + §红线 6 + 新建数据清洗规范文件.

**改 `references/scripts/dryrun.py`** (+110 行, 1 个新 check 函数):

- **check 54 (IQR/boxplot + 紧邻 drop L21, auto)**: 启发式扫 `求解/问题N/*.py`, 找 5 个常见 IQR/boxplot/quantile 命名/调用:
  - 紧邻 `drop/dropna/删除/剔除/outlier` (10 行窗口) → **red** (P0-2 反例, 趋势段被全删)
  - 纯描述统计 (describe / quantile 用于报告) → **green**
  - 找不到 IQR/boxplot → **yellow** (非数据清洗题, 跳过)
- 跳过 `__init__` / 共享 utils / 绘图脚本 (含 `plot/绘图/figure` 路径, boxplot 用于画图不剔除)

**新建 `references/data-usage/数据清洗规范.md`** (6.4 KB, 7 节, P0-2 权威源):

- **§1 总纲**: 趋势数据禁用全局 IQR/箱线判据. 二阶差分"速率阶段变化"是物理现象, 不是测量错误
- **§2 4 类允许检测方法**:
  1. **物理越界**: `T ∈ [T_min, T_max]`, `C > 0`, `R ∈ (0, R₀]`, `X ∈ [0, 1]`
  2. **一阶差分突变**: z-score > 5 (远比 IQR 的 1.5 严格)
  3. **物理单调性 (带容差 ε=1e-6)**: 收缩曲线 R 不增, 升温曲线 T 不降
  4. **时间间隔一致性 + 重复值**: Δt 偏差 > 5% 提示时间戳错乱
- **§3 边界/驱动类数据默认保留全量**: 附件 M 的 R(t) / 预报曲线 / 滚动预测是**驱动**数据, 删 1 行 = 改 1 个边界时刻
- **§4 二阶差分"速率阶段变化"是物理现象**: 升温曲线常分阶段 (表面水 → 自由水 → 结合水), d²T/dt² 突变是阶段切换
- **§5 与 v1.5.8 §红线 5 协同**: 输入侧 P0-2 (清洗错) + 输出侧 P0-1 (离散式错) = 机理题"数据-模型"双防
- **§6 dryrun check 54 (L21) 协同**: 启发式扫源码 IQR + drop
- **§7 引用**: 跨 4 文件协同

**改 `references/read-checklist/题意红线.md`** (+50 行, §红线 6):

- **§红线 6 (数据清洗维度通用)**: 趋势数据禁用全局 IQR/箱线判据
  - 4 类允许检测方法 (物理越界 / 一阶差分 z>5 / 单调性含容差 / 时间间隔+重复)
  - 边界/驱动类数据默认保留全量
  - 二阶差分"速率阶段变化"是物理现象
  - 与 v1.5.8 §红线 5 协同: 输入侧 (P0-2) + 输出侧 (P0-1) = 双防

**改 `references/by-category/数据分析类典型反模式.md`** (+2 行, §1 反模式表 #11):

- **#11 趋势数据 IQR 误删**: 单调趋势段被全删, 改 4 类允许检测. 2026A P0-2 反例: 升温 27 行 + 收缩 23 行被 IQR(k=3) 全删. dryrun check 54 (L21)

**改 `references/by-category/物理机理类典型反模式.md`** (+2 行, §1 反模式表 #11):

- **#11 升温/收缩曲线 IQR 误删 (输入侧 P0)**: 跟 #9 (输出侧 P0-1) 协同: 输入+输出双防

**改 `references/audit/auto-check-list.md`** (+13 行, §数据清洗 IQR 误用节):

- **§L21 段**: check 54 描述 + 4 类允许检测列表 + 阈值

**改 `references/audit/post-solution-audit-list.md`** (16 层表 +1 行 L21):

- **L21**: 趋势数据 IQR 误用, auto (check 54), dryrun 5 min

**改 SKILL.md** (1474 → 1476, +2 行):

- §Step 0 数据节 +1 段 (引用数据清洗规范.md + §红线 6 + check 54)
- §5 道防线速查表段补"数据清洗 v1.5.8.1 加 check 54 (L21)"

**影响文件**:

- 改 `references/scripts/dryrun.py` (+110 行: check_iqr_outlier + CHECKS 1 行)
- **新建** `references/data-usage/数据清洗规范.md` (6.4 KB, 7 节权威源)
- 改 `references/read-checklist/题意红线.md` (+50 行: §红线 6)
- 改 `references/by-category/数据分析类典型反模式.md` (+2 行: 反模式 #11)
- 改 `references/by-category/物理机理类典型反模式.md` (+2 行: 反模式 #11)
- 改 `references/audit/auto-check-list.md` (+13 行: §L21 段)
- 改 `references/audit/post-solution-audit-list.md` (+1 行: L21)
- 改 SKILL.md (+2 行)
- 改 CHANGELOG.md (主文件更新标题 + v1.5.8.1 entry)

**dryrun**: 32/50 → 32/51 green + 18→19 yellow + 0 red (待 v1.5.8.1 commit 后跑实数) → **目标 33/51 green + 18 yellow + 0 red**.

**v1.5.8.1 后续方向** (Sep 28 改进意见 25 项, 留位):

- **v1.5.8 剩余 P0** (P0-3 数字三来源 / P0-4 check_struct / P0-5 支撑材料超限 / P0-6 附录一致性 / P0-7 重跑影响面 / P0-8 反斜杠批量改写) 等用户确认
- **v1.5.9 P1 8 项** (评阅对齐 / 绘图双标题 / fig_sanity / 文献流程 / 移动边界反证 / 耗时落盘 / 表格组表头 / 跨文档一致) 等用户确认
- **v1.6.0 P2 9 项** (Python 探测 / GBK reconfigure / heredoc 反斜杠 / 波浪号中文 / 模板 4 问化 / pack 忽略 / Read 尺寸校验 / Overfull 案例 / rename 列名) 等用户确认

---

## v1.5.8 — FVM Robin 边界离散式 check 53 + §红线 5 (2026A 复盘 v1.1 §2.1 P0-1 防御)

**核心**: 2026A 实跑复盘 v1.1 §2.1 P0-1 (v15 终审) — 温度场 `build_surface_row()` 返回 `(1.0, 1+β, β)`, β = h·Δr/α ≈ 29611 且**式中无 Δt**, 表面钉死在烘房温度 (h→∞ 极限, 不是题面 h=25). 决定性证据: 正确格式 `dE/dt ÷ [h(T∞−T_s)A] ≈ 0.995`, 错格式 = 223 (不可能). 水分场叠加错: 错离散式 + 错算 Bi_m = 32 (实 3.24) + 改用 Dirichlet 三层错误. v1.5.8 加 1 项 auto check + §红线 5 + 物理机理类 #9/#10 反模式, 静态扫 `求解/问题N/solve_*.py` bc_row 函数.

**改 `references/scripts/dryrun.py`** (+140 行, 1 个新 check 函数):

- **check 53 (FVM Robin 边界离散式 L20, auto)**: 启发式扫 `求解/问题N/*.py`, 找 6 个常见命名 (`build_surface_row` / `bc_row` / `surface_row` / `build_bc` / `compute_bc` / `boundary_row`) 函数. 检测:
  - 错模式 `\((1, 1+β, β)\)` (β = h·Δr/D, 无 Δt) → **red** (P0-1 反例, 表面 h→∞ 钉死)
  - 真 Robin 含 `2μ + γ` 三元组 `(1+2μ+γ, -2μ, γ)` 或显式 `gamma = 2*h_eff*dt/dr` → **green**
  - 找不到 bc_row 函数 → **yellow** (非 FVM 物理机理题, e.g. 优化/数据分析/常微分)
- 跳过 `__init__` / 共享 utils / `_` 开头

**改 `references/read-checklist/题意红线.md`** (+67 行, §红线 5):

- **§红线 5 (物理机理类必读)**: 边界离散式两道校验 + 半控制体 FVM Robin 模板
  - **校验 1**: 能量/质量守恒校验 `dE/dt ÷ [h(T∞−T_s)A]`, \|比值 − 1\| < 0.05 绿
  - **校验 2**: 独立换实现重算 (FVM → 解析极限/FDM/FEniCS), 同一特征量对比 相对误差 < 1% 绿
  - **正确模板**: `(1+2μ+γ)·U[N-1] − 2μ·U[N-2] = U_old + γ·U_amb`, μ = D_eff·Δt/Δr², γ = 2·h_eff·Δt/Δr (Biot 含 Δt, 不同于经典 Bi = h·Δr/D)
  - **3 类错模式 vs 2 类对模式对照表**: 错 1 `(1, 1+β, β)` β=h·Δr/D 无 Δt = h→∞ / 错 2 项错位传热方向反 / 错 3 β 无 Δt 维数不一致 / 对 1 显式半控制体 Robin / 对 2 Crank-Nicolson 时间中心
  - **适用题**: 物理机理类 (本科 A/生物/传染病/扩散/传热/动边界), 含 2026A 热-质耦合干燥

**改 `references/by-category/物理机理类典型反模式.md`** (+5 行, §1 反模式表 #9/#10 + §3 期望对照两行):

- **#9 Robin 边界离散式错**: `(1, 1+β, β)` 形式 → 表面钉死, 改用真 Robin 模板. dryrun check 53 自动扫
- **#10 求解后不换实现独立验算**: 跑完仅一套 FVM 不换方法 → 红. 守恒比值 + 独立换实现 2 道校验
- **§3 跑完后对照 2 行**: Robin 边界能量守恒 \|比值 − 1\| < 0.05 / 独立换实现 相对误差 < 1%

**改 `references/audit/auto-check-list.md`** (+13 行, §FVM Robin 边界离散式节):

- **§L20 段**: check 53 描述 + 真模板代码块 (μ, γ 公式) + 跳到 §红线 5 完整反例对照表

**改 `references/audit/post-solution-audit-list.md`** (16 层表 +1 行 L20):

- **L20**: FVM Robin 边界离散式, auto (check 53) + manual 两道校验, dryrun 10 min

**改 SKILL.md** (1475 → 1477, +2 行):

- §Step 0 类目适配 物理机理类 ⭐ 行补 "v1.5.8 反模式 #9/#10"
- §5 道防线速查表段补 "物理机理类 check 53 (L20) 自动扫 bc_row, 抓 Robin 边界 P0"

**干系人协同 (新条目 §红线 5 引用)**:

- `references/read-checklist/题意红线.md §红线 5` 加 1 段 "跟 li-mtrie 协同" 跨 3 文件
- `references/by-category/物理机理类典型反模式.md §5 引用` 加 v1.5.8 链接 (待 v1.5.8 hotfix 合并后)

**影响文件**:

- 改 `references/scripts/dryrun.py` (+140 行: check_bc_robin_template + CHECKS 1 行)
- 改 `references/read-checklist/题意红线.md` (+67 行: §红线 5)
- 改 `references/by-category/物理机理类典型反模式.md` (+5 行: 反模式 #9/#10)
- 改 `references/audit/auto-check-list.md` (+13 行: §L20 节)
- 改 `references/audit/post-solution-audit-list.md` (+1 行: L20)
- 改 SKILL.md (+2 行)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 32/49 + 17 yellow + 0 red (待 v1.5.8 commit 后跑实数) → **目标 33/50 green + 17 yellow + 0 red**.

**v1.5.8 后续方向** (Sep 28 改进意见 25 项中, 留位):

- **v1.5.8 剩余 P0** (P0-2 IQR 禁用 / P0-3 数字三来源 / P0-4 check_struct) 等用户确认
- **v1.5.9 P1 8 项** (评阅对齐 / 绘图双标题 / fig_sanity / 文献流程 / 移动边界反证 / 耗时落盘 / 表格组表头 / 跨文档一致) 等用户确认
- **v1.6.0 P2 9 项** (Python 探测 / GBK reconfigure / heredoc 反斜杠 / 波浪号中文 / 模板 4 问化 / pack 忽略 / Read 尺寸校验 / Overfull 案例 / rename 列名) 等用户确认

---



> **v1.5.7.20 之前 15 个 hotfix** (v1.5.7.5 ~ v1.5.7.19) → [`CHANGELOG-archive.md`](CHANGELOG-archive.md).
>
> **拆分原因**: 392 行累积, human 翻历史困难. 主文件只留最新 4 个 (writing-for-agents 审计 hotfix).
>
> **查找旧版本**: 用 grep 搜 `CHANGELOG-archive.md` (e.g. `grep -n v1.5.7.10 CHANGELOG-archive.md`).

## v1.5.7.44 — AIGC 2-gram TTR + 3-gram 重复率 L18/L19 (v1.5.7.43 hotfix, user 指令 "继续" → A AIGC 深化)

**核心**: v1.5.7.37 AIGC 扫描只覆盖段首重复率 (check 49) + 连接词密度 (check 50), 漏 n-gram 维度. Sep 13 AIGC 报告 §2.3 报 2-gram TTR 0.457 / 3-gram 重复率 60.3% (Sep 13 阈值). v1.5.7.44 加 2 项 check 深化 AIGC 维度.

**改 `references/scripts/dryrun.py`** (+160 行, 2 个新 check 函数 + 1 个 helper):

- **新增 `_extract_ngrams(text, n)` helper** (8 行): sliding window 提取 n-gram 集, 过滤纯标点 n-gram (避免 "，。""。" 误计)
- **check 51 (AIGC 2-gram TTR L18, auto)**: 跑论文 11 章节 .tex 散文, 跳过注释 + 4 种数学环境 (`$...$` / `\[...\]` / `\begin{equation}` / `\begin{align}`), 计算 2-gram 唯一数 / 总 2-gram 数
  - > 0.45 green (Sep 13 0.457 同级)
  - 0.35-0.45 yellow (Sep 13 同等)
  - < 0.35 red (词汇多样性低, AIGC 风险)
- **check 52 (AIGC 3-gram 重复率 L19, auto)**: 同 check 51, 但 n=3, 重复率 = 1 - 唯一/总
  - < 60% green (Sep 13 60.3% 同级)
  - 60-70% yellow (Sep 13 同等)
  - > 70% red (词汇重复度高, AIGC 风险)

**Sep 13 AIGC 报告 6 维度全映射** (v1.5.7.37 + v1.5.7.44):

| 报告维度 | Sep 13 阈值 | dryrun check | 防御动作 |
|---|---|---|---|
| 段首重复率 | 39.6% | check 49 (L16) | 分散段首为变体 (本问/该问题/此问题) |
| 连接词密度 | 7.5% | check 50 (L17) | 替换"同时/然而/因此"为"且/并/另一方面" |
| 2-gram TTR | 0.457 | check 51 (L18, v1.5.7.44 新增) | 分散词汇: 用同义词替换高频 2-gram |
| 3-gram 重复率 | 60.3% | check 52 (L19, v1.5.7.44 新增) | 分散重复 3-gram: 同义改写 |
| 2-gram TTR / 3-gram 重复率 协同 | TTR 高 (0.5+) + 重复率低 (<60%) = 真多样 | 两项都 green 才算 AIGC 安全 | — |
| "同时" 偏多 | ×8 | check 50 子项 top3 | 替换 2-3 处为"且/并" |

**改 SKILL.md** (1474 → 1475, +1 行, ≤ 1500 ✓):

- §跑题后审计清单 段 check 49/50 描述加 "51/52" 标识 (45/47/48 → 45/47/48/49/50/51/52)

**改 `references/audit/auto-check-list.md`** (+1 节 "AIGC 深化 v1.5.7.44"):

- 加 2-gram TTR / 3-gram 重复率 阈值映射表
- 跑题后必跑 dryrun 段 "L11/L14/L15/L16/L17" → "L11/L14/L15/L16/L17/L18/L19"

**改 `references/audit/post-solution-audit-list.md`** (+2 行 16 层表):

- L18 2-gram TTR / L19 3-gram 重复率 列入 16 层表

**影响文件**:

- 改 `references/scripts/dryrun.py` (+160 行: _extract_ngrams + check_ngram_ttr + check_ngram_repetition + CHECKS 2 行)
- 改 SKILL.md (+1 行)
- 改 `references/audit/auto-check-list.md` (+10 行: AIGC 深化节)
- 改 `references/audit/post-solution-audit-list.md` (+2 行: L18/L19)
- 改 CHANGELOG.md (主文件更新标题)

**dryrun**: 32/49 green + 17 yellow + 0 red (check 35 green SKILL.md 1475 ≤ 1500 ✓ + check 33 green leading words 11 个全在 ✓).

**v1.5.7.44 后续优化方向** (留位):

- check 51/52 当前是字符级 sliding window, 中文 2-gram 大部分跨词边界. v1.5.7.X 可改 jieba 分词 + 词级 n-gram
- check 51/52 跳过数学环境, 但 `\[...\]` `equation` 块可能跨多行, regex DOTALL 覆盖. 复杂 LaTeX (嵌套环境) 可能误判
- 3 个 AIGC check (段首 + 连接词 + n-gram) 综合评分可加, 单项 green 但组合 red 应警惕 (e.g. 段首 25% green + 连接词 8% green + 2-gram 0.3 yellow = 综合 yellow, 暗示刻意分散)

**v1.5.7.34 → v1.5.7.44 累计 11 hotfix** (跨 5 session, 4 个日历日):

- 47 项 dryrun check: 31 → 49 (净增 18 项, v1.5.7.44 +2)
- 文档: 经验汇总 13 KB, 参考文献审计清单 27 KB, 绘图规范 36 KB, references/audit/ 6 个子文件, auto-check-list 加 AIGC 深化节
- 代码: agent_audit.py 10.9 KB
- 审计架构: 单一 self → self + agent 双层 (默认 agent, fresh worker)
- 跑题后必做总耗时: dryrun 1 min + manual 5 类 50 min + 跨文件比对 L4 30 min = 81 min (AIGC 维度加深, 词汇多样性自动检查)

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

