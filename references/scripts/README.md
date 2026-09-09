# scripts/ — 程序化自检工具集

> 借鉴自 `scipilot-figure-skill`（MIT 风格脚本）+ cumcm-live-workflow-skill v5.0 `verify_pdf_metrics.py`，改写为数学建模国赛工作流。
> 原作者：[scipilot-figure-skill](https://github.com/scipilot/scipilot-figure-skill)

**7 个 Python 脚本**（5 自检 + 1 AIGC + 1 跨题工具），覆盖「画图前数据剖析 → 出图后程序自检 → 提交前格式检查 → 终审前 PDF 体检 → AIGC 9 维度扫描 → 跨题 GBK 兼容 → **23 项 check 一体化 sign-off**」。
**不依赖** skill 系统本身——独立可执行，`pip install pandas matplotlib Pillow numpy PyMuPDF` 后即用。

**脚本索引**（按工作流顺序）:

| # | 脚本 | 类别 | 用途 |
|---|------|------|------|
| 1 | `profile_data.py` | 自检 | 画图前 EDA（数据剖析） |
| 2 | `visual_qa.py` | 自检 | 出图后程序自检（缺字/裁切/刻度重叠） |
| 3 | `data_utils.py` | 跨题工具 | GBK 兼容 + CSV 安全读写 |
| 4 | `check_figure.py` | 自检 | 提交前图片格式合规（DPI/字体嵌入） |
| 5 | `aigc_scan.py` | AIGC | 9 维度 AI 痕迹扫描 |
| 6 | `verify_pdf_metrics.py` | 自检 | 终审前 PDF 6 项体检 |
| 7 | `dryrun.py` | 自检 | **23 项 check 一键 sign-off**（赛前 1 天必跑） |

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

## 3. `data_utils.py` — 跨题 GBK 兼容 + CSV 安全读写

**目的**：解决 Windows PowerShell 5.1 GBK 控制台跑中文/emoji 乱码崩溃问题；同时给所有脚本提供统一的 CSV 读写入口（兼容 UTF-8 / UTF-8 BOM / GBK）。

**工作流位置**：被其他 6 个脚本 import（`ensure_utf8_stdout` 几乎每脚本头部都调），跨题复用。

### 用法

```python
from data_utils import ensure_utf8_stdout, read_csv_safe, save_csv
import pandas as pd

ensure_utf8_stdout()  # 调一次, stdout/stderr reconfigure utf-8
df = read_csv_safe("数据/结果.csv")  # 自动试 utf-8 / utf-8-sig / gbk
save_csv(df, "数据/结果_clean.csv")  # 统一 utf-8-sig, Excel 打开不乱码
```

### 主要导出

- `ensure_utf8_stdout()` — Windows GBK console 强制 UTF-8，emoji/中文不崩
- `read_csv_safe(path, **kwargs)` — 自动试 3 种编码, 返回 DataFrame
- `save_csv(df, path, **kwargs)` — 统一 utf-8-sig 写出

### 何时不该用

- 用 Jupyter / Linux 终端（默认 UTF-8，不需要 reconfigure）
- 读 SAS / SPSS 文件（用 `pyreadstat`）

---

## 4. `check_figure.py` — 提交前格式合规检查

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

## 5. `aigc_scan.py` — 9 维度 AIGC 痕迹扫描

**目的**：跑题后 / 终审前对**完整论文**做 9 维度 AIGC 痕迹扫描——
模板句式、被动语态、形容词副词、连接词、句式多样性、模板词、口语化
词、过密标点、AIGC 特征词（v1.5.0+）。**非破坏性**——只读、不修改。

**工作流位置**：Step 5.5（提交前 1-2 小时）或 Stage 6 终审前。

### 用法

```bash
# 基础扫描
py aigc_scan.py 论文/论文.pdf

# 输出 JSON 报告（可计分）
py aigc_scan.py 论文/论文.pdf --json > aigc_report.json

# 指定阈值（默认 9 维度各有一套阈值）
py aigc_scan.py 论文/论文.pdf --threshold 0.5

# 退出码: 0=全维度 ok, 1=有维度超阈值
```

```python
from aigc_scan import load_text, scan_text
text = load_text("论文/论文.pdf")  # 文件不存在会 raise FileNotFoundError
report = scan_text(text)
print(report.summary())
```

### 9 维度

1. 模板句式命中（`TEMPLATE_PATTERNS`）
2. 被动语态密度
3. 形容词 / 副词密度
4. 连接词密度
5. 句式多样性
6. 模板词命中（`TEMPLATE_WORDS`）
7. 口语化 / 网络用语词（`COLLOQUIAL_TERMS`）
8. 过密标点
9. AIGC 特征词（v1.5.0+）

### 配合

- 命中后用 `references/去AIGC指南.md` 4 铁律 + 3 轮协议降重
- 受保护片段（参考文献/公式/数据/术语/引语）见 `references/受保护片段.md`

---

## 6. `verify_pdf_metrics.py` — 终审前 PDF 成品结构体检

> 借鉴自 cumcm-live-workflow-skill v5.0 `references/verify_pdf_metrics.py`，适配 li-mtrie 2026 规范 + CUMCMthesis 格式（页边距 2.5 cm）。

**目的**：交付前 10 秒出 6 项体检结果：
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

## 7. `dryrun.py` — 23 项 check 清单 (v1.5.7+)

`dryrun.py` 跑 `py dryrun.py` 一键验 23 项, sign-off 绿 = 赛前可安心参赛. 跟 CI `smoke-test.yml` 等价, 但本地手动跑.

**23 项 check (按 sign-off 顺序)**:

| # | check | v1.5.x | 触发 red 的常见原因 |
|---|-------|--------|---------------------|
| 1 | 装包 (核心包) | v1.5.0+ | `pip install pandas numpy scipy openpyxl pymupdf` |
| 2 | 10 Python 脚本 py_compile | v1.5.0+ | 语法错, 看脚本 output |
| 3 | LaTeX 编译 (xelatex × 2) | v1.5.0+ | 模板占位符未替换 / 语法错 / 缺图 |
| 4 | Overfull 数 | v1.5.0+ | 论文.log 有 Overfull \hbox/\vbox |
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
| 19 | 读题清单 15 项全覆盖 | v1.5.7+ | 跑题前从 `references/读题清单.md` 复制到 `求解/读题清单.md` 填完 |
| 20 | v1.5.7.5 writing-for-agents 修剪 (description/红线/CHANGELOG/4 完成判据) | v1.5.7.5+ | 验证 4 项: description ≤ 6 行 + references/红线与失败模式.md + CHANGELOG.md + 4 个 🟢 Step X 完成判据 |
| 21 | profile_data.py 不遮蔽 warnings 模块 | v1.5.7.5+ | 局部 list 变量重命名为 `warns` (检查 `warnings: list[str]` / `warnings.append(`) |
| 22 | profile_data.py sd 键名正确 | v1.5.7.5+ | `.get("std", ...)` → `.get("sd", ...)` (检查 `.get("std",`) |
| 23 | aigc_scan.py 库函数不再 sys.exit | v1.5.7.5+ | 库函数错误处理改 `raise` 不调 `sys.exit` (检查 `sys.exit(`) |

**常见 sign-off 状态**:
- 🟢 **绿** (11-19 green, 0 red): 赛前 1 天跑一次安心参赛
- 🟡 **黄** (有 yellow, 0 red): 设计意图跳过, 不用管
- 🔴 **红** (有 red): 必须修, 看每项的"修复:"提示

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
