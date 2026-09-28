# check_tex_compile — 编译命令参考 (v1.5.7.20 新增, 从 SKILL.md §Step 4 拆出)

> **权威源**: 本文件是 §Step 4 编译命令的权威源. SKILL.md 只留指针 + 红/绿判据.
>
> **为什么独立**: xelatex 命令块 + 编译顺序 + 红/绿判据在 SKILL.md 占 ~50 行 inline reference, **不是跑题主流程** (主流程是 5 步状态机). 拆到这里减 SKILL.md sprawl.

---

## 1. 编译命令 (论文版 + 电子版 + AI 详情)

```powershell
Set-Location 论文

# 论文版 (含承诺书 + 编号页) — 跑 2 次解析 \ref / \cite / \pageref
xelatex -interaction=nonstopmode 论文.tex
xelatex -interaction=nonstopmode 论文.tex

# 电子版 (不含承诺书 + 编号页, 第一页直接是摘要页)
xelatex -interaction=nonstopmode 电子版.tex
xelatex -interaction=nonstopmode 电子版.tex

# AI 工具使用详情 (共用 format.cls, 同样 ×2)
xelatex -interaction=nonstopmode AI工具使用详情.tex
xelatex -interaction=nonstopmode AI工具使用详情.tex
```

**为什么 ×2**:

- 第 1 次解析 `\ref` / `\cite` / `\pageref` / 目录占位 → 第 2 次填到正确页码
- longtable 续表头需 2 次定位 (首页 + 跨页续表头)
- AI 详情跟主论文共用 format.cls, 同样规则

---

## 2. 红/绿判据 (一行 grep 出全)

```powershell
# 必须全绿才进 Step 4.4 打包
Select-String -Path 论文.log -Pattern '! Error|Overfull|Rerun'

# 绿: ! Error = 0, Overfull \hbox < 5, Rerun 标记 ≤ 1
# 红: ! Error ≥ 1 → 修 LaTeX; Overfull ≥ 5 → 调列宽比例 (Step 4.2)
```

---

## 3. 排版优化 (Step 4.2 循环)

```powershell
# 一行 grep 警告
Select-String -Path 论文.log, 电子版.log -Pattern 'Overfull|Underfull|Float too large'

# 修复: 调整列宽比例 / 改换行位置
# 2 次修不好允许 \\newline 或 \\sloppy
```

**绿/红**:
- **绿**: `! Error` = 0, `Overfull \hbox` < 5, `Underfull \hbox` < 10
- **红**: 列宽比例公式 `1.04 − 0.04N` (详 paper-spec §4.1)

---

## 4. 打包 + 一键合规

- **打包支撑材料** (Step 4.4) → `references/scripts/pack.py` + dryrun check 5
- **一键合规验证** (Step 4.3) → `references/data-usage/合规检查清单.md §2 一键验证命令`
- **最终提交物检查** (Step 4.5) → 详 SKILL.md §Step 4.5

---

## 5. 与 SKILL.md 的引用关系

- SKILL.md §Step 4.1: 留 why ×2 + 红/绿判据, 指针 → 本文件
- SKILL.md §Step 4.2: 留绿/红判据 + 列宽公式, 命令块推 → 本文件
- SKILL.md §Step 4.3: 已指针化 (`references/data-usage/合规检查清单.md §2`), 维持
- SKILL.md §Step 4.4/4.5: 涉及打包命令, 维持 inline (有 sign-off 关键判据)