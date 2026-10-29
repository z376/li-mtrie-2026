# scripts/ — 程序化自检工具集

> 借鉴自 `scipilot-figure-skill`（MIT 风格脚本）+ cumcm-live-workflow-skill v5.0 `verify_pdf_metrics.py`，改写为数学建模国赛工作流。
> 原作者：[scipilot-figure-skill](https://github.com/scipilot/scipilot-figure-skill)

12 个 Python 脚本 + 2 个 .md，覆盖「画图前数据剖析 → 出图后程序自检 → 提交前格式检查 → 终审前 PDF 体检 → AIGC 9 维度扫描 → 数值台账 → 代理审计 → **65 项 check 一体化 sign-off**」。
**不依赖** skill 系统本身——独立可执行，`pip install pandas matplotlib Pillow numpy PyMuPDF` 后即用。

---

## 0. 脚本速查表 (12 个 .py)

> **权威源**：本表是 `references/scripts/` 的完整索引（v1.7.0 起，SKILL.md 指向本表）。
> 下文 §1-§8 保留 5 个主力脚本的详细用法，其余脚本见本表 + 各脚本 `--help`。

| # | 脚本 | 一句话用途 | 什么时候跑 |
|---|------|-----------|-----------|
| 1 | `dryrun.py` | **65 项 check 一体化 sign-off**（赛前 1 天必跑，0 red 才放行） | 赛前 1 天 + 跑题后 |
| 2 | `bc_check.py` | 表面行能量守恒校验（`dE/dt ÷ 边界通量 ≈ 1`，P0-1 签名 ratio=223） | 机理题求解埋点后 + 跑完出报告 |
| 3 | `fig_sanity.py` | 图形**内容**自检（曲线恒定 / 全 NaN / 残留 `set_title` / U+2080 乱码） | 出图后、编译前 |
| 4 | `check_figure.py` | 提交前图片**格式**合规（DPI ≥ 200 / 禁 JPEG / 字体嵌入） | 打包支撑材料前 |
| 5 | `visual_qa.py` | 出图后版面自检（缺字乱码 / 文字越界 / 刻度重叠） | 每张图 `savefig` 后 |
| 6 | `verify_pdf_metrics.py` | 终审前 PDF 6 项体检（结构 / 越界 / 匿名 / 关键数字 / `??` 引用 / 摘要页） | Step 4 编译完、打包前 |
| 7 | `aigc_scan.py` | AIGC 9 维度自动扫描（段首重复率 / 连接词密度 / n-gram TTR） | 论文写完、降重前 |
| 8 | `number_ledger.py` | 数值台账生成与核对（4 子命令 `init`/`add`/`check`/`show`） | Step 3 写论文时 |
| 9 | `check_meta.py` | `meta.json` 3 件套校验（实测耗时 / 复杂度 / 步长依据） | 求解完、写论文前 |
| 10 | `profile_data.py` | 画图前 EDA（列类型 / 分布 / 相关性 / 初步图型建议） | Step 1.5 探路弹 |
| 11 | `agent_audit.py` | 代理审计 brief 生成（A-H 板块 prompt） | Step 4.6 代理审计 |
| 12 | `data_utils.py` | 3 个跨题 utility（GBK stdout / utf-8-sig CSV 读写） | 任意脚本里 import |

| .md | 用途 |
|-----|------|
| `check_tex_compile.md` | xelatex 编译命令 + 临时文件清理 + 5GB 工作空间清单 |
| `README.md` | 本文件（脚本索引 + 主力脚本详细用法） |

> ⚠️ **格式 vs 内容**：3 与 4 互补不重叠——`check_figure.py` 管**格式**（DPI/格式/字体），`fig_sanity.py` 管**内容**（曲线恒定/全 NaN/双标题）。

---

## 1. `profile_data.py` — 画图前 EDA（数据剖析）

**目的**：在动手画图前，先搞清楚数据长什么样——列类型、缺失率、样本量、
分布形态、异常值、分组结构、相关性。基于这些事实推荐**初步图型**。

**工作流位置**：Step 1.5（数据剖析），在 Step 1 选定模型之后、画图之前。

### 用法

```bash
# CLI
py profile_data.py 数据/结果.csv --group group --group condition
py profile_data.py 数据/结果.csv --json > profile.json

# Python API
from profile_data import profile_data, render_report
info = profile_data("数据/结果.csv", group_cols=["group", "condition"])
print(render_report(info))
```

### 输出内容

- **列类型识别**：continuous / categorical / ordinal / datetime / boolean / text
- **描述统计**：mean / sd / range / skewness / 异常值
- **缺失率**：每列的 missing %
- **分组结构**：每组 n、min/median/max，**小样本自动告警**（n<10 警告，n<3 强警告）
- **相关性矩阵**：Pearson，按 |r| 排序
- **初步图型建议**：基于"数据形态 → 推荐图型"决策树

### 何时不该用

- 数据 < 5 行（统计意义小，直接看）
- 数据是图像/音频/视频（用专门工具）

---

## 2. `visual_qa.py` — 出图后程序自检（自检闭环的机器层）

**目的**：在论文里用图前，自动检查三类问题：
- **缺字乱码**（FAIL）—— 拦截 matplotlib 缺字警告（"missing from font" / "Glyph"）
- **文字越界裁切**（WARN）—— Text 的 window_extent 超出画布
- **刻度标签重叠**（WARN）—— 相邻 tick label 的包围盒相交

**工作流位置**：Step 5（排版优化）末尾，每张图 savefig 后调用。

### 用法

```python
from visual_qa import audit_layout, render_preview
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
# ... 画图 ...
fig.savefig("fig1.pdf")

# 程序自检
issues = audit_layout(fig)
for severity, msg in issues:
    print(f"[{severity}] {msg}")

# 同时渲一张中分辨率 PNG 预览（给 AI 读图复核用）
render_preview(fig, "fig1_preview.png", dpi=150)
```

```bash
# CLI 演示
py visual_qa.py demo

# 单独渲 PNG 预览
py visual_qa.py figs/fig1.png --preview out.png
```

### 设计分工（与 AI 读图互补）

- **程序（这个脚本）**：抓**确定性**问题（缺字、文字越界、刻度重叠）
- **AI 读图**（在 `code-template.py` 末尾的注释里说明）：抓**感知性**问题
  （图例压数据、子图对齐、配色灰度可分、整体观感）

两层串起来才是完整的"出图 → 渲 PNG → 程序自检 + AI 读图 → 回改 → 再看"闭环。

---

## 3. `check_figure.py` — 提交前格式合规检查

**目的**：批量检查图片文件的格式合规性——格式（PDF/SVG vs JPEG）、
DPI（≥ 200）、矢量字体嵌入类型（必须 TrueType/Type 42 而非 Type 3）。
**非破坏性**——只读、不修改原图。

**工作流位置**：Step 5.5（打包支撑材料）前，对 `求解/问题X/图片/` 全量扫描。

### 用法

```bash
# 基础检查（DPI ≥ 200）
py check_figure.py 求解/问题1/图片/*.png

# 严格模式（任意 FAIL 即 exit 2，便于 CI）
py check_figure.py 求解/问题*/图片/*.pdf --strict

# 自定义最小 DPI（默认 200）
py check_figure.py figs/*.pdf --min-dpi 300
```

```python
from check_figure import check_figure, print_report
issues, info = check_figure("fig1.pdf", min_dpi=200)
print_report("fig1.pdf", issues, info)
```

### 输出 severity

- **INFO** —— 提示（如 Pillow 未装）
- **WARN** —— 警告（如未嵌入 DPI 元数据）
- **FAIL** —— 不合格（如 JPEG 用在数据图、DPI < 200、字体嵌入错误）

### 数模国赛标准（调整后）

- **格式**：PDF / PNG 都行；JPEG 拒绝（数模用 JPEG 会被扣印象分）
- **DPI**：≥ 200（论文里 600dpi 印刷级；屏幕看 200dpi 已够）
- **字体嵌入**：矢量图必须 TrueType 嵌入（pdftotext 看 Type42）

---

## 整合到主流程

```
Step 0  读题读数据
Step 1  求解计划（候选模型比选）         ← workflow.md
Step 1.5 数据剖析（本目录 profile_data）  ← NEW
Step 2  逐题求解（code-template.py）
Step 3  写论文（paper-spec.md）
Step 4  编译（xelatex × 2）
Step 5  排版优化（visual_qa 自检）        ← NEW（脚本）
Step 5.5 打包支撑材料（check_figure 检）  ← NEW（脚本）
Step 5.6 终审前 PDF 体检（verify_pdf_metrics 检）  ← NEW（脚本，借鉴 cumcm-live-workflow）
```

---

## 4. `verify_pdf_metrics.py` — 终审前 PDF 成品结构体检

> 借鉴自 cumcm-live-workflow-skill v5.0 `references/scripts/verify_pdf_metrics.py`，适配 li-mtrie 2026 规范 + CUMCMthesis 格式（页边距 2.5 cm）。

**目的**：交付前 10 秒出 4 项体检结果：
- **结构**：每页首行 + 字数 → 摘要是否单页
- **越界**：bbox 检测表格/内容是否越右/左/下边界（2.5 cm）
- **匿名**：PDF 元数据 (author/title/keywords) 应为空
- **关键数字**：compact 去空白匹配（规避字体间距）
- **未定义引用**：LaTeX `??` 标记（需跑第二次 xelatex 稳定交叉引用）
- **摘要页判断**：第 1 页是否只有摘要+关键词（"问题重述"出现 = 摘要溢出）

**工作流位置**：Step 5.5（打包支撑材料）前，对 `论文/论文.pdf` 跑一次。

### 用法

```bash
# 基础体检（不传关键数字）
py verify_pdf_metrics.py 论文/论文.pdf

# 加关键数字检查（论文里必须有这些数字）
py verify_pdf_metrics.py 论文/论文.pdf 0.4503 412.47 8.25

# 退出码：0=通过, 1=有问题
```

### 输出示例

```
页数: 20

[1] 结构 (每页首行 + 字数)
  p1: 烟幕干扰弹的投放策略 | 1024字符 <- 摘要页
  p2: 一、问题重述 | 856字符
  ...

[2] 越界检测 (max_x > 右边距 = 2.5cm)
  ✓ 全部页内容在 2.5cm 边距内

[3] 元数据匿名
  ⚠ 有信息: {'author': '...', 'title': '...'}
  → 修复: 在 format.cls / 论文.tex 顶部加 \hypersetup{pdfauthor={}, pdftitle={}}

[4] 关键数字出现次数
  0.4503: 5 次 ✓
  412.47: 3 次 ✓

[5] LaTeX 未定义引用: 0 处

[6] 摘要页判断
  含"关键词": True ✓
  含"问题重述": False (应为 False = 摘要未溢出)
  含"AI 工具使用声明": False (正常情况下, 论文版摘要页应不包含)

========== 总评 ==========
⚠ 有问题, 见上方提示
```

### 依赖

```bash
pip install PyMuPDF
```

---

## 5. `dryrun.py` — 65 项 check 清单 (v1.7.0)

`dryrun.py` 跑 `py -3 dryrun.py --mode self` 一键验 **65 项**, sign-off = 赛前可安心参赛. 跟 CI `smoke-test.yml` 等价, 但本地手动跑.

**完整 65 项清单**（每项判据 + 修复提示）见 `dryrun.py` 的 `CHECKS` 表—— 那里是唯一权威源, 本文件只列前 20 项基础层（复制必 stale）.

**前 20 项 (基础层, 按 sign-off 顺序)**:

| # | check | v1.5.x | 触发 red 的常见原因 |
|---|-------|--------|---------------------|
| 1 | 装包 (核心包) | v1.5.0+ | `pip install pandas numpy scipy openpyxl pymupdf` |
| 2 | 10 Python 脚本 py_compile | v1.5.0+ | 语法错, 看脚本 output |
| 3 | LaTeX 编译 (xelatex × 2) | v1.5.0+ | 模板占位符未替换 / 语法错 / 缺图 |
| 4 | Overfull 数 | v1.5.0+ | 论文.log 有 Overfull \\hbox/\\vbox |
| 5 | pack.py + 2 zip | v1.5.0+ | 跑 `py tools/pack.py` 重打 |
| 6 | AIGC 风险 | v1.5.0+ | `py aigc_scan.py 论文.pdf` 查 9 维度 |
| 7 | SKILL.md frontmatter | v1.5.3+ | 修 SKILL.md `version: "x.y.z"` 字段 |
| 8 | LLM 工具 5 prompt (v1.5.0+) | v1.5.0+ | 检查 `references/llm-prompts/` 5 个 .md |
| 9 | v1.5.1 BZD 借鉴 3 references | v1.5.1+ | 3 个 .md + 1 个 README |
| 10 | v1.5.3 BZD 借鉴 11 新文件 | v1.5.3+ | 9 板块自查 + 1 README + 题意翻译 + 学校国奖画像 |
| 11 | v1.5.2 fitz compat | v1.5.2+ | `import pymupdf as fitz` 兼容 |
| 12 | LICENSE = MIT | v1.5.0+ | 跑题不用管 |
| 13 | 5 步状态机 checkable | v1.5.0+ | 装包 + 7 脚本 import + profile_data |
| 14 | LaTeX 编译可执行性 | v1.5.0+ | xelatex 在 PATH (MiKTeX/TeX Live) |
| 15 | 占位符未替换 (【 TODO) | v1.5.4+ | 搜索 `【` 找未填占位符 |
| 16 | 10.附录.tex 文件存在 | v1.5.4+ | 跑 `py 求解/问题X/问题X_xxx.py` 生成结果 |
| 17 | 图引用存在 (includegraphics) | v1.5.4+ | figures/ 目录的 .png 必须存在 |
| 18 | Post-Solution Audit (必做 2+4) | v1.5.0+ | 跑 `py verify_pdf_metrics.py 论文.pdf` |
| 19 | 读题清单 15 项全覆盖 | v1.5.7+ | 跑题前从 `references/read-checklist/读题清单.md` 复制到 `求解/读题清单.md` 填完 |
| 20 | v1.5.7.5 writing-for-agents 修剪 (description/红线/CHANGELOG/4 完成判据) | v1.5.7.5+ | 验证 4 项: description ≤ 6 行 + references/read-checklist/红线与失败模式.md + CHANGELOG.md + 4 个 🟢 Step X 完成判据 |

**常见 sign-off 状态**:
- 🟢 **`green`** (全部 green, 0 red): 赛前 1 天跑一次安心参赛
- 🟡 **`yellow`** (有 yellow, 0 red): 设计意图跳过, 不用管
- 🔴 **`red`** (有 red): 必须修, 看每项的"修复:"提示

---

## 依赖

```
pip install pandas matplotlib Pillow numpy PyMuPDF
```

可选（用于 visual_qa 的 PNG 预览质量）：
```
pip install SciencePlots  # 多套期刊预设；不装也能用
```

---

## License

脚本借鉴自 scipilot-figure-skill，遵循原作者的开放使用许可。
本目录文件**仅供学习交流**，商用请自行评估原作者条款。
