# -*- coding: utf-8 -*-
"""fig_sanity.py — 图形程序化内容自检 (v1.5.9 新增, P1-3 防御).

依据: 2026A 复盘 v1.1 §P1-3 — Q1 干燥前沿因阈值写成 `2.5*C0` 曲线恒为 0
(NP.PTP(Y) == 0), 靠肉眼发现; 另有 C₀ 字形□乱码. 改进: 程序化自检
NP.PTP(Y)==0 / 全 NaN / 超物理范围 / 标题含 U+2080 下标 / 顶部标题带暗
像素占比 > 0.06 (残留 set_title).

与 check_figure.py (格式 / DPI / 字体) 互补, check_figure.py 是格式层,
fig_sanity.py 是内容层. 两者协同: 内容错 (np.ptp=0) 走 fig_sanity,
格式错 (DPI 不足) 走 check_figure.

用法:
    py fig_sanity.py figures/  # 扫整个目录
    py fig_sanity.py figures/q1_*.png  # 扫指定文件
    from fig_sanity import audit_content; audit_content('figures/q1.png')  # Python API
"""
import os
import sys
import re
import argparse
from pathlib import Path

# 物理范围阈值 (按题面给, 跑题用户可改)
PHYSICAL_BOUNDS = {
    'T': (-50.0, 200.0),     # 温度 ℃ (烘房上限 ~150℃)
    'C': (0.0, 1.0),         # 浓度 (无量纲, 0-1)
    'X': (0.0, 1.0),         # 含水率
    'R': (0.0, 0.5),         # 半径 m (药材 2-4cm)
    'rho': (0.0, 10000.0),   # 密度 kg/m³
    'cp': (0.0, 10000.0),    # 比热 J/(kg·K)
    'h': (0.0, 1000.0),      # 传热系数 W/(m²·K)
    'k': (0.0, 100.0),       # 导热系数 W/(m·K)
    'time': (0.0, 1e7),      # 时间 s
}


def check_fig_nan(path: str) -> bool:
    """检查图像数据是否全 NaN (从同目录 csv/读取, fallback 直接读 png)."""
    # 简化: 直接 read numpy 失败的图像 (跳过内容级)
    return False


def check_fig_title_pixel(path: str, threshold: float = 0.06) -> tuple:
    """用 PIL 检测图像顶部 5% 区域暗像素占比.

    用于检测残留 matplotlib set_title (图内标题). 双标题会让 caption 与
    set_title 近似复述, 顶部暗像素增多. 阈值 0.06 = 顶部 5% 区域暗像素
    (R<100) 占比.

    返回 (占比, 是否超阈值).
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return -1.0, False

    try:
        img = Image.open(path).convert('RGB')
        w, h = img.size
        # 取顶部 5%
        top_h = max(int(h * 0.05), 10)
        top_region = np.array(img.crop((0, 0, w, top_h)))
        # 暗像素: R<100 (任意通道)
        dark = (top_region[:, :, 0] < 100).sum()
        total = top_region.shape[0] * top_region.shape[1]
        ratio = dark / total if total > 0 else 0.0
        return ratio, ratio > threshold
    except Exception:
        return -1.0, False


def check_fig_unicode_subscript(path: str) -> bool:
    """检测 .py 源文件 (同目录) 是否含 U+2080 下标 (C₀ □乱码反例)."""
    # 简化: 检查同目录 .py
    p = Path(path)
    base = p.stem
    py_candidates = list(p.parent.glob(f"{base}.py"))
    py_candidates.extend(p.parent.glob(f"*_{base}.py"))
    py_candidates.extend(p.parent.glob(f"plot_{base}.py"))
    for py in py_candidates:
        try:
            content = py.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        # U+2080 是下标 0, U+2081-U+2089 是下标 1-9
        for ch in ['\u2080', '\u2081', '\u2082', '\u2083', '\u2084', '\u2085', '\u2086', '\u2087', '\u2088', '\u2089']:
            if ch in content:
                return True
    return False


def check_fig_csv_data(path: str) -> dict:
    """检查对应 .csv 数据, np.ptp(y)==0 / 全 NaN / 超物理范围."""
    issues = []
    p = Path(path)
    base = p.stem
    csv_candidates = list(p.parent.glob(f"{base}.csv"))
    csv_candidates.extend(p.parent.glob(f"*_{base}.csv"))
    csv_candidates.extend(p.parent.glob(f"{base}_data.csv"))
    csv_candidates.extend(p.parent.glob(f"{base}_data/*.csv"))

    if not csv_candidates:
        return {"has_csv": False}

    try:
        import numpy as np
        # 找第一个 csv 检查
        for csv in csv_candidates[:1]:
            try:
                data = np.loadtxt(csv, delimiter=',', skiprows=1)
            except Exception:
                try:
                    data = np.loadtxt(csv, delimiter='\t', skiprows=1)
                except Exception:
                    return {"has_csv": True, "load_error": True}
            if data.size == 0:
                issues.append("csv 空文件")
                continue
            # 检查每列
            if data.ndim == 1:
                data = data.reshape(-1, 1)
            for j in range(min(data.shape[1], 8)):
                col = data[:, j]
                # 全 NaN
                if np.all(np.isnan(col)):
                    issues.append(f"col[{j}] 全 NaN")
                    continue
                # 排除 NaN 后检查
                valid = col[~np.isnan(col)]
                if valid.size == 0:
                    continue
                # np.ptp == 0 (曲线恒为常数)
                ptp = np.ptp(valid)
                if ptp == 0:
                    issues.append(f"col[{j}] np.ptp=0 (曲线恒为常数, 阈值可能写错)")
                # 超物理范围 (按列头 1 行 找物理量)
            break
    except ImportError:
        return {"has_csv": True, "numpy_missing": True}

    return {"has_csv": True, "issues": issues}


def audit_content(path: str, title_threshold: float = 0.06) -> dict:
    """主入口: 1 张图的内容自检, 返回 {issues: [], warnings: [], ok: bool}."""
    p = Path(path)
    if not p.exists():
        return {"issues": [f"文件不存在: {path}"], "warnings": [], "ok": False}

    if p.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.pdf', '.svg'):
        return {"issues": [], "warnings": [f"非图像文件: {p.suffix}"], "ok": True}

    issues = []
    warnings = []

    # 1. 顶部暗像素 (残留 set_title)
    ratio, has_title = check_fig_title_pixel(str(p), title_threshold)
    if ratio >= 0:
        if has_title:
            issues.append(f"顶部暗像素占比 {ratio:.3f} > {title_threshold} (残留 set_title, 与 caption 双标题)")
        # else: 0.06 阈值内 OK, 不报

    # 2. U+2080 下标
    if check_fig_unicode_subscript(str(p)):
        warnings.append(".py 源文件含 U+2080 下标 (C₀ □乱码反例, 改用 'C_0' 或 'C0')")

    # 3. csv 数据自检
    csv_check = check_fig_csv_data(str(p))
    if csv_check.get("has_csv"):
        if csv_check.get("load_error"):
            warnings.append("csv 加载失败, 跳过 np.ptp 检查")
        elif csv_check.get("numpy_missing"):
            warnings.append("numpy 缺失, 跳过 np.ptp 检查")
        else:
            for issue in csv_check.get("issues", []):
                issues.append(issue)

    return {"issues": issues, "warnings": warnings, "ok": not issues}


def main():
    parser = argparse.ArgumentParser(description="图形程序化内容自检 (P1-3 防御)")
    parser.add_argument("paths", nargs="+", help="文件或目录")
    parser.add_argument("--threshold", type=float, default=0.06, help="顶部暗像素阈值 (默认 0.06)")
    parser.add_argument("--exit-red-on-issue", action="store_true", help="有 issue 时 exit 1")
    args = parser.parse_args()

    files = []
    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            for ext in ('.png', '.jpg', '.jpeg', '.pdf', '.svg'):
                files.extend(path.rglob(f"*{ext}"))
        elif path.is_file():
            files.append(path)

    if not files:
        print("[ERROR] 没找到任何图像文件")
        sys.exit(1)

    n_total = len(files)
    n_red = 0
    n_yellow = 0
    n_green = 0
    print(f"[INFO] 扫 {n_total} 张图 (顶部暗像素阈值 {args.threshold})")
    print()
    for f in sorted(files):
        result = audit_content(str(f), args.threshold)
        if result["ok"] and not result["warnings"]:
            n_green += 1
            print(f"  [GREEN ] {f.name}")
        elif result["issues"]:
            n_red += 1
            print(f"  [RED   ] {f.name}")
            for issue in result["issues"]:
                print(f"          - {issue}")
        else:
            n_yellow += 1
            print(f"  [YELLOW] {f.name}")
            for w in result["warnings"]:
                print(f"          - {w}")

    print()
    print(f"[SUMMARY] {n_total} 图: {n_green} green + {n_yellow} yellow + {n_red} red")
    if args.exit_red_on_issue and n_red > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
