# -*- coding: utf-8 -*-
"""check_meta.py — 验证 meta.json 含 3 件套 (v1.5.9.4 新增, P1-7 防御).

依据: 2026A 复盘 v1.1 §P1-7 — 评阅关注点 2 强调"高效数值计算过程", 但脚本
print 了 elapsed 未入交付文件, 论文靠会话记忆. 改进: code-template 强制
`meta.json` 落盘 (耗时/步数/网格/版本), 论文 §5.X.2 必引 3 件套.

本脚本: 扫 `求解/问题N/结果/meta.json`, 验证必填字段 (elapsed_sec /
steps / grid / dt / dr / complexity / version) 都不为 None. 缺一 → red.

用法:
    py check_meta.py --root <跑题根>           # 扫所有问题
    py check_meta.py --root <跑题根> --problem 1  # 单问题
    from check_meta import audit_meta; audit_meta(root, "问题1/结果/meta.json")
"""
import argparse
import json
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

REQUIRED_FIELDS = ["elapsed_sec", "steps", "grid", "dt", "dr", "complexity", "version"]


def audit_meta(meta_path: Path) -> dict:
    """单 meta.json 审计. 返回 {ok, missing, fields}."""
    if not meta_path.exists():
        return {"ok": False, "missing": ["文件不存在"], "fields": {}}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"ok": False, "missing": [f"JSON 解析失败: {e}"], "fields": {}}

    missing = []
    for f in REQUIRED_FIELDS:
        if f not in data or data[f] is None or (isinstance(data[f], str) and not data[f].strip()):
            missing.append(f)

    return {"ok": not missing, "missing": missing, "fields": data}


def main():
    parser = argparse.ArgumentParser(description="验证 meta.json 含 3 件套 (P1-7 防御)")
    parser.add_argument("--root", required=True, type=Path, help="跑题项目根")
    parser.add_argument("--problem", type=str, default=None, help="单问题编号 (e.g. 1, 2-1, 2-2)")
    args = parser.parse_args()

    solve_dir = args.root / "求解"
    if not solve_dir.is_dir():
        print(f"[ERROR] 求解/ 不存在: {solve_dir}")
        sys.exit(1)

    # 扫所有问题目录
    problem_dirs = sorted([d for d in solve_dir.iterdir()
                          if d.is_dir() and (d.name.startswith("问题") or d.name.startswith("Q"))])
    if args.problem:
        problem_dirs = [d for d in problem_dirs if args.problem in d.name]

    if not problem_dirs:
        print(f"[WARN] 没找到问题目录 (扫 {solve_dir})")
        sys.exit(0)

    n_total = 0
    n_red = 0
    n_green = 0
    print(f"[INFO] 扫 {len(problem_dirs)} 个问题目录")
    for pdir in problem_dirs:
        meta_files = list(pdir.rglob("meta.json"))
        if not meta_files:
            print(f"  [RED] {pdir.name}: meta.json 缺失 (P1-7 强制)")
            n_red += 1
            n_total += 1
            continue
        for mf in meta_files:
            n_total += 1
            result = audit_meta(mf)
            if result["ok"]:
                print(f"  [GREEN] {mf.relative_to(args.root)}: 7 件套全填 ({result['fields'].get('elapsed_sec', '?')}s)")
                n_green += 1
            else:
                print(f"  [RED] {mf.relative_to(args.root)}: 缺字段 {result['missing']}")
                n_red += 1

    print()
    print(f"[SUMMARY] {n_total} meta.json: {n_green} green + {n_red} red")
    if n_red > 0:
        print("修复: 跑 code-template.py 让其自动落 meta.json, 填全 7 字段 (elapsed_sec / steps / grid / dt / dr / complexity / version)")
        sys.exit(1)


if __name__ == "__main__":
    main()
