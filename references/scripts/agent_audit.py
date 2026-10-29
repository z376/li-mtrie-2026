"""li-mtrie-2026 :: agent_audit.py
====================================
跑题后 mavis 代理审计 brief 生成器 (v1.5.7.38).

背景: dryrun 47 项 hardcode check 是 mechanical 防线 (DPI/格式/语法), 抓不到
内容级问题 (v15 P0-1 表9 365冒334 / v17 P0-A 表9 编造拆分 / v17 P0-C claude2025
误列 / v15 P0-2 Bertsimas-Sim 声称与代码不符 等). 这类问题需要上下文推理 +
数字级比对 + cross-file 比对, 必须靠 mavis worker sub-session 代理审计.

设计:
- dryrun self-audit (47 项) 仍然跑, 防 mechanical 问题
- 用户要求审计时, 跑本脚本生成 markdown brief
- 复制 brief 到 mavis 主对话 → mavis spawn mavis worker sub-session (fresh, 独立 context)
- worker 实际读 paper/tex + result xlsx + LP 复现 + 比对, 写报告
- 报告回 mavis 主对话 → 用户

每次审计都生成 fresh brief, 不缓存 (mavis worker 每次 fresh, 独立 context).

用法:
    python references/scripts/agent_audit.py                    # 默认 paper_dir
    python references/scripts/agent_audit.py --paper-dir C:/my-paper/论文
    python references/scripts/agent_audit.py --list             # 列出 paper 文件清单
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Windows GBK console 兼容 (v1.7.2 新增: 子进程管道输出必须是 UTF-8)
# 背景: dryrun.py 用 subprocess + encoding='utf-8' 读本脚本 stdout,
#       本脚本若按 cp936(GBK) 写中文 -> UnicodeDecodeError -> 调用方 exit 1.
# Python 3.7+
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass  # 旧 Python / 非 stdout 对象, 跳过

# 与 dryrun.get_paper_dir 同步
SKILL_ROOT = Path(__file__).parent.parent.parent
TEX_DIR = SKILL_ROOT / "论文"


def get_paper_dir() -> Path:
    """与 dryrun.get_paper_dir 同步: --paper-dir > PAPER_DIR > cwd/论文/ > templates/example-paper/ > cwd."""
    env_dir = os.environ.get("PAPER_DIR")
    if env_dir:
        return Path(env_dir)
    if "--paper-dir" in sys.argv:
        idx = sys.argv.index("--paper-dir")
        if idx + 1 < len(sys.argv):
            return Path(sys.argv[idx + 1])
    cwd = Path(os.getcwd())
    if (cwd / "论文").is_dir() and any((cwd / "论文").glob("*.tex")):
        return cwd / "论文"
    template_dir = SKILL_ROOT / "references" / "templates" / "example-paper"
    if template_dir.is_dir() and any(template_dir.glob("*.tex")):
        return template_dir
    if cwd.is_dir() and any(cwd.glob("*.tex")):
        return cwd
    return TEX_DIR


def list_paper_files(paper_dir: Path) -> dict:
    """列 paper dir 下所有相关文件, 按类别分组."""
    files = {
        "tex_chapters": sorted(paper_dir.glob("*.tex")),
        "figures": sorted((paper_dir / "figures").rglob("*.png")) if (paper_dir / "figures").exists() else [],
        "pdfs": sorted(paper_dir.glob("*.pdf")),
    }
    # 求解目录
    solve_dir = paper_dir.parent / "求解"
    if solve_dir.exists():
        files["solve_py"] = sorted(solve_dir.rglob("*.py"))
        files["solve_xlsx"] = sorted(solve_dir.rglob("result*.xlsx"))
        files["solve_imgs"] = sorted(solve_dir.rglob("*.png"))
    else:
        files["solve_py"] = []
        files["solve_xlsx"] = []
        files["solve_imgs"] = []
    # 数据目录
    data_dir = paper_dir.parent / "数据"
    if data_dir.exists():
        files["data"] = sorted(data_dir.rglob("*"))
    else:
        files["data"] = []
    return files


def generate_brief(paper_dir: Path) -> str:
    """生成 mavis worker 审计 brief (markdown)."""
    if not paper_dir.exists():
        return f"[ERROR] paper_dir 不存在: {paper_dir}"

    files = list_paper_files(paper_dir)
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    # 文件清单
    tex_lines = "\n".join(f"  - `{f.relative_to(paper_dir.parent)}`" for f in files["tex_chapters"])
    figure_lines = "\n".join(f"  - `{f.relative_to(paper_dir.parent)}`" for f in files["figures"]) or "  (无)"
    pdf_lines = "\n".join(f"  - `{f.relative_to(paper_dir.parent)}`" for f in files["pdfs"]) or "  (无)"
    solve_py_lines = "\n".join(f"  - `{f.relative_to(paper_dir.parent)}`" for f in files["solve_py"]) or "  (无)"
    solve_xlsx_lines = "\n".join(f"  - `{f.relative_to(paper_dir.parent)}`" for f in files["solve_xlsx"]) or "  (无)"
    solve_img_lines = "\n".join(f"  - `{f.relative_to(paper_dir.parent)}`" for f in files["solve_imgs"]) or "  (无)"

    template_note = "\n> ⚠️ 这是 example 模板, 不是跑题论文 — 审计时跳过'真实数字'类检查, 重点看结构/格式.\n" if is_template else ""

    brief = f"""# mavis 代理审计 brief — li-mtrie-2026 跑题后 (v1.5.7.38)

> **用法**: 复制本 brief 到 mavis 主对话, mavis 会 spawn mavis worker sub-session 独立 fresh 审计.
> **重要**: 每次审计都 fresh 调用, 不缓存; worker 用独立 context, 不复用主对话历史.

## 1. 审计目标

- **论文目录**: `{paper_dir}`
- **项目根**: `{paper_dir.parent}` (含 论文/ + 求解/ + 数据/)
- **skill 根目录**: `{SKILL_ROOT}` (skill 自带脚本在此, 如 `references/scripts/bc_check.py`; 审计工具请用这里的绝对路径)
- **审计时间**: 当前 (fresh, 不复用历史)
- **审计模式**: 跑题后内容审计 (P0 一票否决 + P1 严重 + P2 推荐) {template_note}

## 2. 文件清单 (worker 应读这些)

### 2.1 论文章节 (.tex, {len(files['tex_chapters'])} 个)
{tex_lines}

### 2.2 图片 ({len(files['figures'])} 个)
{figure_lines}

### 2.3 PDF 编译产物
{pdf_lines}

### 2.4 求解代码 + 结果 ({len(files['solve_py'])} py + {len(files['solve_xlsx'])} xlsx)
- 求解 .py:
{solve_py_lines}
- 结果 .xlsx:
{solve_xlsx_lines}
- 中间图 ({len(files['solve_imgs'])} 个):
{solve_img_lines}

## 3. 审计 checklist (L1-L16 + 实战反例)

按 `references/audit/参考文献审计清单.md` 16 层审计框架 (v1.5.7.35) + 绘图规范 §十 实战反例 (v1.5.7.36) + AIGC 扫描 (v1.5.7.37). 重点关注:

### 3.1 关键 P0 反例 (2025C 实战, 一票否决级)

| 反例 | 防御检查点 |
|---|---|
| v15 P0-1 §5.3 表9 365天值冒名 334 天 (3197.7 万 vs 实际 2918.3 万) | 扫摘要 + §5.X 数字 vs resultX.xlsx 真实值, 跨问题口径混用红 |
| v15 P0-2 "Bertsimas-Sim Γ 预算" 声称与代码 plan_day_robust 不符 | 读求解/共享/planner.py 找实际方法, 对照 §3 假设 + §5 + §7 描述 |
| v15 P0-3 g_adj 无上界 → 14,797 格物理不可行值 | 跑 plan_day, 检查 g_adj ≤ p_max·dt |
| v15 P0-4 附件 5 旧版 (09-11 11:21) | 检查 数据/附件/附件5/ mtime vs 求解/最新 mtime |
| v17 P0-A 表9 编造拆分 (凑"行和=总费用"凭空构造) | 数字级比对: 计划购电费 + 紧急购电费 + 多买电费 = 总费用? |
| v17 P0-B 表q1_robust 全表编造 (38,823 ≈ 36,272 × 1.07 编造痕迹) | 调 plan_day_robust 重算 Q1, 比对论文表值 |
| v17 P0-C claude2025 列为正式文献 [14] (AI 修复时把自己写进参考文献) | 扫 9.参考文献.tex 含 AI 工具关键词 (Claude Sonnet/Anthropic/OpenAI/GPT-4o 等 40 项) |
| v17 P0-D li2018/zhang2022 幻觉文献 (标题真, 作者/期刊/年份/卷期全错) | 人工 spot-check 12 步骤 (L4), 国家科技期刊平台 / Web of Science 核验 |
| v17 P0-E 旧图未刷新 + 附件 5 仅 2/5 刷新 | 比对 figures/ mtime vs 求解 resultX.xlsx mtime |
| 论文综合 §2.4 Q4 论文数与任一口径都不符 (Q2/Q3 365 vs Q4 334) | 全文统一 334 天 (附件 5 模板) 或 365 天, 标注口径 |
| 论文综合 §六.1 图1 SOC 子图缺失 (图注称"上:购电量, 下:SOC", 实际只有上面板) | 读 PDF caption vs 实际 figure axes 数 |
| 论文综合 §六.2 8 张冗余未引用图残留 | 扫 figures/ 中未被任何 .tex \\includegraphics 引用的 .png |
| 结果图文献 §3.4 Q1 未按题面表1/表2 格式 | 检查 result1.xlsx 有合规 sheet, 论文是否引用 |
| 结果图文献 §3.5 §6/§7 灵敏度表无代码支撑 | 扫 求解/ 下 .py 含 noise_injection / parameter sweep / sensitivity |

### 3.2 AIGC 痕迹 (v1.5.7.37 dryrun check 49/50)

- 段首重复率 > 50% 红 (Sep 13 报告阈值 39.6%)
- 连接词密度 > 15% 红 (Sep 13 报告阈值 7.5%)
- "同时" ×8 偏多, 替换为"且/并/另一方面"
- "问题一/二/三/四" 段首 ×12 偏多, 替换为"本问/该问题/此问题"

### 3.3 数据/代码一致性 (L10 manual)

- §3 模型假设 vs 求解/共享/planner.py 实际方法名
- 数据来源文献 (附件 1-5) vs resultX.xlsx 数字
- 鲁棒参数 (δ_pv / δ_load) vs 论文 §5.1.2 公式

## 4. 报告输出格式 (worker 必须按此格式)

```markdown
# mavis worker 审计报告 — [paper_dir] (审计时间: <date>)

## 总体结论
- P0 数量: X 项 (一票否决级, 提交前必修)
- P1 数量: Y 项 (严重, 提交前修)
- P2 数量: Z 项 (推荐优化)
- 整体判定: ❌ 不通过 / ⚠️ 警告 / ✅ 可提交

## P0 项 (一票否决)
### P0-1: [标题]
- 位置: 论文/5.X.tex L123
- 问题: [具体描述]
- 复现: [代码/LP 重算步骤]
- 修复: [具体命令/LaTeX 修改]

## P1 项 (严重)
### P1-1: ...

## P2 项 (推荐)
### P2-1: ...

## 数字一致性比对表
| 位置 | 论文值 | resultX.xlsx 真实值 | 偏差 |
|---|---|---|---|
| §5.2 总费用 | ... | ... | ... |

## 参考文献核验表
| 条目 | 真实性 | 备注 |
|---|---|---|
```

## 5. 跑题后审计必做顺序 (worker 应按此顺序)

1. **P0 优先**: 扫 §3.1 关键 P0 反例 (14 项) — 任一命中即标 P0
2. **P1 次优**: 数字一致性 + 假设 vs 代码 + 图文一致 + 灵敏度可复现
3. **P2 推荐**: 段首重复 + 连接词密度 + 冗余图清理 + Q1 表1/表2 格式 + 中文字体

## 6. 重要约束

- **不要缓存**: 每次审计 fresh 调用, 不复用主对话历史
- **不要省略数字**: 关键 P0 项必须给复现值 (LP 复算 / 文件 mtime / 期刊数据库核验)
- **不要给模糊建议**: 修复必须给具体命令 (xelatex 命令 / sed 替换 / Python 脚本)
- **不要只看封面**: 必须读全部 13 章节 .tex + resultX.xlsx + planner.py
- **输出短**: 报告 ≤ 30 KB, 重点突出 P0 (一票否决)

---

**简明触发**: 复制本 brief 整段到 mavis 主对话, mavis 会自动 spawn mavis worker sub-session 独立 fresh 审计.
"""
    return brief


def _cli() -> int:
    p = argparse.ArgumentParser(description="mavis 代理审计 brief 生成器 (v1.5.7.38)")
    p.add_argument("--paper-dir", help="论文目录路径 (默认自动检测)")
    p.add_argument("--list", action="store_true", help="只列 paper 文件清单, 不生成 brief")
    args = p.parse_args()

    paper_dir = Path(args.paper_dir) if args.paper_dir else get_paper_dir()

    if args.list:
        files = list_paper_files(paper_dir)
        print(f"# paper_dir: {paper_dir}\n")
        for k, v in files.items():
            print(f"## {k} ({len(v)} 个)")
            for f in v:
                try:
                    print(f"  - {f.relative_to(paper_dir.parent)}")
                except ValueError:
                    print(f"  - {f}")
            print()
        return 0

    if not paper_dir.exists():
        print(f"[ERROR] paper_dir 不存在: {paper_dir}", file=sys.stderr)
        return 1

    brief = generate_brief(paper_dir)
    print(brief)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())