# scripts/ — 程序化自检工具集

> 借鉴自 `scipilot-figure-skill`（MIT 风格脚本）+ cumcm-live-workflow-skill v5.0 `verify_pdf_metrics.py`，改写为数学建模国赛工作流。
> 原作者：[scipilot-figure-skill](https://github.com/scipilot/scipilot-figure-skill)

6 个 Python 脚本（4 自检 + 1 AIGC + 1 跨题工具），覆盖「画图前数据剖析 → 出图后程序自检 → 提交前格式检查 → 终审前 PDF 体检 → AIGC 9 维度扫描 → 跨题 GBK 兼容」。
**不依赖** skill 系统本身——独立可执行，`pip install pandas matplotlib Pillow numpy PyMuPDF` 后即用。

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

> 借鉴自 cumcm-live-workflow-skill v5.0 `references/verify_pdf_metrics.py`，适配 li-mtrie 2026 规范 + CUMCMthesis 格式（页边距 2.5 cm）。

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
