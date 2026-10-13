# 跑题后 Manual 兜底清单 (v1.5.7.42 新建, 5 类 L8/L9/L10/L15/L16)

> **本文件**: dryrun 47 项 hardcode 是 mechanical 防线, 抓不到内容级推理. 5 类留位 manual 在本文件详细描述 (含 PowerShell 命令 + 实战反例 + 修复).
>
> **何时用**: dryrun sign-off 绿后, 跑题后必做 manual 5 类, 总耗时约 60 分钟.
>
> **详细 16 层总览** (L1-L16 16 个 check 类型 + auto/manual 分类) 见 `references/audit/post-solution-audit-list.md`.

---

## L8 灵敏度表 ↔ 代码 (manual, 10 min)

**目标**: 论文 §6/§7/§8 含"灵敏度"/"参数扫描"/"敏感性"等关键词的表, 必须有对应 `.py` 脚本在 `求解/` 里 (有 noise injection 或 parameter sweep 循环).

**结果图文献 (Sep 11) §3.5 反例**: 惩罚系数四档 (15,512,526 / 15,607,482 / 15,690,228 等) 与预测误差五档 (15,651,102 … 17,540,736) 在 求解/ 全部脚本中**找不到对应实验代码** (无噪声注入、无参数扫描循环), 不可复现.

### 手工验证步骤

```powershell
# 1. 提取论文 §6/§7/§8 中所有数字表
Get-Content 论文\6.模型检验.tex, 论文\7.模型评价.tex, 论文\8.模型改进推广.tex
# 手动找含"灵敏度"/"参数扫描"/"敏感性"/"扰动"等关键词的表

# 2. grep 求解/ 下所有 .py 文件, 找是否含 noise_injection / sweep / sensitivity / parameter 等关键词
Select-String -Path 求解\**\*.py -Pattern "noise_injection|sweep|sensitivity|parameter_scan|扰动|扫描|敏感"
# 应该至少 1 个 .py 含相应逻辑 (否则: 补写 / 删表)

# 3. 跑对应 .py 脚本, 看输出是否匹配 §6/§7/§8 表格
python 求解\问题3\问题3_灵敏度.py
# 输出数字应与 §7 灵敏度表 ±1% 偏差 (允许数值舍入)

# 4. 不匹配 → 补写灵敏度实验脚本 (改动系数需重跑全年 Q3) 或 删除该表
```

### 修复命令

```bash
# 情况 A: 脚本存在但数字对不上
# 1. 对比 result 文件真实数字与论文表格, 找出偏差最大的 1 行
# 2. 改 .py 脚本 (e.g. noise_injection.scale, sweep.range)
# 3. 重跑 .py → 重新生成 result xlsx
# 4. 改论文 §6/§7/§8 表格数字 (用 result 真实值, 不用 AI 编造)

# 情况 B: 脚本不存在
# 1. 删论文 §6/§7/§8 灵敏度表 (不可复现的表 = 编造数据, 评委扣分)
# 2. 或补写 .py (e.g. noise_injection + sweep 循环, 跑 4-5 档参数)
```

### 反例防御

- **结果图文献 §3.5**: 灵敏度表无代码支撑 → 评委要求支撑材料时无法提供 → 论文扣分
- 防御: 写论文时, 任何"参数扫描"/"灵敏度"表**必须**先有 .py 跑出, 再写表
- 防回腐: 写完论文回头 grep 求解/ 验证, 没代码的表 = 必修

---

## L9 SOC 末值合理性 (manual, 10 min)

**目标**: 论文 §5.X 四季代表日 / 跨日 SOC 末值 应等于 SOC 初值 (日末储能无终值价值, 优化器每日放空) + 不超模型上限 (e.g. SOC_max=10800 kWh).

**结果图文献 (Sep 11) §3.3 反例**: SOC 末 13424 > 10800 违反自身约束; Q2 表 SOC 末 5767/8430/5606/9253, Q3 表 SOC 末 5703/9588/9664/**13424** (超出模型上限 10800). 论文 SOC 末列**全部编造**.

### 手工验证步骤

```powershell
# 1. 提取 §5.2/§5.3/§5.4 四季代表日表中 SOC 末 列所有数字
Get-Content 论文\5.2.建模与求解.tex, 论文\5.3.建模与求解.tex
# 找 SOC末 / S末 / 储能末值 等列

# 2. grep resultX.xlsx 对应 sheet (SOC) 实际值
# 用 references/scripts/verify_pdf_metrics.py 辅助 (或 Python openpyxl)
python -c "import openpyxl; wb=openpyxl.load_workbook('求解\问题2\结果\result2.xlsx'); ws=wb['SOC']; print([ws.cell(i,24).value for i in range(2,6)])"
# 提取四季代表日对应日 SOC 末值

# 3. 比对:
#    - 实际 SOC 末 = 1200 (日末放空) → 论文应写 1200
#    - 实际 SOC 末 < SOC_max → 论文不应 > SOC_max
#    - 不匹配 → 用复算值替换, 删除编造值

# 4. 检查 SOC 末值列所有数字是否 ≤ SOC_max
#    e.g. SOC_max=10800 kWh → 任何 > 10800 数字 = 编造
```

### 修复命令

```bash
# 情况 A: 论文 SOC 末 ≠ 实际
# 1. 跑 resultX.xlsx 提取真实 SOC 末
# 2. 改论文 §5.X 四季代表日表: 用 result 真实值替换

# 情况 B: SOC 末 > SOC_max
# 1. 99% 是编造. 跑 plan_day 重算 SOC 序列
# 2. 改论文 SOC 末值为真实复算值 (通常 = 1200, 日末放空)

# 情况 C: 论文 SOC 初 6000 但 SOC 末 ≠ 6000
# 1. 检查 §3 假设: "Q1 强制 S(0)=S(24)=6000"
# 2. 若 §3 假设强制, 论文应写 SOC 末 = 6000 (与 §3 一致)
# 3. 若 §3 假设不强制, 论文应写 SOC 末 = 1200 (放空, 无终值价值)
```

### 反例防御

- **结果图文献 §3.3**: Q2/Q3 四季 SOC 末编造 → 评委按 result 文件复算发现 → 一票否决
- 防御: 写 §5.X 四季表前, 必跑 resultX.xlsx 提取真实 SOC 末值, 用 result 真实值写
- 防回腐: 写完 §5.X 后回头核对 SOC 末值 ≤ SOC_max, 跨日 SOC 连续性 (e.g. Q2 末 = Q3 初)

---

## L10 假设 ↔ 代码 (manual, 15 min)

**目标**: 论文 §3 模型假设 应与 `求解/共享/planner.py` 实际方法一致.

**v15 P0-2 反例**: 摘要、§5.2、表 7 方法名均称 "Bertsimas-Sim Γ 预算"; §7 模型评价写"引入**逐时段最坏情况约束**\cite{bertsimas2004}"; §8.1.1 改进方向写"采用 Bertsimas-Sim Γ 预算约束". 实际代码 plan_day_robust L422-425 对**每一个时段**施加最坏情况约束 `pv·(1-δ)·Δt + g + pd ≥ load·(1+δ)·Δt + pc`; Γ 参数只出现在求解后检查 `bs_ok` (L452-463), **从未进入约束**. 这是**逐时段 worst-case, 不是 Bertsimas-Sim**.

**论文综合 (Sep 12) §3.1 反例**: §3 假设 5 写"完美预测 (Q1、Q2): 问题一和二中光伏出力与负荷为已知确定性数据", 实际 Q2 用 Bertsimas-Sim 鲁棒优化 (预报误差 σ=10%). 假设与代码矛盾.

### 手工验证步骤

```powershell
# 1. 读 求解/共享/planner.py 找实际方法名
Select-String -Path 求解\共享\planner.py -Pattern "def plan_day|def plan_day_robust|def robust_lp|def mpc_rolling|def benders|forecast|鲁棒|滚动|δ_pv|Γ"
# 输出: plan_day (确定性) / plan_day_robust (鲁棒) / mpc_rolling (滚动) / benders (分解) 等

# 2. 读论文 §3 假设
Get-Content 论文\3.模型假设.tex
# 找: "完美预测" / "确定性 LP" / "鲁棒优化" / "MPC 滚动" / "Benders 分解" 等

# 3. 验证: 假设里的方法名是否对应代码实际方法
#    假设"鲁棒优化 (σ_pv=10%, σ_load=5%)" → 验证 planner.py plan_day_robust 含 σ_pv=0.10, σ_load=0.05
#    假设"逐时段最坏情况" → 验证 plan_day_robust 对每时段施加 pv·(1-δ) 约束 (不是 Γ 预算)

# 4. 检查关键参数 (δ_pv, δ_load, Γ_pv, Γ_load) 是否在代码约束里
Select-String -Path 求解\共享\planner.py -Pattern "delta_pv|delta_load|0\.1[05]|0\.05|6\.0|4\.0"
# 找到: 关键参数真实值, 跟论文 §3 假设 / §5 公式是否一致
```

### 修复命令

```bash
# 情况 A: 假设方法名跟代码不一致
# 方案 1: 改论文 §3 假设 + §5 + §7 描述 (推荐, 工作量小)
#    "Bertsimas-Sim Γ 预算" → "逐时段最坏情况鲁棒约束 (预算思想源自 Bertsimas-Sim)"
#    删 Γ_pv=6 / Γ_load=4 约束级声称 (实际是求解后检查, 不是约束)

# 方案 2: 改代码实现真 Γ 预算 (工作量大, 不建议赛前做)
#    在 plan_day_robust 加 Γ_pv 控制最坏时段数, 不再对每时段施加约束

# 情况 B: 假设参数跟代码不一致
# 1. 找论文 §3 假设参数 (e.g. σ_pv=10%, σ_load=5%)
# 2. 找代码实际参数 (grep planner.py)
# 3. 不一致 → 改论文 §3/§5/§7 描述 (推荐) 或改代码参数

# 情况 C: §3 假设 "完美预测" 但代码是鲁棒优化
# 1. 改 §3 假设 5: "Q1 完美预测; Q2-Q4 鲁棒优化 (σ_pv=10%, σ_load=5%)"
# 2. 改 §5.2/§5.3/§5.4 摘要: 不再说 "Q2 确定性 LP", 改 "Q2 鲁棒优化"
```

### 反例防御

- **v15 P0-2**: Bertsimas-Sim vs 逐时段 worst-case 矛盾 → §7/§8 反而如实描述了真实实现, 但摘要/§5 写错 → 评委按代码核验发现
- 防御: 写 §3 假设时**必读 planner.py**, 假设与代码 1:1 对应
- 防回腐: 写完 §3 后, 必跑 `Select-String` 验证关键参数 (δ_pv, δ_load, Γ) 在代码里

---

## L15 双向题 vs 4h 窗口 (manual, 5 min)

**目标**: 论文 Q3 双向违约价 (over/under 双向罚) + §5.2 推导 应与代码 0.5/1.5 双向罚一致; Q1 6 个 10 分钟时段 (10:00-10:10 等) 应与 result1.xlsx 指定时段表 sheet 一致.

**论文综合 (Sep 12) §2.3 + §3 反例**: Q3 论文总费 15,854,382 vs code 31,288,350, **漏算双向罚 1,075,244** (论文只写了 g_plan 累计, 没含 over/under 罚). Q1 论文表 2/表 3 与 result1.xlsx 不符 (分表合计 39,483 ≠ 59,264; 电价列 0.38/0.85 vs 实际 0.37-1.40).

### 手工验证步骤

```powershell
# Q3 双向罚验证:
# 1. 读 求解/问题3/问题3_双向罚.py 找双向罚参数
Select-String -Path 求解\问题3\问题3_双向罚.py -Pattern "over_price|under_price|0\.5|1\.5|双向"

# 2. 跑 result3.xlsx, 提取 over_total/under_total 列求和
python -c "import openpyxl; wb=openpyxl.load_workbook('求解\问题3\结果\result3.xlsx'); print([s for s in wb.sheetnames if 'over' in s or 'under' in s or '罚' in s])"

# 3. §5.3 双向罚金额应等于 over_total × 1.5 + under_total × 0.5
#    不一致 → 改 §5.3 总费 = 调整购电费 + 双向罚

# Q1 6 时段验证:
# 1. 读 result1.xlsx 合规 sheet (表1-指定时段购电)
python -c "import openpyxl; wb=openpyxl.load_workbook('求解\问题1\结果\result1.xlsx'); print(wb.sheetnames)"

# 2. 提取 6 个 10 分钟时段 (10:00-10:10, 10:10-10:20, ..., 10:50-11:00) 购电量
#    §5.1.2 表 2 应展示这 6 行 + 全天购电量 + 全天购电费

# 3. 论文表 vs result 真实值比对: 每行数字应一致 ±1% (允许舍入)
```

### 修复命令

```bash
# Q3 双向罚漏算:
# 1. 跑 result3.xlsx 提取 over_total, under_total
python -c "import openpyxl; wb=openpyxl.load_workbook('求解\问题3\结果\result3.xlsx'); ws=wb['调整购电量']; print(ws.cell(2, 1).value)"

# 2. 改 §5.3 总费 = 调整购电费 + over × 1.5 + under × 0.5
#    e.g. 31,288,350 = 15,854,382 + 15,358,968 × 0.5 + 0 × 1.5
#       (实际拆分由 result 真实数字决定)

# Q1 6 时段展示错误:
# 1. 找 result1.xlsx 合规 sheet 数据
# 2. 用合规 sheet 数据重做 §5.1.2 表 2/表 3
#    删论文自定义分时段 (凌晨/早峰/午间), 改用题目规定的 6 个 10 分钟时段
```

### 反例防御

- **论文综合 §2.3**: Q3 总费漏算双向罚 → 评委按 result 复算发现偏差百万级 → 一票否决
- 防御: 写 §5.3 前**必跑 result3.xlsx**, 数字加双向罚 (over × 1.5 + under × 0.5)
- 防回腐: 写完 §5.X 后, 每问跑 result 真实数字 vs 论文数字, 偏差 > 1% 必修

---

## L16 Q1 表1/表2 格式 (manual, 10 min)

**目标**: 论文 Q1 展示应按题目要求"表1格式给出 6 个 10 分钟时段购电量 + 全天购电费" + "表2格式给出 4 小时窗口充放电量 + 0:00/24:00 储电量".

**结果图文献 (Sep 11) §3.4 反例**: 论文 Q1 用自定义 6 时段划分 (凌晨/早峰/午间...), 未呈现题目规定表格; result1.xlsx 中已有合规 sheet (表1-指定时段购电: 486.40/394.93/636.98; 表2-指定时段充放电), 论文应直接引用.

### 手工验证步骤

```powershell
# 1. 打开 result1.xlsx, 找 sheet "表1-指定时段购电" (或类似)
python -c "import openpyxl; wb=openpyxl.load_workbook('求解\问题1\结果\result1.xlsx'); print(wb.sheetnames)"

# 2. §5.1.2 应展示:
#    表 1: 10:00-10:10 / 10:10-10:20 / ... / 10:50-11:00 共 6 行 + 全天购电量 + 全天购电费
#    表 2: 4 小时窗口 (e.g. 04:00-08:00) 充放电量 + 0:00 / 24:00 储电量

# 3. 找 sheet "表2-指定时段充放电" (或类似)
# 4. §5.1.2 应展示: 4 个 4 小时窗口的充电量/放电量 + 起始/结束 SOC
```

### 修复命令

```bash
# 情况 A: 论文用自定义分时段, 没用题面规定表格
# 1. 打开 result1.xlsx, 找合规 sheet "表1-指定时段购电" 和 "表2-指定时段充放电"
# 2. 提取数字: 6 个 10 分钟时段购电量 (486.40/394.93/636.98 等) + 4 小时窗口充放电量
# 3. 用合规 sheet 数据重做 §5.1.2 表 1/表 2/表 3
#    删论文自定义分时段 (凌晨/早峰/午间), 改用题目规定 6 时段

# 情况 B: 论文表与 result 数据不符
# 1. result1.xlsx 实际数据 vs 论文表数字, 找差异行
# 2. 改论文用 result 真实值 (允许 ±1% 舍入)

# 情况 C: SOC 最小值错误 (论文 1200, 实际 1834.6)
# 1. 跑 result1.xlsx SOC sheet, 找最小值
# 2. 改 §5.1.2 + §6 检验表: SOC 最小 = 1834.6 kWh
```

### 反例防御

- **结果图文献 §3.4**: Q1 未按题面表1/表2 格式 → 题目明确要求, 形式扣分
- 防御: 写 §5.1.2 前**必读 result1.xlsx 合规 sheet**, 用合规数据重做表
- 防回腐: 写完 §5.1.2 后, 回头核对: 是否有 6 个 10 分钟时段 (10:00-10:10 等) + 4 小时窗口 + 0:00/24:00 储电量

---

## 跑题后必做顺序 (5 类 manual 总览)

| manual | 时间 | 优先级 | 反例来源 |
|---|---|---|---|
| L8 灵敏度表 ↔ 代码 | 10 min | 中 | 结果图文献 §3.5 |
| L9 SOC 末值合理性 | 10 min | 高 (一票否决级) | 结果图文献 §3.3 (SOC 13424 > 10800) |
| L10 假设 ↔ 代码 | 15 min | 高 (一票否决级) | v15 P0-2 (Bertsimas-Sim 矛盾) + 论文综合 §3.1 |
| L15 双向题 vs 4h 窗口 | 5 min | 高 (一票否决级) | 论文综合 §2.3 (漏算双向罚百万) |
| L16 Q1 表1/表2 格式 | 10 min | 中 (形式扣分) | 结果图文献 §3.4 (未按题面格式) |
| **总耗时** | **50 min** | | |

## 引用

- `SKILL.md` 1 行指针 → 本文件 (v1.5.7.42 新增)
- `references/audit/post-solution-audit-list.md` (v1.5.7.41, 16 层总览)
- `references/audit/auto-check-list.md` (v1.5.7.41, check 45/47/48/49/50 简表)
- `references/audit/agent-audit-brief.md` (v1.5.7.41, 代理审计 brief 说明)
- `references/audit/参考文献审计清单.md` (v1.5.7.35, 27 KB, 16 层详细描述)