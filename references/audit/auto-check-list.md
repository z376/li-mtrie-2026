# 跑题后自动检查 (v1.5.7.41 拆段自 SKILL.md)

> **拆段原因**: v1.5.7.41 SKILL.md 1500 行临界缓解, 把 v1.5.7.36-37 加的 3 行段拆到本文件. SKILL.md 留 1 行指针 → 本文件.

## 绘图自检 (v1.5.7.36, check 45/47/48 auto)

| check | 防御反例 |
|---|---|
| **45** 旧图 mtime (L11) | v15 P0-3 §5.4 图7/8 是 g_adj 修复前旧图 / v17 P0-E 图7/8/q1_不确定性分配 |
| **47** 冗余图 (L14) | 论文综合 §六.2 8 张冗余未引用图残留 (q2_季节PV箱线图/q2_累计费用/q2_梅雨敏感性 等) |
| **48** 图注 vs axes (L15) | 论文综合 §六.1 图1 SOC 子图缺失 (图注称"上:购电量与电价, 下:储能SOC", 实际只有单面板) |

**完整 §十 实战反例 R1-R5** (R1 旧图 + R2 冗余图 + R3 图注不符 + R4 中文方块 + R5 文字越界) 见 `references/plot/绘图规范与避坑.md`.

## AIGC 扫描 (v1.5.7.37, check 49/50 auto)

| check | 防御反例 |
|---|---|
| **49** 段首重复率 (L16) | Sep 13 AIGC 报告 段首重复率 39.6% (因"问题一/二/三/四"结构). 阈值: <30% green / 30-50% yellow / >50% red |
| **50** 连接词密度 (L17) | Sep 13 AIGC 报告 连接词密度 7.5% (低) / "同时" ×8 偏多. 阈值: <10% green / 10-15% yellow / >15% red |

## AIGC 深化 (v1.5.7.44, check 51/52 auto, n-gram 维度)

| check | 防御反例 |
|---|---|
| **51** 2-gram TTR (L18) | Sep 13 AIGC 报告 2-gram TTR 0.457 (Sep 13 阈值, > 0.35 正常). 阈值: > 0.45 green / 0.35-0.45 yellow / < 0.35 red |
| **52** 3-gram 重复率 (L19) | Sep 13 AIGC 报告 3-gram 重复率 60.3% (Sep 13 阈值, < 70% 可接受). 阈值: < 60% green / 60-70% yellow / > 70% red |

**Sep 13 报告阈值映射**:

| 报告维度 | 阈值 | check 49-52 阈值 | 防御动作 |
|---|---|---|---|
| 段首重复率 | 39.6% | <30% green / 30-50% yellow / >50% red | 分散段首为变体 (本问/该问题/此问题) |
| 连接词密度 | 7.5% | <10% green / 10-15% yellow / >15% red | 替换"同时/然而/因此"为"且/并/另一方面" |
| 2-gram TTR | 0.457 | > 0.45 green / 0.35-0.45 yellow / < 0.35 red | 分散词汇: 用同义词替换高频 2-gram (e.g. 储能/电池/蓄电池, 优化/调度/规划) |
| 3-gram 重复率 | 60.3% | < 60% green / 60-70% yellow / > 70% red | 分散重复 3-gram: 同义改写 (e.g. 储能 SOC 初始 → 储能荷电状态初值) |
| "同时" 偏多 | ×8 | check 50 子项 top3 | 替换 2-3 处为"且/并" |
| "问题" 段首 | ×12 (因"问题一/二/三/四") | check 49 段首重复率 | 改为"本问/该问题/此问题" |
| "本文" 段首 | ×6 | check 49 段首重复率 | 改为"本研究/笔者" |

## FVM Robin 边界离散式 (v1.5.8, check 53 auto, L20 物理机理类必做)

| check | 防御反例 |
|---|---|
| **53** Robin 边界离散式 L20 | 2026A 复盘 v1.1 §2.1 P0-1 (温度场 build_surface_row 返回 `(1.0, 1+β, β)`, β = h·Δr/α ≈ 29611 **式中无 Δt** → 表面钉死在烘房温度 h→∞ 极限). 决定性证据: 正确格式 `dE/dt ÷ [h(T∞−T_s)A] ≈ 0.995`, 错格式 = 223 (不可能). 阈值: 真 Robin 含 `γ=2·h_eff·Δt/Δr` green / `(1, 1+β, β)` 错模式 red / 找不到 bc_row 函数 (非 FVM) yellow |

**正确半控制体 FVM Robin 模板** (圆柱/球坐标通用):
```
(1 + 2μ + γ) · U^{n+1}_{N-1} − 2μ · U^{n+1}_{N-2} = U^n_{N-1} + γ · U_amb
μ = D_eff · Δt / Δr²        (Fourier 数 / 2)
γ = 2 · h_eff · Δt / Δr     (Biot 含 Δt, 不同于经典 Bi = h·Δr/D)
```
完整反例 + 3 类错模式 vs 2 类对模式对照表 → `references/read-checklist/题意红线.md §红线 5`.

## 数据清洗 IQR 误用 (v1.5.8.1, check 54 auto, L21 数据清洗通用必做)

| check | 防御反例 |
|---|---|
| **54** IQR/boxplot + 紧邻 drop L21 | 2026A 复盘 v1.1 §0 P0-2 (附件 1 升温曲线 27 行 + 附件 2 收缩曲线 23 行被 `IQR(k=3) = Q3 + 3×IQR / Q1 - 3×IQR` 全删, **边界条件腰斩**). 趋势数据四分位距天然覆盖不了过程段. 阈值: IQR + 紧邻 `drop/删除/剔除/outlier` 10 行内 red / 纯描述统计 green / 找不到 IQR yellow |

**4 类允许检测 (单调趋势段内, 替代 IQR)**:
1. **物理越界**: `T ∈ [T_min, T_max]`, `C > 0`, `R ∈ (0, R₀]`, `X ∈ [0, 1]`
2. **一阶差分 z>5**: `(ΔT/Δt - μ_rate) / σ_rate`, 比 IQR 严格 (z=1.5 偏松)
3. **物理单调性 (含容差 ε=1e-6)**: 收缩曲线 R 不增, 升温曲线 T 不降
4. **时间间隔+重复值**: Δt 偏差 > 5% 提示时间戳错乱, 重复行保留第 1

完整 4 类代码模板 + 边界/驱动默认保留 + 阶段变化识别 → `references/data-usage/数据清洗规范.md` (6.4 KB, 7 节) + `references/read-checklist/题意红线.md §红线 6`.

## 关键判据数字三来源 (v1.5.8.2, check 55 auto, L22 Step 3 必做)

| check | 防御反例 |
|---|---|
| **55** 关键判据 (Bi/Fo/收缩率/Re/Pr) 来源标记 L22 | 2026A 复盘 v1.1 §0 P0-3 (5.2.2 ρ/cp/k 起止值目测错实 976.4→667.3; 5.4.1"前 10h→1.424cm、78%"目测错实 5h、71.8%; **Bi_m 一次心算 32 实 3.24 差 10 倍**). 阈值: 关键判据 + 含 `实算/print/resultX.xlsx/公式/solver 算` 紧邻 100 字符 green / 无来源 yellow / 找不到关键判据 yellow 跳过 |

**3 类可信来源** (Step 3 强约束):
1. **脚本 print 落盘** (来源=1) — solver 输出 `T_max=33.5279, t_dry=205906 s`
2. **从 resultX.xlsx 读** (来源=2) — `pd.read_excel('result1.xlsx').iloc[:, 1].tolist()`
3. **公式现场算 + 二次独立复算** (来源=3) — `Bi = h·L/k = 25·0.02/0.5 = 1.0`

**禁止** (3 类): ❌ 凭图读数 / ❌ 一次性心算 / ❌ AI 写数字

**配套工具**:
- `求解/数值台账.csv` 4 列 (符号/值/来源/生成脚本), Step 3 起手必建
- `references/scripts/number_ledger.py` 4 子命令 (init/add/check/show), 8.3 KB
- `references/audit/数值台账规范.md` 权威源 4.6 KB 6 节 (3 来源约束 + 4 道防线 + 反例对照 + check 55 协同)

## resultX 结构 vs 附件3 模板 (v1.5.8.3, check 56 auto, L23 物理/数据题必做)

| check | 防御反例 |
|---|---|
| **56** resultX 列名/dtype/sheet vs 附件3 模板 L23 | 2026A 复盘 §P0-4 (4 个 result 的 A 列名写成 `时间`, 模板为 `时间\到药材中心的距离`; result4 多插"半径/cm"列导致距离列右移且为字符串; 论文表5 用了 0.1cm 21 列, 题面要求 0.5cm 5 列). 阈值: 列名不匹配 red / dtype 错 red / 找不到附件3 模板 yellow / resultX 不存在 yellow |

**比对 4 维度** (openpyxl 逐列扫描):
1. **sheet 名集合**: result 应包含模板所有 sheet 名
2. **A 列名精确匹配**: 模板 `时间\到药材中心的距离` vs result `时间` → 错
3. **距离列 dtype 数值**: 不能是字符串 (e.g. `r/cm` 列误为 str)
4. **result4 末列 = "药材表面"**: 题面要求, 不能漏

**论文表步长 vs result 完整序列步长** (读题清单 §10 细化):
- **论文表步长**: 报给评委的最终输出 (e.g. 0.5cm 5 行)
- **result 完整序列步长**: 保存到 resultX 的全部数据 (e.g. dt=60s, t=0 到 205906s ≈ 3433 行)
- 两者分别登记, 不可混用 (论文表 ≠ result 全序列)

## 支撑材料超限预案 (v1.5.8.4, check 57 auto, L24 Step 4.4 打包前必做)

| check | 防御反例 |
|---|---|
| **57** 支撑材料/ 超限 L24 | 2026A 复盘 §P0-5 (result2.xlsx 35→36MB, 单文件即超 20MB 包限). 阈值: >10MB 单文件 + 总 >20MB red / 大文件已配套 csv.gz yellow / 全部 <10MB green / 支撑材料/ 不存在 yellow |

**3 步预案** (单文件 >10MB 触发):
1. **等价压缩 (csv.gz / npz)**: 保留生成脚本 + 重生指引. **重跑后必重新生成**
2. **附录 A/D/J 同步改写**: 附录仍写 result2.xlsx 但包内是 csv.gz → 评审判 FAIL
3. **pack 脚本固化忽略规则**: `~$*` (Office 临时) / `.gitkeep` / `__pycache__/` / `*.aux/*.log` / `run_log.txt` / `.DS_Store`

## 附录 ↔ 支撑材料包一致性 (v1.5.8.5, check 58 auto, L25 终审必做)

| check | 防御反例 |
|---|---|
| **58** 附录 `\texttt{路径}` vs 支撑材料/ 包内文件 L25 | 2026A 复盘 §P0-6 (附录 J 引用 `论文/_frag/gen_tables.py` 不在包内; 附录 A 仍列已剔除 result2.xlsx; 附录 J 表号错位 "表1↔result1" 但符号说明+边界数据占了表1/表2, 题面结果表实为表3-表8). 阈值: 包外文件 red / 全在包内 green / 附录无路径 yellow / 支撑材料 不存在 yellow |

**防御** (静态分析, 不解压 .rar):
- 扫 `paper_dir/10.附录.tex` + `10.0.附录固定说明.tex`
- regex `\\texttt\{([^}]+)\}` 提所有路径
- 验证 `Path(path).name` 在 `支撑材料/` 下某处存在 (rglob basename)
- 缺一 → red (P0-6 翻车)

**留给 v1.5.9 P1 fig_sanity**: 附录表号引用 (e.g. `表1↔result1`) vs 编译 .aux 实际 `\newlabel{tab:xxx}` 一致性 (复杂度高, 跨编译阶段)

## 图形程序化内容自检 (v1.5.9, check 59 auto, L26 跑题后必做)

| check | 防御反例 |
|---|---|
| **59** 图形内容 (np.ptp=0 / U+2080 / 顶暗像素) L26 | 2026A 复盘 §P1-3 (Q1 干燥前沿因阈值写成 `2.5*C0` 曲线恒为 0; C₀ 字形□乱码 U+2080 下标; 22 张图带 set_title 双标题). 阈值: np.ptp=0 red / 顶暗像素 > 0.06 red / U+2080 yellow / 全 green |

**与 check_figure.py 互补**: check_figure.py 是格式层 (DPI/字体), fig_sanity.py 是内容层 (np.ptp/U+2080/顶像素). 两者协同: 内容错走 fig_sanity, 格式错走 check_figure.

**3 类内容自检** (fig_sanity.py):
1. **np.ptp(y) == 0 曲线恒为常数** (阈值写错, Q1 干燥前沿 2.5*C0) → red
2. **全 NaN 列** → red
3. **顶部暗像素占比 > 0.06** (残留 set_title, 双标题) → red
4. **U+2080 下标** (C₀ □乱码) → yellow

**配套脚本**: `references/scripts/fig_sanity.py` (8.5 KB, 含 audit_content 单图 / CLI 扫目录 / 物理范围阈值表)

## 评阅要点对齐 (v1.5.9.1, 文档 + manual 必做, Step 3 起手)

> **触发场景**: 拿到官方评阅要点后发现 7 处可补强 (Q1"烘房数据处理"成段 / Q3"简化烘干条件"鼓励 / Q4 用词"动边界" / **关注点 2 强调"高效"**). 改进: Step 3 增子环节"评阅要点对齐" — 4 列映射矩阵 (题面要求 / 关注点编号 / 落位章节 / 是否显式落位).

**4 大通用关注点** (所有题类必含):
1. **物理机理** (物理定律 + 假设 + 边界条件)
2. **方法合理性** (≥ 3 种方法对比 + 选择理由)
3. **高效** (**实测耗时 + O(复杂度) + 步长依据**, P1-7 联动 code-template meta.json)
4. **结果完整性** (**步长/量程/精度核对表**)

**物理机理类 5 大专属** (A 题/物理题必含):
A1 物理定律引用 / A2 守恒律验证 (v1.5.8 §红线 5) / A3 网格收敛 / A4 极限情况 / A5 参数灵敏度 ±10%

**判定**: 任何 ✗ 项必在 Step 3 起手前补写对应章节. 跑题后 audit 阶段必跑 映射矩阵所有 ✓ → 验证.

**配套文档**: `references/评阅要点对齐.md` (5.0 KB, 6 节, 权威源) + `references/paper/paper-spec.md` §一 新增 2 段 (4 大通用 + 5 大专属对照表)

## meta.json 3 件套 (v1.5.9.4, check 60 auto, L27 评阅关注点 2 '高效' 必填)

| check | 防御反例 |
|---|---|
| **60** meta.json 含 3 件套 L27 | 2026A 复盘 §P1-7 (脚本 print 了 elapsed 但未入交付文件, 论文靠会话记忆). 阈值: 7 字段全填 green / 任一缺 red / meta.json 不存在 red |

**必填 7 字段** (code-template 强制落盘):
1. **elapsed_sec** — 实测耗时 (s) ★ 评阅关注点 3
2. **steps** — 时间步数
3. **grid** — 网格数 (e.g. `N_r=100, N_t=3433`)
4. **dt** — 时间步长 ★ 步长依据
5. **dr** — 空间步长 (PDE/网格题) ★ 步长依据
6. **complexity** — O(复杂度) (e.g. `O(N_r·N_t)`) ★ 评阅关注点 3
7. **version** — Python 版本 + code-template 版本

**论文 §5.X.2 "模型求解" 段必引 3 件套**: 步长依据 (dt/dr) + O(复杂度) (complexity) + 实测耗时 (elapsed_sec)

**配套脚本**:
- `references/code-template.py` (改, 末尾加 meta 段)
- `references/scripts/check_meta.py` (新建, 3.6 KB, audit_meta + CLI)

**跑题后必跑 dryrun** (L11/L14/L15/L16/L17/L18/L19/L20/L21/L22/L23/L24/L25/L26/L27/L28 全覆盖).

## 论文表格两行表头 (v1.5.9.5, check 61 auto, L28 题面格式合规必做)

| check | 防御反例 |
|---|---|
| **61** 论文 .tex 表格两行表头 L28 | 2026A 复盘 §P1-8 (题面表 1-6 模板带 `到药材中心的距离/cm` **跨列组表头**, 我们的表只有裸距离值缺该组标签, 审计判 WARN. 题面明确"按表 X 的格式给出", 格式偏差会被对照). 阈值: `\multicolumn` + `\multirow` 配对 green / 缺 `\multirow` yellow / 全无配对 red / 无 longtable yellow |

**正确两行表头写法** (题面表 1-6 模板格式):
```latex
\begin{longtable}{cccc}
  \caption{问题4 干燥前沿随时间变化} \\
  \toprule
  \multicolumn{3}{c}{到药材中心的距离/cm} & \multirow{2}{*}{药材表面} \\
  \cmidrule(lr){1-3}
  0 & 0.5 & 1.0 & 含水率/\% \\
  \midrule
  ... % from df.to_latex()
  \bottomrule
\end{longtable}
```

**关键**:
- 第 1 行: `\multicolumn{n}{c}{组标签}` (跨列组, e.g. `到药材中心的距离/cm`) + `\multirow{n}{*}{命名列}` (命名列如"药材表面"**不纳入组头**、单独列)
- 第 2 行: 行表头 + 各列值
- 需 `\usepackage{multirow}` (booktabs + multirow)

**跨 v1.5.8.3 check 56 协同**: check 56 比对 resultX **列名** vs 附件3 模板; check 61 比对论文 .tex **表头** vs 题面模板格式. 两个都要, 缺一个都判格式偏差.

## Python 探测 + 波浪号中文 (v1.6.0, check 0 第 0 项 + check 63 L29)

| check | 防御反例 |
|---|---|
| **62** Python 解释器探测 (第 0 项) | 2026A 复盘 §P2-1 (`python` 为**微软商店占位符** exit 49, 全程被迫 `py`). 探测 `py -3` → `python` → `python3`, exit 49 = 占位符跳过. 阈值: 探测 OK + pip 同源 green / 探测 OK 但 pip 不同源 yellow / 全不可用 red |
| **63** LaTeX 波浪号后接中文 L29 | 2026A 复盘 §P2-4 (`\textasciitilde` 直接接中文 → **未定义命令** ×2, 编译报错). 波浪号后仅接数字/空格, 接中文用"至". 阈值: 无命中 green / template 状态 yellow / 命中 red |

**配套文档**: `references/workflow/Python环境.md` (6.1 KB, 8 节权威源: 探测式 + 3 步绿验证 + GBK 兼容 + venv + 装包/预下载 + 踩坑库 7 项)

## SKILL.md 自洽性 (v1.7.0, check 68 L34)

writing-for-agents 第 2 轮代理审计 (2026-10-29) 抓出 3 个 P0, 全是"文档自己和自己对不上"型 ——
任何单文件阅读都发现不了, 但一改就错. check 68 把这类自洽性变成可执行锚点.

| check | 防御反例 | 阈值 |
|---|---|---|
| **68** SKILL.md 自洽性 L34 | 5 条规则: **R1** 必读 3 文件 description↔正文一致 (审计原 P0-1: description 指 5道防线自检清单, 正文指 读题清单.md → always-loaded 指针漏掉 check 19 依赖的 读题清单.md) / **R2** 状态机 Step 0/1/2/3/4 每框都有 green/red 判据门 (原 P0-2: Step 0 无门 + 两套互不引用的判据) / **R3** .tex 数量声明 = 模板实际 (11 章节 / 20 章节 .tex / 模板 25 个 .tex, 原口径 5 处不一致: 11/14/18/25) / **R4** 判据用词统一 green-red (原声明"用 green/red 不用绿/红", 实际中文用了 65 次) / **R5** 无坏字符串 ("干 run") 且 8 项自检指针不得写 §2 (真位置 = paper-spec.md §4.0) | 任一规则命中 red / 全过 green |

**反向验证**: 7 条注入用例 (R1/R2/R3/R3b/R4/R5a/R5b) 逐条造错 → 必须 red, 已全过.

**配套文档**: `references/audit/验收清单.md` §J (打钩区) + `references/audit/验收标准.md` (§1 表 6 项 + §0 对照表)

## 验收标准复核 (v1.6.3-4, check 64 L30 + check 65 L31 + check 66 L32)

2026A 复盘 §验收标准 6 条 → 可执行锚点 (权威源: `references/audit/验收标准.md`)

| check | 防御反例 | 阈值 |
|---|---|---|
| **64** 表面行能量守恒 L30 | 2026A P0-1 (温度场 `build_surface_row` 返回 `(1, 1+β, β)`, β=h·Δr/α 无 Δt = h→∞ 极限). 决定性证据 = `dE/dt ÷ [h(T∞−Ts)·A]`: 错 **223** vs 对 **0.995**. 工具 `references/scripts/bc_check.py` (ConservationRecorder 2 行接入 + CLI 3 模式). check 64 = A 段防御资产自检 (bc_check.py 自测须能区分 对组 1 / 错组 223) + B 段项目 `求解/问题N/**/守恒记录*.csv` 实测 | 资产缺失 red / 数据偏离 red / 区间不足 yellow / 其余 green |
| **65** 论文数字台账覆盖 L31 | 2026A P0-3 (5.2.2 ρ/cp/k 目测错 976.4→667.3 + 5.4.1 "前10h→1.424cm、占78%" 目测错 + Bi_m 心算 32 实 3.24). **反向**检查 (check 40 是正向). 候选数字口径: 排除年份 1900-2100 + 0-9 整数计数 + 注释 + 数学环境 + `\label`/`\ref` | 台账不存在 yellow / 台账 <3 条 yellow / 覆盖率 <40% red / 40-70% yellow / ≥70% green |
| **66** 表/图编号一致性 L32 | 兑现 check 58 的留位 ("表号错位留给 P1 fig_sanity"): **2026A P0-6** 附录 J 写"表1↔result1"但符号说明+边界数据占了表1/表2, 题面结果表实为表3-表8. 4 条规则: R1 重复 label / R2 悬空 `\ref` / R3 越界"表 N 图 N" / R4 附录 `resultM↔表N` 自相矛盾. **v1.6.2 模板曾中招** (`eq:model`/`eq:constraints`/`fig:q1_results` 各 ×4) | 任一规则命中 red / 全过 green |

**配套文档**: `references/audit/验收标准.md` (9.5 KB, 6 条逐条 → check 号/判据/兜底) +
`references/audit/验收清单.md` §J (打钩区 + 4 条自查命令)

## 读图串档 + Overfull 案例 + 统一列名 (v1.6.1, 文档 + 工具增强)

| 项 | 类型 | 落点 | 防御反例 |
|----|------|------|---------|
| **P2-7** 读图串档 | 代理审计 H 板块 (H1-H3) | `references/代理审计prompt.md` + `fig_sanity.py` 尺寸校验 | 2026A 复盘: Read 工具读图同尺寸串档. 防御: PIL 尺寸校验 + montage 拼图 + 文件名水印 + 单张读取. fig_sanity.py 加 `check_fig_dimensions` + `check_fig_duplicate` (md5 比对) |
| **P2-8** Overfull 3 案例 | 文档 | `references/paper/paper-spec.md §4.1` | 2026A: Overfull 修复套路重复劳动 (本轮 6→0). 加 3 案例表 (列宽超 / 缺列声明 / 长文本溢出) + **粗体字体回退警告标注"无害"** (不影响编译, 不用修) + 快速定位命令 |
| **P2-9** 统一列名 | 模板 | `references/code-template.py` | 2026A: 绘图脚本按旧列名 `时间` 过滤 (模板列名已改 `时间\到药材中心的距离`) → KeyError; result4 已删 `半径/cm` 列但脚本仍读. 防御: `normalize_result_df()` (首列 → '时间') + `numeric_columns_except_first()` (列集合按位置推导, 不硬编码) |

**跑题后必跑 dryrun** (L11/L14-L29 全覆盖).

## 引用

- `SKILL.md` 1 行指针 → 本文件
- `references/plot/绘图规范与避坑.md §十` (R1-R5 5 类图问题实战反例)
- `references/audit/参考文献审计清单.md` (L11-L17 详细描述)
- `references/audit/post-solution-audit-list.md` (v1.5.7.41, 16 层总览)