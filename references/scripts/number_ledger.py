# -*- coding: utf-8 -*-
"""数值台账生成 + 核对脚本 (v1.5.8.2 新增, P0-3 防御).

依据: 2026A 复盘 v1.1 §0 P0-3 — 5.2.2 ρ/cp/k 起止值目测错 (实 976.4→667.3) +
5.4.1"前 10h→1.424cm、占 78%" 目测错 (实 5h、71.8%) + Bi_m 一次心算错 (实 32, 真 3.24).

设计: 4 列结构台账 (符号/值/来源/生成脚本), 3 个子命令:
- init: 建空台账, 扫描现有 result*.xlsx 提取数字
- add: 单条添加 (--sym, --val, --source, --script)
- check: 扫论文 .tex, grep 数字, vs 台账匹配率, 未匹配红

用法:
    python references/scripts/number_ledger.py init --root <跑题根>
    python references/scripts/number_ledger.py add --sym "\\rho" --val 976.4 --source 1 --script "求解/问题1/solve_1.py:L42"
    python references/scripts/number_ledger.py check --paper <论文 dir>
    python references/scripts/number_ledger.py show
"""
import argparse
import csv
import re
import sys
from pathlib import Path


LEDGER_COLS = ["符号", "值", "来源", "生成脚本"]
SOURCE_LABELS = {1: "脚本 print", 2: "resultX.xlsx", 3: "公式现场算"}


def init_ledger(root: Path) -> Path:
    """建空台账 + 扫描现有 result*.xlsx."""
    csv_path = root / "求解" / "数值台账.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(LEDGER_COLS)
        print(f"[OK] 建空台账: {csv_path}")
    else:
        print(f"[SKIP] 台账已存在: {csv_path}")

    # 扫描现有 result*.xlsx 提数字 (每个 sheet 头 3 行 × 头 5 列)
    result_files = list((root / "求解").rglob("result*.xlsx")) if (root / "求解").exists() else []
    if not result_files:
        print(f"[WARN] 求解/ 下未找到 result*.xlsx (跑完求解再跑 init 扫描)")
        return csv_path

    print(f"[INFO] 扫描 {len(result_files)} 个 result*.xlsx")
    try:
        import openpyxl
    except ImportError:
        print("[WARN] openpyxl 未装, 跳过 result 扫描 (pip install openpyxl)")
        return csv_path

    n_added = 0
    for rf in result_files[:3]:  # 限 3 个避免太慢
        try:
            wb = openpyxl.load_workbook(rf, data_only=True, read_only=True)
            for sheet_name in wb.sheetnames[:2]:  # 每个 result 限 2 sheet
                ws = wb[sheet_name]
                for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=5, values_only=True), 1):
                    for col_idx, val in enumerate(row[:5], 1):
                        if isinstance(val, (int, float)) and not isinstance(val, bool):
                            sym = f"result_{rf.stem}_{sheet_name}_r{row_idx}_c{col_idx}"
                            with open(csv_path, "a", encoding="utf-8", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow([sym, val, 2, f"求解/{rf.relative_to(root / '求解')}"])
                            n_added += 1
        except Exception as e:
            print(f"[WARN] 扫描 {rf.name} 失败: {e}")
    print(f"[OK] 扫描完成, 添加 {n_added} 行 result 数字到台账")
    return csv_path


def add_entry(root: Path, sym: str, val: str, source: int, script: str) -> None:
    """单条添加 (幂等)."""
    if source not in (1, 2, 3):
        print(f"[ERROR] 来源必须是 1/2/3, 当前 {source}"); return
    csv_path = root / "求解" / "数值台账.csv"
    if not csv_path.exists():
        print(f"[INIT] 台账不存在, 先跑 init"); init_ledger(root)
    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([sym, val, source, script])
    print(f"[OK] 添加: {sym} = {val} ({SOURCE_LABELS[source]})")


def check_ledger(root: Path, paper_dir: Path) -> int:
    """扫论文 .tex, grep 数字, vs 台账匹配率, 未匹配红."""
    csv_path = root / "求解" / "数值台账.csv"
    if not csv_path.exists():
        print(f"[ERROR] 台账不存在: {csv_path} (先跑 init)"); return 1

    # 读台账
    ledger_vals = set()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                v = float(row["值"])
                # 简化: 数字字符串 (3 位有效)
                ledger_vals.add(f"{v:.3g}")
            except (ValueError, KeyError):
                pass
    print(f"[INFO] 台账 {len(ledger_vals)} 个有效数字")

    # 扫论文 .tex 散文
    target_files = ["0.摘要.tex", "1.引言.tex", "2.总体分析.tex",
                    "5.1.1.分析与准备.tex", "5.1.2.建模与求解.tex",
                    "5.2.建模与求解.tex", "5.3.建模与求解.tex", "5.4.建模与求解.tex",
                    "6.模型检验.tex", "7.模型评价.tex"]
    paper_numbers = []
    for fname in target_files:
        p = paper_dir / fname
        if not p.exists(): continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception: continue
        # 跳过注释 + 数学环境
        text = re.sub(r"%.*", "", text)
        for pat in [r"\$[^\$\n]+\$", r"\\\[[^\]]+\\\]",
                    r"\\begin\{equation\*?\}.+?\\end\{equation\*?\}",
                    r"\\begin\{align\*?\}.+?\\end\{align\*?\}"]:
            text = re.sub(pat, "", text, flags=re.DOTALL)
        # 提所有数字 (3 位有效, 含小数/负号/百分号)
        for m in re.finditer(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?%?", text):
            try:
                v = float(m.group().rstrip("%"))
                paper_numbers.append((fname, m.group(), f"{v:.3g}"))
            except ValueError: pass

    unique_paper = set(n[2] for n in paper_numbers)
    matched = unique_paper & ledger_vals
    unmatched = unique_paper - ledger_vals
    print(f"[INFO] 论文 {len(unique_paper)} 个唯一数字, 匹配台账 {len(matched)} 个, 未匹配 {len(unmatched)} 个")
    if unmatched:
        print(f"[WARN] 未匹配数字 (前 10): {list(unmatched)[:10]}")
        print(f"  建议: 跑 `number_ledger.py add --sym <符号> --val <值> --source <1|2|3> --script <生成脚本>` 补台账")
    match_rate = len(matched) / len(unique_paper) if unique_paper else 1.0
    print(f"[OK] 匹配率: {match_rate:.1%}")
    return 0 if match_rate >= 0.7 else 1  # <70% 视为 red


def show_ledger(root: Path) -> None:
    """打印台账."""
    csv_path = root / "求解" / "数值台账.csv"
    if not csv_path.exists():
        print(f"[ERROR] 台账不存在: {csv_path}"); return
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            print(" | ".join(row))


def main():
    parser = argparse.ArgumentParser(description="数值台账生成+核对 (P0-3 防御)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="建空台账 + 扫 result*.xlsx")
    p_init.add_argument("--root", required=True, type=Path)

    p_add = sub.add_parser("add", help="单条添加")
    p_add.add_argument("--root", required=True, type=Path)
    p_add.add_argument("--sym", required=True, help="LaTeX 符号 e.g. \\rho")
    p_add.add_argument("--val", required=True, help="实际数值")
    p_add.add_argument("--source", required=True, type=int, choices=[1, 2, 3])
    p_add.add_argument("--script", required=True, help="来源脚本路径 e.g. 求解/问题1/solve_1.py:L42")

    p_check = sub.add_parser("check", help="扫论文 .tex vs 台账匹配率")
    p_check.add_argument("--root", required=True, type=Path)
    p_check.add_argument("--paper", required=True, type=Path)

    p_show = sub.add_parser("show", help="打印台账")
    p_show.add_argument("--root", required=True, type=Path)

    args = parser.parse_args()
    if args.cmd == "init":
        init_ledger(args.root)
    elif args.cmd == "add":
        add_entry(args.root, args.sym, args.val, args.source, args.script)
    elif args.cmd == "check":
        sys.exit(check_ledger(args.root, args.paper))
    elif args.cmd == "show":
        show_ledger(args.root)


if __name__ == "__main__":
    main()
