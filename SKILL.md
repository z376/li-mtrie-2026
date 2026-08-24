---
name: li-mtrie
description: |
  数学建模竞赛端到端 skill。Use this skill when the user says "开始求解"、"求解这个题目"、
  "生成论文"、"做数模"、"国赛/美赛/MCM/ICM/CUMCM 求解" or pastes a math modeling
  problem PDF and asks to solve it. Triggers on phrases like "开始建模"、"跑代码写论文"、
  "出论文 PDF"、"帮我做这道数模题".

  Do NOT use for general data analysis, one-off Python scripts, or research questions
  that don't lead to a 论文.pdf deliverable.
metadata:
  version: "1.2"
  category: competition-workflow
  scope: user
  source_workspace: D:/MiniMax code/1/数建Skill模板
  spec_compliance: "全国大学生数学建模竞赛论文格式规范（2026年修订稿，2026-09-01起试行）+ 全国大学生数学建模竞赛人工智能工具使用规定（2026年试行）"
---

# Math Modeling

数学建模竞赛（国赛/美赛/校赛）端到端解题 + 论文写作工作流。基于 2024 高教社杯 4 篇
获奖论文（B159/B195/B196/D039）的结构归纳，并按 2026 年全国组委会修订的论文格式
规范（2026 年修订稿）+《人工智能工具使用规定（2026 年试行）》做了对齐更新。

## Inputs to collect

开始前确认三件事（**没准备好就停下来等用户**）：

1. **赛题 PDF** → 用户是否已放进 `题目/` 目录
2. **数据文件** → 用户是否已放进 `数据/` 目录（xlsx / csv / docx）
3. **建模类型** → 用户是否已知问题类型（优化/评价/预测/分类/机理）

如果用户只说"开始求解"而没放题/数据，**必须**先停下来等用户放好再启动。

## Python 环境就位（开赛第 1 小时必做）

**为什么**：Windows 上常同时存在多个 Python（微软商店版 / Anaconda / 系统版 / VS Code 选中版），
`pip install` 装到 A 解释器，Jupyter 用的却是 B 解释器 → `import pulp` 仍 `ModuleNotFoundError`。
**半小时排查不如提前 30 秒确认**。

**3 步确认（开赛第 1 小时跑一次，截图存 `求解/环境确认.md`）**：

```powershell
# 1) 确认"接下来要用的"是哪个解释器
python -c "import sys; print(sys.executable)"
# 记下输出路径, 例如: C:\Python312\python.exe
# 后续所有 python / pip 都用这个

# 2) 确认 pip 和 python 是同一个（避免 pip 装到别处）
python -m pip --version
# 看输出第一行是不是和上面 sys.executable 一致

# 3) 装包后用同一个解释器验证
python -c "import pandas, numpy, scipy, matplotlib, openpyxl; print('core ok')"
```

**推荐版本**：Python 3.10 / 3.11 / 3.12（不要 3.13+，部分老包兼容性差）。

---

## 环境隔离（强烈建议 venv）

**为什么**：赛前一周装的 `pandas 2.0`，赛题要用 `pandas 2.2` 的新 feature → 全局升级破坏以前的脚本；
两支队伍在同一个目录下抢包 → 互相覆盖。建议**每个赛题目录一个 venv**。

```powershell
# 1) 在当前赛题目录下创建 venv（一次性）
python -m venv .venv

# 2) 激活 venv（每次新开终端都要做）
.\.venv\Scripts\Activate.ps1
# 激活后命令行前缀会变成 (.venv) PS ...，证明已隔离

# 3) 在 venv 里装包（用 python -m pip 不用 pip，更稳）
python -m pip install --upgrade pip
python -m pip install pandas numpy scipy matplotlib openpyxl PyMuPDF pulp
```

**赛前 1 天**必做：按上面装好并 `python -c "import 全部包"` 验证一次。**封闭网络环境**见
下方必装依赖的「离线装包」段。

---

## 必装依赖

```bash
# 核心（必装）
pip install pandas numpy scipy matplotlib openpyxl PyMuPDF

# 优化（强烈建议，C 题/规划类题用）
pip install pulp  # ILP 求解器

# 可选（视觉/数据科学增强）
pip install seaborn plotly scikit-learn
```

**踩坑案例**（2024 C 题测试）：没装 `pulp` → 重茬约束解不了；用 `scipy.optimize.linprog` 降级为 LP 版，流程跑通但解不是最优。

**离线/限网环境**（封闭赛场常见）：

> **赛前 1 天必做 2 件事**（开赛当晚就来不及了）：
> 1. 切清华镜像（速度 + 防墙）
> 2. 预下载全部 wheel 包到本地，验证 `python -c "import pandas, ..."` 全通

```powershell
# 1) 切清华镜像（速度 + 防墙）
python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 2) 赛前提前下好 wheel 包（断网时离线安装）
python -m pip download -d ./pkgs pandas numpy scipy matplotlib openpyxl PyMuPDF pulp
# 比赛时: python -m pip install --no-index --find-links=./pkgs 全部包名

# 3) 验证可 import（赛前 1 天跑一次，出 7 行 OK 就放心）
python -c "import pandas, numpy, scipy, matplotlib, openpyxl, fitz, pulp; print('core ok')"
```

**封闭赛场预下载建议**：把 pandas / numpy / scipy / matplotlib / openpyxl / PyMuPDF / pulp / seaborn 全下到 `pkgs/` 目录，断网时一次性 `pip install --no-index --find-links=./pkgs` 装回来。

**踩坑案例**（2024 C 题测试）：开赛当晚才知道赛场断网，`pip install` 拉不下 PyMuPDF 几 MB 的 wheel，整支队伍一夜没装上包。**赛前 1 天预下载 + 验证是必须项**。

---

## Procedure（状态机式流程）

按以下 **5 步**走，每步都有明确的"输入 → 动作 → 输出 → 下一状态"。**不要跳步**。

```
┌─ Step 0: 读取输入 ──────────────────────────────────────┐
│  输入: 题目/*.pdf, 数据/*.xlsx/csv                      │
│  动作: PDF 读题 + xlsx 解析 + 题组判定                  │
│  输出: 求解/求解计划.md (题组/题号/问题数/数据概况)     │
│  → 跳到 Step 1                                           │
└──────────────────────────────────────────────────────────┘
                          ↓
┌─ Step 1: 求解计划（先比选方案，再写完整计划）─────────┐
│  输入: 问题列表 (从 Step 0 输出)                         │
│  动作: 为每个问题列候选模型对比表, **等用户选方案**     │
│  输出: 用户选定方案 → 求解/求解计划.md (详细思路+参数)   │
│  → 用户选完后跳到 Step 2                                 │
└──────────────────────────────────────────────────────────┘
                          ↓
┌─ Step 2: 逐题求解 ──────────────────────────────────────┐
│  输入: 选定方案                                          │
│  动作: 每个问题一个 py 文件                              │
│  输出: 求解/问题X/问题X_xxx.py + 图片/*.png + 结果/*.csv │
│  → 全部问题跑完后跳到 Step 3                            │
└──────────────────────────────────────────────────────────┘
                          ↓
┌─ Step 3: 写论文 ─────────────────────────────────────────┐
│  输入: 求解结果 (问题/图片/CSV)                          │
│  动作: 10 章论文结构 (摘要/引言/总体分析/模型假设/符号/ │
│        建模与求解/模型检验/模型评价/改进推广/参考文献/附录)│
│  输出: 论文/0-10 章.tex + 论文.tex 主入口                │
│  → 写完后跳到 Step 4                                    │
└──────────────────────────────────────────────────────────┘
                          ↓
┌─ Step 4: 编译 + 终态（合并自原 Step 5 + Step 5.5）─────┐
│  动作 1: xelatex 编译论文版 × 2 + 电子版 × 2            │
│  动作 2: 跑合规检查命令 (references/合规检查清单.md §2) │
│  动作 3: 打包 支撑材料.rar (≤ 20 MB)                   │
│  动作 4: 最终提交物检查 (论文版 + 电子版 + 支撑材料)    │
│  输出: 论文.pdf + 电子版.pdf + 支撑材料.rar             │
│  → 完成                                                   │
└──────────────────────────────────────────────────────────┘
```

**详细执行步骤**见下面各小节。

### Step 0：读取输入

- 读 `题目/` 下所有 PDF/DOCX，提取问题描述
- **判定题组与题号**（国赛选题规则）：本科组 = A/B/C 任选；高职高专组 = D/E 任选。从题面
  关键词或题目编号判定，**错选题组直接判 0 分**。记录到 `求解/求解计划.md` 顶部。
- 读 `数据/` 下所有 xlsx/docx/csv，**全量读取**，检查：列数一致性、数据类型、合并单元格、多级表头、隐藏 sheet
- 打印数据总览（shape / dtypes / 缺失率），识别问题数量 N
- **用 `references/scripts/profile_data.py` 跑 EDA**（借鉴自 scipilot，自动检测列类型/分布/相关性/初步图型）

**⚠️ 读题/读数据失败回退表**（按症状照做，赛前一晚就备好依赖）：

| 症状 | 原因 | 回退操作 |
|------|------|----------|
| PyMuPDF 读出来是图片/空白 | 扫描件 PDF（图像无文本层） | `pip install pytesseract` + 装 tesseract-ocr；或转 Word/带文本层的 PDF |
| PyMuPDF 报 `file has been encrypted` | 加密 PDF | 打开看是否空密码能解；不能解就联系组委会 |
| `pd.read_excel('data/xxx.xls')` 报格式错误 | 老 .xls | 装 `xlrd<2.0` 后用 `pd.read_excel(..., engine='xlrd')` |
| `pd.read_docx('题目/xxx.doc')` 报格式错 | 老 .doc 不是 .docx | Word 打开 → 另存为 .docx |
| 打开 xlsx 有"受保护视图"提示 | Excel 标记可疑文件 | 打开 → 启用编辑 → 重新保存（**不要在受保护状态下跑脚本**） |
| 装包超时 / ConnectionError | 离线/限网赛场 | 赛前 1 天预下载：`pip download -d ./pkgs pandas numpy scipy matplotlib openpyxl PyMuPDF pulp` |

### Step 1：求解计划（先比选，再写完整计划）

读题后**不要**直接写完整计划。先为每个问题列候选模型对比表，等用户选方案。

候选模型池：

| 问题类型 | 候选模型 |
|----------|---------|
| 优化 | 线性/整数规划、GA、PSO、SA、ACO |
| 评价 | 熵权法、AHP、TOPSIS、模糊综合、CRITIC、灰色关联 |
| 预测 | ARIMA、随机森林、XGBoost、LSTM、GM(1,1)、多元回归 |
| 分类 | 逻辑回归、SVM、随机森林、KNN、朴素贝叶斯、CNN |
| 机理 | 微分方程、动力学建模、元胞自动机、Agent-Based |

强制要求（避免扣分项）：

- 有数据的题：≥ 1 个机器学习/统计模型 + ≥ 1 个传统机理模型
- 优化题：≥ 1 个精确算法 + ≥ 1 个启发式算法
- 评价题：≥ 1 个主观赋权（AHP）+ ≥ 1 个客观赋权（熵权/CRITIC）

**用户选定方案后**再写 `求解/求解计划.md`，按选定方案细化求解思路和参数。

### Step 2：逐题求解

- 创建 `求解/问题X/图片/` 和 `求解/问题X/结果/`
- 每个问题一个 py 文件（中文命名）
- **先算后画**：计算 → 打印 min/max/mean/std → 再画图
- 每题 ≥ 4-6 张图
- 问题 1 输出 `求解/预处理数据.csv` 供后续共用
- **灵敏度分析前置**：求解阶段就测关键参数影响
- 脚本报错→修复→重跑，通过再下一问
- 代码模板见 `references/code-template.py`（数据驱动题）或 `references/mechanism-template.py`（机理题）

**📋 求解 → 论文 衔接清单**（C1，每张图必须标清楚"论文哪节用"）：

每张 PNG 在 `求解/问题X/图片/README.md` 写一行说明：

```markdown
# 问题X 图片清单

| PNG 文件名 | 论文哪一节用 | 说明什么 |
|-----------|-------------|----------|
| 问题X_龙头轨迹.png | §5.X.1 分析 | t=0..300 龙头位置演化 |
| 问题X_速度验证.png | §6 模型检验 | 龙头速度解析解 vs 数值解 |
| 问题X_灵敏度分析.png | §6 模型检验 | PITCH ±20% 对终止时刻的影响 |
```

**论文节段引用规则**（避免图与文字脱节）：

- **5.X.1 分析节** → 引用「数据分布图 + 算法流程图 + 物理模型示意图」
- **5.X.2 建模节** → 引用「求解结果图 + 收敛曲线 + 参数演化图」
- **6 模型检验** → 引用「误差图 + 灵敏度图 + 交叉验证图」
- **7 模型评价 / 8 改进推广** → 可选引用「方案对比图 + 改进前后对比图」

**写论文时**：打开 `求解/问题X/图片/README.md` 查"哪张图放哪节"，**避免图与文字脱节**（评审扣分重灾区）。

### Step 2.Gate：每问跑完必勾（门控检查，不勾完不能进 Step 3）

> **踩坑教训**（2024 A 题测试）：这 8 项只作为占位，跑完 5 个问题后**没回填**，结果发现
> 问题 2 复用了问题 1 的"碰撞距离阈值"但没显式声明；问题 4 的"调头半径 r1=4.5"是拍脑袋的值，
> 没和"问题 3 的最小螺距"联动。**强制**：每写完一个问题的代码，必须在
> `求解/求解计划.md` 末尾的"自检"区逐项回填，**不回填不算完成该问题**。

```
Step 2.Gate（每问跑完必勾）:

□ 8 项整篇一致性自检已回填到 求解/求解计划.md 末尾（详 workflow.md §1c）
□ 5 个踩坑检查已勾：
  □ 跨问题参数复用一致？(如 p, L, d 跨问同值)
  □ 后问输入是前问输出？(声明清楚)
  □ 硬约束能程序化验证？(如不碰撞 → min_sep ≥ 板宽)
  □ 每个最优/预测结果独立验证？(手算/解析解)
  □ 每个输出表/文件按题面列表生成？(result1/2/4 全到位)
□ 至少 4-6 张图，每张在 求解/问题X/图片/README.md 标注「论文哪一节用」
□ result 文件名保留国赛附件原名（result1.xlsx 不要改成 my_result1.xlsx）
□ 跨问题物理常量在 求解/共享/constants.py 已定义？(没有就新建)
```

**📦 跨问题常量强制规范**（C4，详 `references/导入规范.md §8`）：

- 物理常量（板长、螺距、重力加速度）→ **只用大写下划线** `PITCH = 0.55`，放 `求解/共享/constants.py`
- 跨问题参数（前问估出、后问复用）→ 放 `求解/共享/params.py`，按估出问题号归档
- **禁止**问题代码内重定义 `PITCH` / `pitch` / `p` 三种名字指代同一个量（评审标"模型不严谨"）
- 每问跑完反问 3 条：
  1. 本问的物理常量**是否在共享 constants.py 已定义**？
  2. 本问的"前问输出"参数（如 p_min / t_collision）**是否在共享 params.py 已记录**？
  3. 本问的变量名跟其他问题**命名一致**？

**全部勾完才能 next**。如果某项不勾，意味着这一问有未解决的硬问题，下一问会踩同样的坑。

### Step 3：写论文

**Step 3 起手必做 2 件**（漏写就 0 分，2026 规范硬性要求）：

1. **AI 工具使用声明**（位置：`论文/9.0.AI工具使用声明.tex`，紧邻参考文献之前）
2. **附录两段固定说明**（位置：`论文/10.0.附录固定说明.tex`，附录 1 程序 + 附录 2 支撑材料）

> 详细二选一模板 + 6 项 AI 必查 + 评审扣分点 → 见 `references/合规检查清单.md §1.3`（AI 工具类）。

每问拆两个子文件：

- `5.X.1.分析与准备.tex`：三段式分析 + 9 框流程图 + 数据预处理（仅问题1）+ 算法选择对比表
- `5.X.2.建模与求解.tex`：模型建立（步骤式推导）+ 模型求解（结果表+图+分析）

**📌 5.X.2 「结果表」与 `resultX.xlsx` 一致性**（评审对比会标"数据不可信"）：

> 数字必须与 `求解/问题X/结果/resultX.xlsx` 完全一致 — **禁止手抄**。

```latex
% 5.X.2.建模与求解.tex 内的"结果表" longtable 段
% ⚠️ 数字必须与 求解/问题X/结果/resultX.xlsx 一致
% 推荐做法: Python 读 resultX.xlsx → 抽关键行列 → to_latex() 生成
%           复制到下面 longtable 的 & 数字 & 段(不要手抄)
\begin{longtable}{>{\centering\arraybackslash}p{0.12\textwidth}...}
  \caption{问题X 求解结果}
  \label{tab:resultX} \\
  \toprule
  时刻 & 龙头 x & 龙头 y & 板数 \\
  \midrule
  ... % ← from df.to_latex(index=False)
  \bottomrule
\end{longtable}
```

**AI 内联标注规范**（D3，2026 AI 规定第 5 条，漏标会被取消评奖）：

- 章节头声明 / 公式脚注 / 图片 caption 后标注 / 段落标记
- 严格：只标确实由 AI 生成的，不要为了"显得用了 AI"乱标
- 完整 4 条规则 + 3 类禁用场景 → 见 `references/合规检查清单.md §1.3` + `§3 禁用场景`

详细 10 章规范见 `references/paper-spec.md`（含全文统一符号表 + 8 项自检）。

写完后**不要**直接编译，先做**符号一致性自检**（8 项，详见 `references/paper-spec.md §4.0`）。

### Step 4：编译 + 终态（合并自原 Step 5 + Step 5.5）

**🧹 编译前先清理**（A3，96 小时赛场的 C 盘空间管理）：

```powershell
# 每次 xelatex 编译会产生 .aux/.log/.synctex.gz 临时文件，跑 5+ 次会堆 50+ 个
# 正式编译前清一次（这些已在 .gitignore，不影响提交）
Remove-Item 论文\*.aux, 论文\*.log, 论文\*.synctex.gz, 论文\*.toc, 论文\*.out -ErrorAction SilentlyContinue
```

**赛前 1 天**自检清单加一条：**预留 ≥ 5 GB 工作空间**

- 求解/ 中间 PNG + xlsx ≈ 100-500 MB
- 论文/ 编译 5+ 次临时文件 ≈ 50-100 MB
- 支撑材料.rar 副本（重打包 3 次会堆 100MB+）≈ 300 MB
- 提交后剩余空间留 ≥ 4 GB 给系统应急

**Step 4.1: 编译论文版 + 电子版**

**为什么 xelatex 跑 ×2？**
- 第 1 次解析 `\ref` / `\cite` / `\pageref` / 目录占位 → 第 2 次把这些填到正确页码
- longtable 续表头需 2 次才能定位（首页 + 跨页续表头）
- 跟主论文共用 format.cls 的 `AI工具使用详情.pdf` 也按同样规则 ×2

**判断还要不要再编**：看 `.log` 末尾
- 出现 `Rerun` → 再编 1 次（属于正常 2 次流程）
- 出现 `! Error` → 改 LaTeX，不是再编几次能解决的
- 出现 `Overfull \hbox` 警告 → 排版问题，不影响编译成功，但会扣分（Step 4.2 处理）

```powershell
Set-Location 论文
# 论文版（含承诺书+编号页）
xelatex -interaction=nonstopmode 论文.tex
xelatex -interaction=nonstopmode 论文.tex

# 电子版（不含承诺书+编号页，第一页直接是摘要页）
xelatex -interaction=nonstopmode 电子版.tex
xelatex -interaction=nonstopmode 电子版.tex

# AI 工具使用详情在 Step 4.4 子步骤 1 编译（需先填写 5 节占位符）
```

**Step 4.2: 排版优化**（循环直到日志干净）

```bash
# 看警告
grep 'Overfull\|Underfull\|Float too large' 论文.log

# 修复：调整列宽比例 / 改换行位置
# 2 次修不好允许 \\newline 或 \\sloppy
```

**Step 4.3: 跑合规检查命令**（一键验证）

→ 详见 `references/合规检查清单.md §2 一键验证命令`

**Step 4.4: 打包支撑材料**

**子步骤 1: 填写并编译 AI 工具使用详情**（如果用了 AI）

```powershell
# 1) 填写 LaTeX 模板（人工）
#    打开 论文/AI工具使用详情.tex，按 5 节填写占位符：
#    工具信息 / 使用目的 / prompt 摘要 / 核验情况 / 禁用场景声明

# 2) 编译成 PDF（跟主论文共用 format.cls，排版一致）
Set-Location 论文
xelatex -interaction=nonstopmode AI工具使用详情.tex
xelatex -interaction=nonstopmode AI工具使用详情.tex
#    输出: 论文/AI工具使用详情.pdf (≈5 页)

# 3) 复制到支撑材料
Copy-Item AI工具使用详情.pdf ..\支撑材料\AI工具使用详情.pdf -Force
```

**子步骤 2: 打包**

**📦 打包工具选型**（三种任选，**优先 WinRAR / 7z**）：

| 工具 | 命令 | 输出 | 推荐度 |
|------|------|------|--------|
| **WinRAR CLI**（国赛常见） | `"C:\Program Files\WinRAR\rar.exe" a 支撑材料.rar 求解\*` | `.rar` | ⭐⭐⭐⭐⭐ |
| **7-Zip CLI**（开源） | `& "C:\Program Files\7-Zip\7z.exe" a 支撑材料.rar 求解\*` | `.rar` | ⭐⭐⭐⭐ |
| PowerShell `Compress-Archive` | `Compress-Archive -Path 求解\* -DestinationPath 支撑材料.rar -Force` | `.zip`（**不是真 .rar**） | ⭐⭐ 兜底用 |

> 2026 规范后缀 `.rar` / `.zip` 都行，但各省系统支持不一，**优先 `.rar`**。
> **赛前 1 天**必做：确认本机 WinRAR 或 7z 已装好且命令行可调（跑 `rar` / `7z` 看版本号）。

```powershell
# 1) 把整个 求解/ 目录打包成 支撑材料.rar
#    优先用 WinRAR CLI（生成真 .rar），否则用 Compress-Archive 生成 .zip
& "C:\Program Files\WinRAR\rar.exe" a 支撑材料.rar 求解\*
# 兜底: Compress-Archive -Path 求解\* -DestinationPath 支撑材料.rar -Force

# 2) 用了 AI 的话，把 AI工具使用详情.pdf 放进压缩包
if (Test-Path "支撑材料\AI工具使用详情.pdf") {
  & "C:\Program Files\WinRAR\rar.exe" a 支撑材料.rar "支撑材料\AI工具使用详情.pdf"
}

# 3) 检查大小（必须 ≤ 20MB，否则报错）
$sizeMB = [math]::Round((Get-Item 支撑材料.rar).Length / 1MB, 2)
Write-Host "支撑材料.rar: $sizeMB MB"
if ($sizeMB -gt 20) { Write-Error "超过 20MB 限制！" }
```

**模板位置**: `论文/AI工具使用详情.tex`（含 5 节固定结构 + 跟主论文共用 format.cls）
**编译命令**: `xelatex -interaction=nonstopmode AI工具使用详情.tex` (×2)

**Step 4.5: 最终提交物检查**

3 个文件硬要求（详 `references/合规检查清单.md §5`）：
- `论文/论文.pdf` — 纸质版（含承诺书 + 编号页）
- `论文/电子版.pdf` — 电子版（≤ 20MB，不放承诺书/编号页）
- `支撑材料.rar` — 全部源码+数据集+中间图，≤ 20MB；用了 AI 必含 `AI工具使用详情.pdf`

**不放**：承诺书 / 编号页 / 参赛队/学校/赛区信息（2026 规范第十一条硬性要求）。

---

## 合规与硬规则

**完整硬规则 + AI 合规 + 纪律红线**在 `references/合规检查清单.md`（不再在主文档里堆 100 行）。**写完论文后**逐项打勾 + 跑 §2 验证命令。

**核心 3 条不要忘**（最高频违规）：

1. **公式必须用公式编辑器**（不要截图，评审无法识别/检索）
2. **AI 工具使用声明放参考文献之前**（不是附录）
3. **AI 工具使用详情.pdf 放支撑材料**（不是附录）

完整内容：见 `references/合规检查清单.md`。

---

## Output contract

每个竞赛任务交付（与 Step 4.5 提交物一致）：

- `论文/论文.pdf` — 纸质版（含承诺书+编号页）
- `论文/电子版.pdf` — 电子版（不放承诺书/编号页）
- `支撑材料.rar` — 全部源码+数据集+中间图，≤ 20MB
- `支撑材料/AI工具使用详情.pdf` — 用 AI 必填（2026 AI 规定第 4 条）

中间产物（不提交但要保留）：见 `README.md` 目录结构段。

---

## 跑题期间红线（参赛规则第 3/5 条）

> 完整 8 条禁止/允许行为表 + 严重违规后果（取消评奖 + 指导教师 2 年禁赛）→ 见 `references/合规检查清单.md §4`

---

## Failure handling

- **数据缺失>20%**：KNN 插补或删除该特征，不静默丢
- **XGBoost/GBR 过拟合**：降低 max_depth、增加正则化参数
- **预测值异常**：检查特征是否存在数据泄露
- **交叉验证方差过大**：增加折数或采用重复 CV
- **LaTeX 编译 Error**：先 grep 看具体错，针对修；连续 2 次失败切换策略（改 `\caption` 转义 / 检查字体路径）
- **Overfull/Underfull warning**：调整列宽比例 / 改换行位置；2 次修不好允许 `\\newline` 或 `\\sloppy`

---

## Templates inside this skill

完整目录结构 + 各文件用途见 **`README.md` 目录结构段**（与本文档保持同步，README.md 是单一权威源）。

## 赛前学习清单

正式开赛前，按 `references/赛前学习清单.md` 准备：

- **§二 题型映射表** — 6 大题型的优先算法 + 备选 + 评奖加分项
- **§三 算法清单** — 经典（A1-A4，共 30+ 算法）+ 现代（B1-B3，含启发式 + 机器学习）
- **§四 备赛路径** — 60/30/7 天三档速成（按可投入时间选一档）
- **§五 跑题期间红线** — 2026 参赛规则第 3、4、5 条对应的**具体禁止行为**
- **§六 参考资源** — zhanwen/MathModel 等公开仓库的**赛前/跑题边界**标注
- **§七 自检清单** — 赛前 1 周 / 赛前 1 天 / 开赛第 1 小时三次复检

**核心 10 算法**（覆盖 80% 题型，30 天档必学）：线性规划/整数规划、动态规划、蒙特卡洛、
AHP+熵权法组合定权、TOPSIS、灰色预测 GM(1,1)、ARIMA、随机森林/XGBoost、LSTM、
遗传算法/粒子群（任选其一）。
