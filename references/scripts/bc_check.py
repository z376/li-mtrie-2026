# -*- coding: utf-8 -*-
"""bc_check.py — 表面行能量守恒校验器 (v1.6.3 新增, 2026A 复盘 v1.1 §验收标准 第 1/2 条).

背景 (2026A v15 P0-1 的决定性证据):
    温度场 build_surface_row 返回 (1.0, 1+beta, beta), beta = h*dr/alpha (**无 dt**),
    等价于 h->inf 极限, 表面被错误地钉死在 T_amb (题面给的是有限 h=25).

    判定式:   ratio = dE/dt / [h*(T_inf - T_s)*A]
        错格式 (1, 1+beta, beta)  -> ratio = 223   (不可能的 223 倍)
        真 Robin (1+2mu+gamma)    -> ratio = 0.995
    => |ratio - 1| 必须 < 0.05. 偏离一个数量级 = 离散式必错, 不是数值误差.

本脚本把"守恒校验"从"代理审计时人工手推"变成"求解时自动记录 + 一条命令出报告":

用法 A (求解时接入, 2 行):
    from bc_check import ConservationRecorder
    rec = ConservationRecorder(tol=0.05)
    for step in ...:
        ...
        rec.record(t, E_total, flux_boundary)   # E_total=系统总能量, flux_boundary=边界净流入(流入为正)
    rec.save("结果/守恒记录.csv")

用法 B (跑完出报告):
    py bc_check.py --csv 求解/问题1/结果/守恒记录.csv
    py bc_check.py --project .                  # 扫 求解/ 下所有 守恒记录*.csv
    py bc_check.py --demo                       # 自测 (内置 对/错 两组数据, 错组复现 P0-1 的 223)

退出码: 0 = 守恒成立, 1 = 守恒被破坏, 2 = 用法/读取错误.

约定 (与 验收清单.md §J 一致):
    - 环境用 `py` 而非 `python` (Windows 商店占位符 exit 49), 本脚本强制 UTF-8 输出.
    - 记录文件默认落 `求解/问题N/结果/守恒记录.csv` (dryrun check 64 自动扫这个路径).
    - 记录 CSV 列序: t, E_total, flux_boundary (有表头则按表头识别).
"""
import argparse
import csv
import sys
from pathlib import Path

# Windows GBK 终端兼容 (2025 B 题踩坑 + 2026A 复盘附录 A 要求)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DEFAULT_TOL = 0.05
# 守恒记录文件名约定 (求解时约定, dryrun check 64 按此扫描)
RECORD_GLOBS = ("守恒记录*.csv", "bc_record*.csv", "conservation*.csv")
# 零通量判定阈值 (相对系统量级, 避免除零)
FLUX_EPS = 1e-15


class ConservationRecorder:
    """守恒校验记录器 — 求解循环里每步记一行 (t, E_total, flux_boundary).

    物理约定:
        E_total        系统总能量 (J), 随时间变化
        flux_boundary  边界净通量 (W), **流入系统为正** (与 dE/dt 同号)
        => 守恒成立时 dE/dt / flux_boundary ≈ 1

    典型接入 (机理题 / FVM 题):
        rec = ConservationRecorder(tol=0.05)
        for n in range(n_steps):
            ...                                   # 推进一个时间步
            rec.record(t[n+1], total_energy(), boundary_net_flux())
        rec.save("结果/守恒记录.csv")
    """

    def __init__(self, tol=DEFAULT_TOL, name="surface"):
        self.tol = float(tol)
        self.name = name
        self.rows = []          # [(t, E_total, flux_boundary), ...]

    def record(self, t, E_total, flux_boundary):
        """记一行. 三个参数都强制转 float, 传 numpy 标量也安全."""
        self.rows.append((float(t), float(E_total), float(flux_boundary)))

    # 兼容别名 (用户可能写成 rec.log(...) / rec.add(...))
    log = record
    add = record

    def report(self):
        """返回 verify_rows 结果 dict."""
        return verify_rows(self.rows, tol=self.tol, name=self.name)

    def save(self, path):
        """落盘 CSV (UTF-8, 带表头). 返回 Path."""
        path = Path(path)
        if path.parent and str(path.parent):
            path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["t", "E_total", "flux_boundary"])
            for t, e, fl in self.rows:
                w.writerow([f"{t:.10g}", f"{e:.10g}", f"{fl:.10g}"])
        return path

    def __len__(self):
        return len(self.rows)


def verify_rows(rows, tol=DEFAULT_TOL, name="surface"):
    """dE/dt ÷ 边界通量, 判定 |ratio - 1| <= tol.

    返回 dict:
        ok         bool, 守恒是否成立
        n_valid    int,  有效区间数 (dt>0 且通量非零)
        n_skipped  int,  跳过区间数
        ratios     list, 每个有效区间的 ratio
        worst      float, |ratio-1| 最大的那个 ratio (最坏点)
        mean_ratio float, 所有 ratio 的均值
        reason     str,   判定理由 (可直接贴进审计报告)
    """
    rows = sorted([tuple(float(x) for x in r) for r in rows], key=lambda r: r[0])
    ratios = []
    skipped = 0
    for i in range(len(rows) - 1):
        t0, e0, f0 = rows[i]
        t1, e1, f1 = rows[i + 1]
        dt = t1 - t0
        if dt <= 0:
            skipped += 1
            continue
        dedt = (e1 - e0) / dt
        # 通量取区间中值 (线性插值), 避免端点单边取值带来的相位偏差
        flux = 0.5 * (f0 + f1)
        if abs(flux) < FLUX_EPS:
            skipped += 1
            continue
        ratios.append(dedt / flux)

    base = {"name": name, "n_valid": len(ratios), "n_skipped": skipped,
            "ratios": ratios, "worst": None, "mean_ratio": None, "ok": False}
    if len(ratios) < 3:
        base["reason"] = (f"有效区间不足 ({len(ratios)} < 3), 无法判定守恒 "
                          f"(至少记 4 个时刻)")
        return base

    worst = max(ratios, key=lambda r: abs(r - 1.0))
    mean_ratio = sum(ratios) / len(ratios)
    ok = abs(worst - 1.0) <= tol
    base.update({
        "ok": ok,
        "worst": worst,
        "mean_ratio": mean_ratio,
        "reason": (f"守恒成立 (最差 ratio={worst:.4f}, |ratio-1|={abs(worst-1.0):.4f} <= {tol})"
                   if ok else
                   f"守恒被破坏: 最差 ratio={worst:.4f} (|ratio-1|={abs(worst-1.0):.4f} > tol {tol}) "
                   f"— 离散式几乎必错 (P0-1 型), 别当成数值误差放过"),
    })
    return base


def _to_float(s):
    try:
        return float(str(s).strip())
    except (TypeError, ValueError):
        return None


def read_record_csv(path):
    """读守恒记录 CSV -> [(t, E_total, flux_boundary), ...].

    容错:
    - 第一行若第 1 列不是数字, 当表头跳过
    - 有表头时按关键字定位列 (t / E / flux, 支持中文"时间/能量/通量")
    - 无表头时按列序 0/1/2
    """
    path = Path(path)
    header = None
    data = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if not row or all(not str(c).strip() for c in row):
                continue
            first = _to_float(row[0])
            if first is None:
                if header is None:
                    header = [str(c).strip().lower() for c in row]
                continue
            data.append([_to_float(c) for c in row])

    if not data:
        return []

    idx_t, idx_e, idx_f = 0, 1, 2
    if header:
        def find(keys, default):
            for i, name in enumerate(header):
                for k in keys:
                    if k in name:
                        return i
            return default
        idx_t = find(["time", "时间", "t_", "t "], 0)
        idx_e = find(["e_total", "energy", "总能量", "能量", "e_"], 1)
        idx_f = find(["flux", "通量", "边界", "q_"], 2)

    out = []
    for r in data:
        try:
            out.append((r[idx_t], r[idx_e], r[idx_f]))
        except IndexError:
            continue
    return out


def find_record_files(root):
    """在 root 下递归找守恒记录 CSV (跳过 .git / 支撑材料包)."""
    root = Path(root)
    found = []
    for pat in RECORD_GLOBS:
        for p in root.rglob(pat):
            s = str(p)
            if ".git" in s or "支撑材料" in s or "node_modules" in s:
                continue
            found.append(p)
    return sorted(set(found))


def run_demo(verbose=True):
    """内置自测: 对/错两组数据, 验证工具本身能区分.

    错组复现 2026A P0-1 的决定性证据 (ratio = 223).
    返回 dict: {"good": report, "bad": report, "pass": bool}
    """
    # 对: E 线性下降 2.5 W, 边界净流出 2.5 W -> ratio = 1
    good = ConservationRecorder(name="demo-good")
    for i in range(11):
        t = float(i)
        good.record(t, 100.0 - 2.5 * t, -2.5)

    # 错: 表面被钉死 (h->inf 极限) -> E 以 557.5 W 掉, 通量仍 2.5 W -> ratio = 223
    bad = ConservationRecorder(name="demo-bad")
    for i in range(11):
        t = float(i)
        bad.record(t, 100.0 - 557.5 * t, -2.5)

    g = good.report()
    b = bad.report()
    ok = bool(g["ok"]) and (not b["ok"]) and abs((b["worst"] or 0) - 223.0) < 5.0
    if verbose:
        print("[bc_check] 自测 (demo)")
        print(f"  [对组] {g['reason']}")
        print(f"  [错组] {b['reason']}")
        print(f"  判定: {'PASS (工具能区分对/错)' if ok else 'FAIL (工具自身失效!)'}")
    return {"good": g, "bad": b, "pass": ok}


def _print_report(path, rep):
    print(f"[bc_check] {path}")
    print(f"  有效区间 {rep['n_valid']} / 跳过 {rep['n_skipped']}")
    if rep["ratios"]:
        print(f"  ratio: min {min(rep['ratios']):.4f}  max {max(rep['ratios']):.4f}  "
              f"mean {rep['mean_ratio']:.4f}  worst {rep['worst']:.4f}")
    print(f"  判定: {'PASS' if rep['ok'] else 'FAIL'} — {rep['reason']}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="表面行能量守恒校验器 (dE/dt ÷ 边界通量 ≈ 1)")
    ap.add_argument("--csv", help="守恒记录 CSV 路径 (t, E_total, flux_boundary)")
    ap.add_argument("--project", help="项目根目录 (扫 求解/ 下所有 守恒记录*.csv)")
    ap.add_argument("--demo", action="store_true", help="跑内置自测 (对/错两组数据)")
    ap.add_argument("--tol", type=float, default=DEFAULT_TOL,
                    help=f"判定阈值 |ratio-1| <= tol (默认 {DEFAULT_TOL})")
    args = ap.parse_args(argv)

    if args.demo:
        res = run_demo(verbose=True)
        return 0 if res["pass"] else 1

    if not args.csv and not args.project:
        ap.print_help()
        return 2

    targets = []
    if args.csv:
        targets.append(Path(args.csv))
    if args.project:
        targets.extend(find_record_files(args.project))

    if not targets:
        print("[bc_check] 没找到守恒记录 CSV. "
              "求解时用 ConservationRecorder.record(t, E, flux) 记录并 save('结果/守恒记录.csv')")
        return 2

    all_ok = True
    any_data = False
    for path in targets:
        if not path.exists():
            print(f"[bc_check] 跳过 (不存在): {path}")
            continue
        rows = read_record_csv(path)
        if not rows:
            print(f"[bc_check] 跳过 (无有效数据行): {path}")
            continue
        any_data = True
        rep = verify_rows(rows, tol=args.tol, name=path.stem)
        _print_report(path, rep)
        if not rep["ok"]:
            all_ok = False

    if not any_data:
        return 2
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
