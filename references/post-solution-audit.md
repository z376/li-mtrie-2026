# Post-Solution Audit (跑题后必做, v1.5.5 新增, 4 必做 + 1 可选)

> v1.5.7.5 从 SKILL.md 拆出, 留指针. sign-off 绿后跑 20-30 分钟, 比交卷后评委扣分划算.

**为啥新增**: 2025C 跑题 other agent 写完 4 个问题的 .py + 论文, 但**没审过**:
- 解题思路是否真对题面 quote 锚定表? (P0-1 sheet 错, P0-2/3 BMI 分组错)
- 代码是否真跑了? 输出文件齐不齐?
- 图片是否实际生成? 5.X.2 引用的图都在不在?
- 5.X.2 论文 .tex 里的数字跟 resultX.xlsx 一致不?

**dryrun check 15/16/17 只查"文件存在性"**, 不查"内容合理性" (那是 LLM 评审/人工审的范围). Post-Solution Audit 是介于两者之间的"机械一致性"自检, 4 必做 + 1 可选.

---

### 必做 1: 解题思路 vs quote 锚定表交叉验证

**目标**: 每问的实际解法跟 Step 0 写的 quote 解读对齐.

```powershell
# 读 求解/求解计划.md 顶部 quote 锚定表
Get-Content 求解\求解计划.md -Head 20

# 读 5.X.1 章节开头, 找"建模思路"段
Get-Content 论文\5.1.1.分析与准备.tex

# 逐问对比: quote 解读里说的"用哪个 sheet" 跟 .py 里的 pd.read_excel(..., sheet_name=?) 一致?
# 例: quote 表写"问题 4 用 Sheet2 (女胎)" → 验证 问题4_xxx.py 里有 sheet_name=1 或 sheet_name="女胎"
```

**为啥必做**: 2025C P0-1 (sheet 错) 如果跑题后审一遍, 会发现"问题 4 .py 写 sheet_name=0 但 quote 表说用 Sheet2", 立刻发现错。

### 必做 2: 代码实际跑过 + 输出文件齐全

**目标**: 4 个 .py 都跑过, 各自有输出 (.png + .csv/xlsx).

```powershell
# 检查每个问题有 .py + 图片/ + 结果/ 目录, 目录非空
foreach ($q in 1..4) {
  $qdir = "求解\问题$q"
  $py = Get-ChildItem "$qdir\*.py"
  $png = Get-ChildItem "$qdir\图片\*.png" -ErrorAction SilentlyContinue
  $csv = Get-ChildItem "$qdir\结果\*.csv" -ErrorAction SilentlyContinue
  Write-Host "问题 $q: py=$($py.Count), png=$($png.Count), csv=$($csv.Count)"
}
# 预期: 每个问题 py=1, png≥4, csv≥1
```

**为啥必做**: 防止"代码写了但没跑" / "图引了但没生成" / "结果 xlsx 没导出". dryrun check 17 只查"图引用了文件存在", 不查"图实际生成了"。

### 必做 3: 5.X.2 数字 ↔ resultX.xlsx 一致性

**目标**: 论文 5.X.2 章节里的 R², AUC, 准确率, 异常数 等数字, 跟 `求解/问题X/结果/resultX.xlsx` 完全一致.

```powershell
# 读 resultX.xlsx 关键数字
py -3 -c "import openpyxl; wb = openpyxl.load_workbook('求解\问题1\结果\问题1_模型评估.csv' if Test-Path '求解\问题1\结果\问题1_模型评估.csv' else None); print(wb.active.values)"

# 跟 论文 5.1.2.建模与求解.tex 里的数字对照
# 例: 摘要写 R²=0.4823, resultX.xlsx 里的 R² 应 = 0.4823 (4 位小数)
```

**为啥必做**: 评委对比"论文数字" vs "支撑材料 xlsx" 不一致 = 直接判"数据不可信"分。dryrun check 不查数字一致性 (需要 LLM 评审/人工对比).

### 必做 4: 5.X.2 引用的图/表都存在

**目标**: 5.X.2 章节 `\includegraphics{...}` 和 `\ref{tab:...}` 引用的所有图/表都生成 + 编号连续.

```powershell
# 跟 check 17 类似, 但只看 5.X.2 (不看其他章)
$content = Get-Content 论文\5.1.2.建模与求解.tex -Raw
$imgs = [regex]::Matches($content, '\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}')
$tabs = [regex]::Matches($content, '\\ref\{(tab:[^}]+)\}')
foreach ($i in $imgs) {
  if (-not (Test-Path (Join-Path "论文" $i.Groups[1].Value))) {
    Write-Error "MISSING: $($i.Groups[1].Value)"
  }
}
Write-Host "5.1.2 引 $($imgs.Count) 张图, $($tabs.Count) 个表"
```

**为啥必做**: dryrun check 17 是"全论文范围", 5.1.2 是核心章节, 单独审一遍更稳.

### 可选 5: LLM 工具 03-自动审稿 (v1.5.0 借鉴, 30 分钟)

如果时间允许, 用 `references/llm-prompts/03-自动审稿.md` 跑 5 维 LLM 评审 (机理/数据/写作/创新/排版), 输出"AI 痕迹词" + 改进建议. 这是可选, 不是必做, 因为要花 30 分钟. sign-off 必做是前 4 项机械检查, LLM 评审是 sign-off 之后做.

---

**Post-Solution Audit 跟 5 步状态机的关系**:
- 5 步状态机 (Step 0-4) 是 "流程" — 跑题过程中每一步必做
- Post-Solution Audit 是 "终审" — 跑题完成 (sign-off 绿) 后, 再过一遍 4 必做
- 4 必做总耗时 20-30 分钟, **比交卷后评委扣分划算得多**
