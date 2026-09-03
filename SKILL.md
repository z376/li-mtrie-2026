---
name: li-mtrie
description: |
  数学建模竞赛（国赛/美赛/MCM/ICM/CUMCM）端到端 skill。Use when the user pastes 数模赛题 PDF
  并说"开始求解"/"跑题"/"做数模"，OR 求解后说"生成论文"/"出论文 PDF"，OR 验证本 skill 自身
  ("smoke test"/"跑 test_run")。

  Do NOT use for: general data analysis, one-off Python scripts, or research questions
  that don't lead to a `论文.pdf` deliverable.
metadata:
  version: "1.5.2"
  category: competition-workflow
  scope: user
  source_workspace: D:/MiniMax code/1/数建Skill模板
  spec_compliance: "全国大学生数学建模竞赛论文格式规范（2026年修订稿，2026-09-01起试行）+ 全国大学生数学建模竞赛人工智能工具使用规定（2026年试行）"
  history:
    - 1.5.2: fix(scripts) 兼容 PyMuPDF ≥1.24 的 fitz deprecate — verify_pdf_metrics.py + visual_qa.py 改 try/except 双 import
    - 1.5.1: 借鉴 BZD 数模社 bzd-model-dictionary + bzd-paper-format-checker + bzd-review-paper v1.0 — 新增 3 个 references (模型字典使用指南 / 格式自查清单 / 百分制评审方法) + 1 个 LLM 工具 04 百分制评审 (3 模式 M1/M2/M3); 追加 refactor P0+P1+P2 13 项 (审计 6.83→7.5/10)
    - 1.5.0: 新增 LLM 工具集成 (3 个结构化 prompt 工具) — 学生自用
    - 1.4.4: 借鉴 6 个外部 skill (数模陪跑独家 + cumcm-live-workflow + aigc-reduce + scipilot-figure + bzd-modeling-ideas + mma v3.3)
---

# Math Modeling

数学建模竞赛（国赛/美赛/校赛）端到端解题 + 论文写作工作流。基于 2024 高教社杯 5 篇
获奖论文（B159/B195/B196/D039 + 南科大板凳龙国一）的结构归纳，并按 2026 年全国组委会
修订的论文格式规范（2026 年修订稿）+《人工智能工具使用规定（2026 年试行）》做了对齐更新。

**本 skill 所有 step 完成判据遵循 `checkable` 原则** — 完成状态由 1 行命令或 1 次肉眼扫描验证为 **绿/红** 二元, 不接受"应该差不多了"。红 = 立即停下修, 绿 = 跳下一步。

**5 篇参考论文速查** → 详 `references/获奖论文/` 目录:
- B159 / B195 / B196 / D039（数据驱动题为主, 4 篇归纳的 10 章结构基线）
- 板凳龙-南科大-2024 国一（机理题, 极坐标+运动学+碰撞, 见 `板凳龙-南科大-2024国一.md`）

## 规范版本兼容

本 skill 默认按 **2026 规范** 实现（`全国大学生数学建模竞赛论文格式规范（2026 年修订稿）` + `人工智能工具使用规定（2026 年试行）`）。

| 规范版本 | 适配情况 | 关键差异点 |
|---------|---------|-----------|
| **2026（默认）** | ✅ 完全适配 | 摘要中文、≤30 页（含正文+AI 声明+参考文献）、附录两段固定说明、AI 声明在参考文献之前、详情 PDF 在支撑材料 |
| 2024（上一版） | ⚠️ 部分适配 | 摘要可中英、≤35 页、AI 工具相关要求未规定 |
| 2027+（新规出台时） | ⚠️ 待重新验证 | 跑题前用 `references/合规检查清单.md` §1 重新确认, 重点看 §1.3 AI + §1.4 纪律 |

**跨版本使用检查清单**：
1. 打开 `references/合规检查清单.md` §1，对照规范版本逐项打勾
2. 重点看 §1.3（AI 工具类）和 §1.4（纪律类）—— 这两块近 2 年变化大
3. LaTeX 模板的 `论文/format.cls` 一般无需改（`\geometry` 边距等参数 2024/2026 一致）
4. **页数限制变了立刻改**（2024 是 ≤35 页，2026 是 ≤30 页）
5. 跑 `references/合规检查清单.md §2 一键验证命令` 跑一遍

**2026-08-26 官方答疑**（新增，详 `references/2026官方答疑/20260826-咨询问题解答.md`）：
1. **正文 30 页 = 正文主体 + AI 声明 + 参考文献**（不包括摘要/附录/承诺书/编号页）
2. **参考文献不必列 AI 工具**（Q2 官方确认）
3. **附录首页应是支撑材料清单**（file list, 评审快速定位）
4. **AI 声明不需要单独开一页**（紧随排版）
5. **不自行查重/AIGC**（官方答疑 Q5：避免内容泄露与知识产权风险）

**老赛题（2024 及更早）兼容模式**：用 `v1.0 上一版`（如有归档）或删掉 §1.3 全部 AI 声明 + 详情 PDF。

## Inputs to collect

开始前确认三件事（**没准备好就停下来等用户**）：

1. **赛题 PDF** → 用户是否已放进 `题目/` 目录
2. **数据文件** → 用户是否已放进 `数据/` 目录（xlsx / csv / docx）
3. **建模类型** → 用户是否已知问题类型（优化/评价/预测/分类/机理）

如果用户只说"开始求解"而没放题/数据，**必须**先停下来等用户放好再启动。

## Python 环境（开赛第 1 小时必做, 赛前 1 天必验证）

**checkable 红/绿 锚定**: 本节所有步骤完成状态由 1 行命令验证。**绿 = 1 行 `core ok` 输出**, **红 = 任何 import 失败或 pip/python 不一致**。

**Why 5 分钟排查 = 1 行提前验证**: Windows 上常同时存在多个 Python (微软商店版 / Anaconda / 系统版 / VS Code 选中版), `pip install` 装到 A 解释器, Jupyter 用 B → `import pulp` 仍 `ModuleNotFoundError`. **3 步全过 = 绿**:

```powershell
# Step 1: 解释器一致 (1 行)
python -c "import sys; print(sys.executable)"

# Step 2: pip/python 同源 (1 行)
python -m pip --version

# Step 3: import 验证 (1 行 = 绿)
python -c "import pandas, numpy, scipy, matplotlib, openpyxl, fitz, pulp; print('core ok')"
```

**推荐 Python**: 3.10 / 3.11 / 3.12 (3.13+ 部分老包兼容性差).

**venv 隔离** (强烈建议, 每赛题目录一个):
```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
# 激活后命令行前缀变 (.venv) PS ... = 隔离绿
```

**装包命令** (核心 + 优化, 缺 pulp → C 题规划类解不了):
```bash
pip install pandas numpy scipy matplotlib openpyxl PyMuPDF pulp
# 可选: pip install seaborn plotly scikit-learn
```

**封闭赛场预下载** (赛前 1 天必做, 开赛当晚来不及):
```powershell
python -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
python -m pip download -d ./pkgs pandas numpy scipy matplotlib openpyxl PyMuPDF pulp
# 比赛时: python -m pip install --no-index --find-links=./pkgs <pkgs>
```

**checkable 绿 (赛前 1 天跑一次)**: `python -c "import pandas, numpy, scipy, matplotlib, openpyxl, fitz, pulp; print('core ok')"` → 输出 `core ok` = **绿**, 无输出 / ImportError = **红** (开赛当晚才修 = 灾难).

**踩坑案例** (2024 C 题测试): 没装 pulp → 重茬约束解不了; 赛场断网 PyMuPDF wheel 拉不下 = 一夜没装上包.

---

## Procedure（状态机式流程）

按以下 **5 步**走，每步都有明确的"输入 → 动作 → 输出 → 下一状态"。**跳步 = 漏判据，下一问踩坑**。

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
│  绿: 每个问题 1 个选定方案, user 用 `1`/`2`/`3`/`OK` 确认 │
│  → 全选完跳到 Step 2 (否则卡死, 不进 Step 2)            │
└──────────────────────────────────────────────────────────┘
                          ↓
┌─ Step 2: 逐题求解 ──────────────────────────────────────┐
│  输入: 选定方案                                          │
│  动作: 每个问题一个 py 文件                              │
│  输出: 求解/问题X/问题X_xxx.py + 图片/*.png + 结果/*.csv │
│  绿: 每个问题 Step 2.Gate 8 项全勾 (详 paper-spec.md §2 8 项自检)│
│  → 全绿跳到 Step 3 (否则卡死, 不进 Step 3)              │
└──────────────────────────────────────────────────────────┘
                          ↓
┌─ Step 3: 写论文 ─────────────────────────────────────────┐
│  输入: 求解结果 (问题/图片/CSV)                          │
│  动作: 10 章论文结构 (摘要/引言/总体分析/模型假设/符号/ │
│        建模与求解/模型检验/模型评价/改进推广/参考文献/附录)│
│  输出: 论文/0-10 章.tex + 论文.tex 主入口                │
│  checkable 绿: 11 个章节 .tex 全存在 + 每个 ≥ 30 行       │
│       + AI 工具使用声明二者择一已选                       │
│       + 附录固定说明两段已填 + 论文.tex 主入口存在         │
│  → 全绿跳到 Step 4                                       │
└──────────────────────────────────────────────────────────┘
                          ↓
┌─ Step 4: 编译 + 终态（合并自原 Step 5 + Step 5.5）─────┐
│  动作 1: xelatex 编译论文版 × 2 + 电子版 × 2            │
│  动作 2: 跑合规检查命令 (references/合规检查清单.md §2) │
│  动作 3: 打包 支撑材料.rar (≤ 20 MB)                   │
│  动作 4: 最终提交物检查 (论文版 + 电子版 + 支撑材料)    │
│  绿: 4 份 log 中 `! Error` 数 = 0, `Overfull \hbox` < 5, │
│      合规检查清单 §2 7 项全过, 3 个交付文件存在且 ≤ 20MB│
│  输出: 论文.pdf + 电子版.pdf + 支撑材料.rar             │
│  → sign-off (全绿 = 可交卷, 缺任一项 = 红 = 立即修)     │
└──────────────────────────────────────────────────────────┘
```

**sign-off 锚定**: Step 4 绿 = 全 skill 5 步状态机可闭环, 学生/团队可交卷. **sign-off 之前 = 仍在开发态**, 任何"差不多"都是红. 详见 `references/验收清单.md` 终审段.

**详细执行步骤**见下面各小节。

### Step 0：读取输入

- 读 `题目/` 下所有 PDF/DOCX，提取问题描述
- **判定题组与题号**（国赛选题规则）：本科组 = A/B/C 任选；高职高专组 = D/E 任选。从题面
  关键词或题目编号判定，**错选题组直接判 0 分**。记录到 `求解/求解计划.md` 顶部。
- 读 `数据/` 下所有 xlsx/docx/csv，**全量读取**，检查：列数一致性、数据类型、合并单元格、多级表头、隐藏 sheet
- 打印数据总览（shape / dtypes / 缺失率），识别问题数量 N
- **用 `references/scripts/profile_data.py` 跑 EDA**（借鉴自 scipilot，自动检测列类型/分布/相关性/初步图型）

**checkable 绿**: 题面文字 ≥ 200 字 + `求解/求解计划.md` 顶部 4 项 (题组/题号/问题数/数据概况) 已填。profile_data.py 跑出报告 = 加分项, 但不是绿门。

**⚠️ 读题/读数据失败回退表**（按症状照做，赛前一晚就备好依赖）：

| 症状 | 原因 | 回退操作 |
|------|------|----------|
| PyMuPDF 读出来是图片/空白 | 扫描件 PDF（图像无文本层） | `pip install pytesseract` + 装 tesseract-ocr；或转 Word/带文本层的 PDF |
| PyMuPDF 报 `file has been encrypted` | 加密 PDF | 打开看是否空密码能解；不能解就联系组委会 |
| `pd.read_excel('data/xxx.xls')` 报格式错误 | 老 .xls | 装 `xlrd<2.0` 后用 `pd.read_excel(..., engine='xlrd')` |
| `pd.read_docx('题目/xxx.doc')` 报格式错 | 老 .doc 不是 .docx | Word 打开 → 另存为 .docx |
| 打开 xlsx 有"受保护视图"提示 | Excel 标记可疑文件 | 打开 → 启用编辑 → 重新保存（受保护状态下跑脚本 = 空数据） |
| 装包超时 / ConnectionError | 离线/限网赛场 | 赛前 1 天预下载：`pip download -d ./pkgs pandas numpy scipy matplotlib openpyxl PyMuPDF pulp` |

### Step 1：求解计划（先比选，再写完整计划）

读题后**先**为每个问题列候选模型对比表，等用户选方案（避免 model mismatch 返工）。

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

### Step 1.5：Tracer bullet 探路（强烈建议, 30 分钟可省 5 小时返工）

**为什么？** 5 个问题逐一求解后才进 Step 3 写论文, 这时若发现 LaTeX 模板错 / 数据格式不兼容 / 共享模块 bug, 整套返工。**tracer bullet**（示踪弹, 借鉴自 *The Practice of Programming*）: **先用问题 1 跑通全流程**, 早暴露问题。

**30 分钟 tracer 流程**:
1. **问题 1 选最简子集求解**（如 1 个数据点, 1 个公式, 1 张图）
2. 跑通 `求解/问题1/问题1_xxx.py`（验证共享模块 + 数据格式）
3. 在 `论文/5.1.*` 写 1 段占位（验证 LaTeX 模板 + 编译）
4. 跑 `xelatex 论文.tex` × 2（验证 format.cls + 思源宋体 + 引用都对）
5. **红/绿判据**:
   - **绿**: 数据读入 + 计算 + 出图 + 论文占位 + 编译 0 error, 全流程 ≤ 30 min → 进 Step 2 全量求解
   - **红**: 任何一环 ≥ 60 min 卡住 → **停下来修**, 别先动其他 4 个问题

**踩坑教训**（2024 C 题测试）: 没跑 tracer, 5 个问题都解完后才发现 `论文/format.cls` 的思源宋体路径写错, 整套重编译 3 小时。

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

### Step 2.Gate：每问跑完必勾（门控检查，全绿才能进 Step 3）

> 8 项整篇一致性自检的**完整清单 + 模板 + 踩坑案例**在 `references/paper-spec.md §2 8 项自检`（权威源, 本节不重复列）。
> 每写完一个问题的代码，必须在 `求解/求解计划.md` 末尾的"自检"区逐项回填，**不全绿 = 该问题未完成**。

**📦 跨问题常量强制规范**（C4，详 `references/导入规范.md §8`）：

- 物理常量（板长、螺距、重力加速度）→ **只用大写下划线** `PITCH = 0.55`，放 `求解/共享/constants.py`
- 跨问题参数（前问估出、后问复用）→ 放 `求解/共享/params.py`，按估出问题号归档
- **统一命名**：问题代码内用同一名字指代同一个量（problem-1 用了 `PITCH`，后续必须用 `PITCH`，别 `pitch` / `p` 混用——评审标"模型不严谨"）
- 每问跑完反问 3 条：
  1. 本问的物理常量**是否在共享 constants.py 已定义**？
  2. 本问的"前问输出"参数（如 p_min / t_collision）**是否在共享 params.py 已记录**？
  3. 本问的变量名跟其他问题**命名一致**？

**全部勾完才能 next**。如果某项不勾，意味着这一问有未解决的硬问题，下一问会踩同样的坑。

### Step 3：写论文

**Step 3 起手必做 2 件**（漏写就 0 分，2026 规范硬性要求）：

1. **AI 工具使用声明**（位置：`论文/9.0.AI工具使用声明.tex`，紧邻参考文献之前）
2. **附录两段固定说明**（位置：`论文/10.0.附录固定说明.tex`，附录 1 程序 + 附录 2 支撑材料）

> AI 工具使用声明 = 1 句话（赛事组委会硬性规定） + 6 项 AI 必查 + 评审扣分点 → 见 `references/合规检查清单.md §1.3`（AI 工具类）。

每问拆两个子文件：

- `5.X.1.分析与准备.tex`：三段式分析 + 9 框流程图 + 数据预处理（仅问题1）+ 算法选择对比表
- `5.X.2.建模与求解.tex`：模型建立（步骤式推导）+ 模型求解（结果表+图+分析）

**📌 5.X.2 「结果表」与 `resultX.xlsx` 一致性**（评审对比会标"数据不可信"）：

> 数字必须与 `求解/问题X/结果/resultX.xlsx` 完全一致 — **从 resultX.xlsx 读出 → to_latex() 生成**（手抄 = 评审扣"数据不可信"分）。

```latex
% 5.X.2.建模与求解.tex 内的"结果表" longtable 段
% 推荐做法: Python 读 resultX.xlsx → 抽关键行列 → to_latex() 生成
%           复制到下面 longtable 的 & 数字 & 段
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
- 严格：只标确实由 AI 生成的（乱标 = 评审反向扣"AI 标注不规范"分）
- 完整 4 条规则 + 3 类禁用场景 → 见 `references/合规检查清单.md §1.3` + `§3 禁用场景`

详细 10 章规范见 `references/paper-spec.md`（含全文统一符号表 + 8 项自检）。

**📌 冲国奖 + 防 AIGC**（写论文时同步看，别等终审才查）：

- **国奖级硬性指标**（6 类数字门槛 + 26 条自查表 6 维度）→ `references/国奖级硬性指标.md`
  - 公式 ≥ 15、表格 ≥ 18、图片 ≥ 10、参考文献 15-25、三类检验齐全、正文 25-30 页
  - 26 条逐条判定（AI 新规 / AI 幻觉 / 建模逻辑 / 求解合理 / 写作规范 / 排版页数）
- **去 AIGC 指南**（降重 4 层法 + 9 类痕迹自查 + 6 类代码特征）→ `references/去AIGC指南.md`
  - **L4 证据/事实**层最有效（补数字、补理由、补边界、补失败方案）
  - 把 AI 从"代写"改成"审稿人"——让 AI 指出问题，队员手动改

**📌 AIGC 防御体系（v1.4.5 起，借鉴 aigc-reduce v1.0）**：

- **4 铁律**（核心 insight）：① 禁止 AI 重写 AI 文本（PaperPure 实测升至 100%）；② 修改率 >40% 但只能靠限定手段；③ 确定性替换不是重写；④ 保持学术语体（硬底线）
- **3 轮协议**（结构化降重流程）：第 1 轮 减法（划禁改 → 扫描 → 词级 → 句级 → 段落）→ 第 2 轮 加法（节奏工程 + 审慎推断 + 具体化）→ 第 3 轮 Anti-AI 审计
- **5 类禁改片段** → `references/受保护片段.md`（引用/公式/数据/术语/引语）
- **4 平台检测弱点** → `references/检测平台弱点.md`（知网 3.0 / PaperPure / 万方 / PaperPass + 3 档修改率）
- **9 维度自动扫描** → `references/scripts/aigc_scan.py`（借鉴 aigc-reduce，含 GBK 兼容 patch）

**📌 绘图避坑体系（v1.4.5 起，借鉴 scipilot-figure-skill）**：

- **18 条可视化陷阱**（均值柱/双Y轴/饼图/Y轴截断/rainbow色图/缺字方框 等）→ `references/绘图避坑.md`（15.8 KB, 详版含审稿人视角 + 代码示例）
- **图型选择决策三轴**（变量数/论证意图/数据规模）→ `references/图型选择决策.md`（11.6 KB, 8 类数据形态分述）
- **速查表** → `references/绘图规范.md §0`（中文化压缩版，每条 1 行）

**📌 整题建模框架（v1.4.5 起，借鉴 bzd-modeling-ideas）**：

- **每道题 4 段式分析**（问题概述 / 总体思路 / 模型比选 / 创新方向）→ 写 `求解/求解计划.md` 时按这 4 段，**直接对应论文 §5.X 章节**
- **5 跨问题架构**（机理→计算→精度 / 描述→估计→预测→决策 / 单例→多主体 / 确定性→不确定→稳健 / 单因素→多因素 / 分类→优化）→ `references/整题建模模式.md`（3.7 KB, 16 道 2020-2025 高教社杯国赛凝练）
- **7 题型路线**（动态优化/物理反演/统计生物/实验数据/规划生产/几何覆盖/分布式信息）+ **6 断链 failures** + **8 验证 routes**（同源）
- **4 段式硬约束 + 创新标准** → `references/策略输出规范.md`（2.8 KB, 反例"使用遗传算法/模型融合/加可视化/堆因素 不算创新"）

**📌 跨题工具 + 验收 + 角色分工（v1.4.5 起，借鉴 mma v3.3）**：

- **3 个跨题 utility** → `references/scripts/data_utils.py`（1.5 KB）
  - `ensure_utf8_stdout()`：GBK console 兼容（emoji 不报错）
  - `read_csv_safe()`：force utf-8-sig 解码，绕开 PowerShell GBK 读 UTF-8 CSV 乱码
  - `save_csv()`：utf-8-sig 写，Excel 直接打开
- **38+ 项验收清单**（Stage 5）→ `references/验收清单.md`（12.9 KB, 6 类：A 编译 / B 数值 / C 硬规则 / D 写作 / E 支撑材料 / F 2026 规范）
- **4 角色 prompt 模板**（建模手/代码手/论文手/验收手）→ `references/角色Prompt.md`（13.5 KB, 团队 4 人分工时直接 copy-paste 角色身份到对话）

**📌 LLM 工具集成（v1.4.5 起，学生自用）**：

- **3 个结构化 prompt 工具**（不调外部 API，copy-paste 到 Mavis/Claude/GPT 即可）：
  - `01-选题推荐.md`：题面 + 数据 → 问题分类 + 候选模型 Top-3 + 数据洞察
  - `02-代码修复.md`：**96 小时救星**——traceback → 根因 + 最小修复 + 验证步骤（debug 30% 时间节约 8-10 小时）
  - `03-自动审稿.md`：5 维评分（机理/数据/写作/创新/排版）+ 改进建议 + AI 痕迹词
- **核心原则**：结构化 JSON 输出 / 不调外部 API / 5 维评分 / 三道防线（diff 必读 / 测试必跑 / 备份必留）
- 完整目录 + 使用流程 + 与 26 条自查表映射 → `references/llm-prompts/README.md`

**📌 题意红线 4 条**（读完题就对照，漏一条 → 终止时刻/临界参数/关键结果整体失真）：

- **用真实几何判据**：物体有宽度/形状 → 建模时用真实几何（不是质点简化）
- 几何初始条件必须用解析公式独立验证（不许只信视觉读图）
- 后问对前问误差高度敏感（每步验证链不断）
- 无官方答案时 5 步自查（解析推导 / 单位自洽 / 边界推演 / 多方法交叉 / 物理事实清单）

→ 完整版 `references/题意红线.md`（4.7 KB）

**📌 PDF 成品结构体检**（终审前必跑，10 秒出结果）：

```powershell
# 体检 4 项: 结构 / 越界 / 匿名 / 关键数字
python references/scripts/verify_pdf_metrics.py 论文/论文.pdf 0.4503 412.47
```

依赖：`pip install PyMuPDF`。脚本自动检查页边距越界、元数据泄露、关键数字出现次数、未定义引用 (`??`)。

写完后**先**做**符号一致性自检**（8 项，详见 `references/paper-spec.md §2 8 项自检`），全绿再编译（漏自检 = 编译时符号错乱返工）。

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

**红/绿判据**（必须全绿才进 Step 4.4 打包）：
- **绿**: `! Error` 数 = 0, `Overfull \hbox` 数 < 5, `Rerun` 标记 ≤ 1 次
- **红**: `! Error` ≥ 1 → 修 LaTeX, 再编多少次也没用; `Overfull` ≥ 5 → 调列宽比例（Step 4.2）
- 用 `Select-String -Path 论文.log -Pattern '! Error|Overfull|Rerun'` 一行出全

```powershell
Set-Location 论文
# 论文版（含承诺书+编号页）
xelatex -interaction=nonstopmode 论文.tex
xelatex -interaction=nonstopmode 论文.tex

# 电子版（不含承诺书+编号页，第一页直接是摘要页）
xelatex -interaction=nonstopmode 电子版.tex
xelatex -interaction=nonstopmode 电子版.tex

# AI 工具使用详情在 Step 4.4 子步骤 1 编译（需先填写 4 节占位符）
```

**Step 4.2: 排版优化**（循环直到日志干净）

**绿/红判据** (必须绿才进 Step 4.3):
- **绿**: `! Error` = 0, `Overfull \hbox` < 5, `Underfull \hbox` < 10
- **红**: `! Error` ≥ 1 → 修 LaTeX; `Overfull` ≥ 5 → 调列宽比例 (paper-spec §4.1 公式 1.04−0.04N)

```powershell
# 一行 grep 警告 (PowerShell)
Select-String -Path 论文.log, 电子版.log -Pattern 'Overfull|Underfull|Float too large'

# 修复：调整列宽比例 / 改换行位置
# 2 次修不好允许 \\newline 或 \\sloppy
```

**Step 4.3: 跑合规检查命令**（一键验证）

→ 详见 `references/合规检查清单.md §2 一键验证命令`

**Step 4.4: 打包支撑材料**

**子步骤 1: 填写并编译 AI 工具使用详情**（如果用了 AI）

```powershell
# 1) 填写 LaTeX 模板（人工）
#    打开 论文/AI工具使用详情.tex，按 4 节填写占位符：
#    工具信息 / 使用目的与环节 / 主要 prompt 与过程 / 对 AI 输出的核验情况

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

**模板位置**: `论文/AI工具使用详情.tex`（含 4 节固定结构 + 跟主论文共用 format.cls）
**编译命令**: `xelatex -interaction=nonstopmode AI工具使用详情.tex` (×2)

**Step 4.5: 最终提交物检查**

3 个文件硬要求（详 `references/合规检查清单.md §5`）：
- `论文/论文.pdf` — 纸质版（含承诺书 + 编号页）
- `论文/电子版.pdf` — 电子版（≤ 20MB，不放承诺书/编号页）
- `支撑材料.rar` — 全部源码+数据集+中间图，≤ 20MB；用了 AI 必含 `AI工具使用详情.pdf`

**不放**：承诺书 / 编号页 / 参赛队/学校/赛区信息（2026 规范第十一条硬性要求）。

---

## Failure handling（求解/编译最常踩的 6 类）

- **数据缺失>20%**：KNN 插补或删除该特征，不静默丢
- **XGBoost/GBR 过拟合**：降低 max_depth、增加正则化参数
- **预测值异常**：检查特征是否存在数据泄露
- **交叉验证方差过大**：增加折数或采用重复 CV
- **LaTeX 编译 Error**：先 `Select-String -Path 论文.log -Pattern '! Error'` 看具体错，针对修；连续 2 次失败切换策略（改 `\caption` 转义 / 检查字体路径）
- **Overfull/Underfull warning**：调整列宽比例 / 改换行位置；2 次修不好允许 `\\newline` 或 `\\sloppy`

---

## 合规与硬规则

**完整硬规则 + AI 合规 + 纪律红线 + 4 类检查表 + 一键验证命令**在 `references/合规检查清单.md`（权威源, 本节不重复列）。**写完论文后**逐项打勾 + 跑 §2 验证命令。

---

## Output contract

每个竞赛任务交付（与 Step 4.5 提交物一致）：

- `论文/论文.pdf` — 纸质版（含承诺书+编号页）
- `论文/电子版.pdf` — 电子版（不放承诺书/编号页）
- `支撑材料.rar` — 全部源码+数据集+中间图，≤ 20MB
- `支撑材料/AI工具使用详情.pdf` — 用 AI 必填（2026 AI 规定第 4 条）

中间产物（不提交但要保留）：见 `README.md` 目录结构段。

---

## 跨平台代码红线（借鉴 cumcm-live-workflow v5.0）

> **附录代码 / 支撑材料 .py 必须跨 Windows / Linux / Overleaf 三平台可运行**

- **路径用正斜杠** `'题号/xxx.py'`：Windows/Linux/Overleaf 通吃。自检命令 `Select-String -Path 求解/**/*.py -Pattern '\\\\'` 必须输出 0 行（实测漏网 62 处是为什么这条必看）
- 提交前自检：
  ```powershell
  # PowerShell 查反斜杠残留
  Select-String -Path 求解/**/*.py -Pattern '\\\\' -CaseSensitive:$false
  # 输出应为 0 行; 出现任何行 = 有反斜杠
  ```
- 附录代码用 `black` 格式化（`pip install black` + `python -m black 求解/**/*.py`），格式化后**重跑验证**功能未破坏
- 附录代码加文件头注释（Python 版本 / 依赖库版本 / 输入文件路径），方便评审 / 复现

跟合规模块的协同:
- `论文/10.附录.tex` 顶部已写"代码完整性铁律 + 文件列表一致性铁律"2 条
- `references/题意红线.md` 第 1 条: 题面物理事实必须建模（避免代码缺关键逻辑）
- `references/国奖级硬性指标.md` §3 自查表第 26 条: 全部路径用正斜杠

---

## 跑题期间红线（参赛规则第 3/5 条）

> 完整 8 条禁止/允许行为表 + 严重违规后果（取消评奖 + 指导教师 2 年禁赛）→ 见 `references/合规检查清单.md §4`

---

## Templates inside this skill

完整目录结构 + 各文件用途见 **`README.md` 目录结构段**（与本文档保持同步，README.md 是单一权威源）。

## 赛前学习清单 (备赛期, 跑题期不加载)

开赛前**一周**看 `references/赛前学习清单.md`（不在跑题 always-loaded 里, 节省 16 KB context）。
覆盖 6 大题型 + 30+ 算法 + 60/30/7 天速成 + 跑题红线 + 自检清单。跑题期间不读。
