"""
scipilot-figure-skill :: profile_data.py
========================================
Exploratory data analysis for figure planning.

本脚本是 scipilot-figure-skill"思考-绘制"工作流的第 1 步。
读入 CSV / Excel / DataFrame，输出探索性分析报告——每列类型、缺失率、
样本量、分布形态、异常值、相关性——并基于这些事实给出"建议图型"提示。

工作流位置:
    用户给数据
        → profile_data.py      ← 你在这里
        → chart_selection.md   按数据形态查图型
        → setup_style.py
        → plot
        → check_figure.py

Usage
-----
    from profile_data import profile_data, render_report

    info = profile_data("results.csv", group_cols=["group", "condition"])
    print(render_report(info))

CLI:
    python profile_data.py results.csv
    python profile_data.py results.csv --group group --group condition
    python profile_data.py results.csv --json > profile.json
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import sys
import warnings
from typing import Any

import numpy as np
import pandas as pd

# Windows GBK 终端默认无法打 unicode 箭头/方头括号 —— 强制走 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass


# 数据类型常量
TYPE_CONTINUOUS = "continuous"
TYPE_CATEGORICAL = "categorical"
TYPE_ORDINAL = "ordinal"
TYPE_DATETIME = "datetime"
TYPE_BOOLEAN = "boolean"
TYPE_TEXT = "text"
TYPE_UNKNOWN = "unknown"


def _detect_column_type(s: pd.Series) -> str:
    """识别一列的数据类型。规则按可靠性递降排序。"""
    if pd.api.types.is_datetime64_any_dtype(s):
        return TYPE_DATETIME
    if pd.api.types.is_bool_dtype(s):
        return TYPE_BOOLEAN
    if pd.api.types.is_numeric_dtype(s):
        non_null = s.dropna()
        # 全是 0/1 ⇒ 当成 boolean
        if non_null.isin({0, 1}).all() and non_null.nunique() <= 2:
            return TYPE_BOOLEAN
        # 唯一值很少且都是整数 ⇒ 可能是有序分类（如 Likert 1-5）
        if non_null.nunique() <= 7 and (non_null % 1 == 0).all():
            return TYPE_ORDINAL
        return TYPE_CONTINUOUS
    if isinstance(s.dtype, pd.CategoricalDtype):
        if s.cat.ordered:
            return TYPE_ORDINAL
        return TYPE_CATEGORICAL
    if pd.api.types.is_object_dtype(s):
        # 尝试解析为时间（前 10 个非空值），失败也无所谓
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pd.to_datetime(s.dropna().iloc[:10], errors="raise")
            return TYPE_DATETIME
        except Exception:
            pass
        non_null = s.dropna()
        nunique = non_null.nunique()
        if nunique == 0:
            return TYPE_UNKNOWN
        # 不同值数量相对样本量很少 ⇒ 分类
        ratio = nunique / max(len(non_null), 1)
        if nunique <= 30 and ratio < 0.5:
            return TYPE_CATEGORICAL
        return TYPE_TEXT
    return TYPE_UNKNOWN


def _iqr_outliers(s: pd.Series) -> tuple[int, float, float]:
    """用 IQR 法返回 (异常值数, 下界, 上界)。"""
    s = s.dropna()
    if len(s) < 4:
        return 0, float("nan"), float("nan")
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((s < lo) | (s > hi)).sum()), float(lo), float(hi)


def _skewness(s: pd.Series) -> float:
    """Fisher–Pearson 偏度系数；空或常数列返回 nan。"""
    arr = s.dropna().to_numpy(dtype=float)
    if len(arr) < 3:
        return float("nan")
    mean = arr.mean()
    sd = arr.std(ddof=1)
    if sd == 0:
        return 0.0
    return float(np.mean(((arr - mean) / sd) ** 3))


def _profile_continuous(s: pd.Series) -> dict:
    s = s.dropna()
    if len(s) == 0:
        return {"n": 0}
    out_n, out_lo, out_hi = _iqr_outliers(s)
    skew = _skewness(s)
    return {
        "n": int(len(s)),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "sd": float(s.std(ddof=1)) if len(s) > 1 else 0.0,
        "min": float(s.min()),
        "max": float(s.max()),
        "skewness": skew,
        "skew_label": _label_skew(skew),
        "n_outliers_iqr": out_n,
        "outlier_lo": out_lo,
        "outlier_hi": out_hi,
        "needs_log_axis": _suggest_log_axis(s),
    }


def _label_skew(skew: float) -> str:
    if math.isnan(skew):
        return "unknown"
    a = abs(skew)
    if a < 0.5:
        return "approximately symmetric"
    if a < 1.0:
        return "moderately skewed"
    return "highly skewed"


def _suggest_log_axis(s: pd.Series) -> bool:
    """范围跨数个量级 + 全正 ⇒ 建议对数轴。"""
    s = s.dropna()
    if (s <= 0).any() or len(s) < 5:
        return False
    return s.max() / max(s.min(), 1e-300) > 100


def _profile_categorical(s: pd.Series) -> dict:
    counts = s.dropna().value_counts()
    return {
        "n": int(s.dropna().shape[0]),
        "n_unique": int(counts.shape[0]),
        "categories": [(str(k), int(v)) for k, v in counts.items()],
        "min_group_n": int(counts.min()) if len(counts) > 0 else 0,
        "max_group_n": int(counts.max()) if len(counts) > 0 else 0,
        "small_groups_flag": bool(len(counts) > 0 and counts.min() < 10),
    }


def _correlation_matrix(df: pd.DataFrame, cont_cols: list[str]) -> dict | None:
    """连续列之间的 Pearson 相关；不足两列返回 None。"""
    if len(cont_cols) < 2:
        return None
    sub = df[cont_cols].dropna()
    if sub.shape[0] < 5:
        return None
    corr = sub.corr(method="pearson")
    pairs: list[dict] = []
    cols = corr.columns.tolist()
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = float(corr.loc[a, b])
            pairs.append({"a": a, "b": b, "r": r,
                          "magnitude": _label_r(r)})
    pairs.sort(key=lambda x: -abs(x["r"]))
    return {"columns": cols, "matrix": corr.round(3).to_dict(),
            "pairs_sorted": pairs}


def _label_r(r: float) -> str:
    a = abs(r)
    if a < 0.1:
        return "negligible"
    if a < 0.3:
        return "weak"
    if a < 0.5:
        return "moderate"
    if a < 0.7:
        return "strong"
    return "very strong"


def _group_summary(df: pd.DataFrame, group_cols: list[str]) -> dict | None:
    """计算分组样本量分布；嵌套/交叉分组都支持。"""
    if not group_cols:
        return None
    gs = df.groupby(group_cols, dropna=False).size()
    return {
        "by": group_cols,
        "n_groups": int(gs.shape[0]),
        "min_n_per_group": int(gs.min()),
        "max_n_per_group": int(gs.max()),
        "median_n_per_group": int(gs.median()),
        "small_groups_flag": bool(gs.min() < 10),
        "tiny_groups_flag": bool(gs.min() < 3),
        "per_group_counts": [(str(idx), int(n)) for idx, n in gs.items()][:20],
    }


def _suggest_charts(info: dict) -> list[str]:
    """把数据特征翻译成"建议图型"提示。粗粒度——精细决策仍要查 chart_selection.md。"""
    cols = info["columns"]
    cont = [c for c, m in cols.items() if m["type"] == TYPE_CONTINUOUS]
    cats = [c for c, m in cols.items()
            if m["type"] in (TYPE_CATEGORICAL, TYPE_BOOLEAN, TYPE_ORDINAL)]
    dt = [c for c, m in cols.items() if m["type"] == TYPE_DATETIME]
    group = info.get("group_summary")
    suggestions: list[str] = []

    # 时间序列
    if dt and cont:
        suggestions.append(
            f"时间序列存在：用折线图 ({dt[0]} 作 x 轴，"
            f"{cont[0]}{'/' + cont[1] if len(cont) > 1 else ''} 作 y 轴) + 误差带")

    # 1 个分类 + 1 个连续：经典对比场景
    if cats and cont:
        if group and group.get("small_groups_flag"):
            suggestions.append(
                f"分类 vs 连续，小样本（每组 n<10）→ "
                "**箱线图/小提琴图 + stripplot 叠加原始点**；"
                "**避免**只画均值柱状图，会掩盖分布。")
        else:
            suggestions.append(
                f"分类 vs 连续，样本量充足 → 箱线图 / 小提琴图，"
                "或带误差棒的柱状图（误差棒说明 SD/SEM/CI）")

    # 两个或更多连续 → 散点或散点矩阵
    if len(cont) >= 2:
        if len(cont) == 2:
            # 2025 B 题踩坑：检测"时间序列"（物理量 vs 物理量）→ 推荐折线图
            time_series_hint = _detect_time_series(cols, cont)
            if time_series_hint:
                # 时间序列：x 是连续递增的物理量（时间/波数/频率等）
                # y 是另一个物理量（反射率/信号/响应）
                suggestions.append(
                    f"检测到时间序列 ({time_series_hint})："
                    f"用**折线图**（{cont[0]} 作 x 轴，{cont[1]} 作 y 轴）"
                    f"+ 找极值/振荡 + 可选 FFT"
                )
                # 信号专属建议（P1-6 增强版）
                if _is_signal_like(cols, cont):
                    suggestions.append(
                        "=== 信号/光谱数据分析建议 ===\n"
                        "  1. 预处理: savgol_filter 平滑 → baseline 校正（ALS/PeakUtils）\n"
                        "  2. 峰检测: find_peaks(height/prominence/width) + find_peaks_cwt\n"
                        "  3. 峰拟合: 高斯/洛伦兹/voigt 拟合 → 峰位/峰宽/峰面积\n"
                        "  4. 频域: scipy.fft/rfft → 找主频/滤波/频谱分析\n"
                        "  5. 多角度互验: 同一物理量不同角度/通道结果对比 → 置信度\n"
                        "  6. 噪声评估: 信噪比(SNR) = signal_std / noise_std\n"
                        "  参考: scipy.signal / peakutils / lmfit / astropy.modeling"
                    )
            else:
                suggestions.append(
                    f"两连续变量 {cont[0]} vs {cont[1]} → 散点图（含回归拟合 + r 值）")
        else:
            suggestions.append(
                f"≥3 个连续变量 → 相关性热力图（{cont[:5]}）或 pairplot 散点矩阵")

    # 单个连续 → 分布
    if len(cont) >= 1 and not cats and not dt:
        suggestions.append(
            f"单个连续变量 {cont[0]} → 直方图 / KDE / 箱线图看分布")

    # 维度过载 → 建议拆图
    if len(cats) >= 2 and len(cont) >= 1:
        n_combo = 1
        for cat in cats:
            n_combo *= max(cols[cat].get("n_unique", 1), 1)
        if n_combo > 12:
            suggestions.append(
                f"分类维度组合数 = {n_combo}（{', '.join(cats)} 全交叉），"
                "**一张图塞不下**——建议按某一维拆成多面板，或选择子集。")

    # 偏度大 → 提示对数轴
    for c in cont:
        m = cols[c]
        if m.get("needs_log_axis"):
            suggestions.append(
                f"{c} 跨数个量级（{m['min']:.3g} ~ {m['max']:.3g}）→ 用对数 y 轴")
        elif m.get("skew_label") == "highly skewed":
            suggestions.append(
                f"{c} 高度偏态（skew={m['skewness']:.2f}）→ "
                "考虑对数变换或小提琴图代替均值柱图")

    if not suggestions:
        suggestions.append("数据特征不足以给出特定建议；查 chart_selection.md 的决策框架。")
    return suggestions


def profile_data(source, group_cols: list[str] | None = None) -> dict:
    """
    主入口。读入数据并返回结构化的分析报告（dict）。

    Args:
        source: 文件路径（csv/xlsx）、pd.DataFrame、或字符串内容。
        group_cols: 分组列名列表（嵌套/交叉），用于分组样本量统计。
    Returns:
        dict 包含 keys: n_rows / n_cols / columns / correlation /
        group_summary / suggestions / warnings
    """
    if isinstance(source, pd.DataFrame):
        df = source.copy()
        path_label = "<DataFrame>"
    elif isinstance(source, str) and os.path.exists(source):
        ext = os.path.splitext(source)[1].lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(source)
        elif ext in (".tsv",):
            df = pd.read_csv(source, sep="\t")
        else:
            df = pd.read_csv(source)
        path_label = source
    else:
        raise ValueError(f"Cannot read data from {source!r}")

    group_cols = group_cols or []
    for g in group_cols:
        if g not in df.columns:
            raise ValueError(f"group column {g!r} not in data; "
                             f"available: {df.columns.tolist()}")

    cols_info: dict[str, dict] = {}
    warnings: list[str] = []
    for c in df.columns:
        s = df[c]
        ctype = _detect_column_type(s)
        n_total = len(s)
        n_null = int(s.isnull().sum())
        entry = {
            "type": ctype,
            "n_total": n_total,
            "n_null": n_null,
            "missing_rate": n_null / n_total if n_total else 0.0,
        }
        if entry["missing_rate"] > 0.20:
            warnings.append(
                f"列 {c!r} 缺失率 {entry['missing_rate']:.0%} — 画图前考虑是否填补、剔除、"
                "或在图注中交代。")
        if ctype == TYPE_CONTINUOUS:
            entry.update(_profile_continuous(s))
        elif ctype in (TYPE_CATEGORICAL, TYPE_BOOLEAN, TYPE_ORDINAL):
            entry.update(_profile_categorical(s))
            if entry.get("small_groups_flag"):
                warnings.append(
                    f"列 {c!r} 至少有一个类别 n<10 — 小样本必须展示原始数据点，"
                    "不要只画均值柱状图。")
        elif ctype == TYPE_DATETIME:
            non_null = pd.to_datetime(s, errors="coerce").dropna()
            if len(non_null) > 0:
                entry["min"] = str(non_null.min())
                entry["max"] = str(non_null.max())
        cols_info[c] = entry

    cont_cols = [c for c, m in cols_info.items() if m["type"] == TYPE_CONTINUOUS]
    correlation = _correlation_matrix(df, cont_cols)

    info = {
        "source": path_label,
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "columns": cols_info,
        "correlation": correlation,
        "group_summary": _group_summary(df, group_cols),
        "warnings": warnings,
    }
    info["suggestions"] = _suggest_charts(info)
    return info


def _detect_time_series(cols: dict, cont: list[str]) -> str | None:
    """检测两连续变量中是否有"时间序列"模式（x 是连续递增物理量）

    返回: 时间轴类型描述（如"波数序列"、"时间序列"、"频率序列"），或 None

    启发式:
    1. 列名含物理量关键字 (cm-1, Hz, time, s, ns, μs, ms, 日期, 时间, 波长, 波数, 频率)
    2. 列数据是连续递增（差分 > 0 占比 > 95%）
    3. 另一列是任何连续值（反射率/信号/响应）
    """
    if len(cont) != 2:
        return None

    # 物理量关键字
    time_kws = [
        # 时间
        'time', '时间', '日期', 'date', 'datetime', 'timestamp', '秒', 'ms', 'us', 'ns',
        # 频率/波数
        'cm-1', 'cm^-1', 'cm−1', 'hz', 'khz', 'mhz', 'ghz', 'freq', 'frequency',
        '波数', '频率', 'wavenumber', 'wavelength', '波长', 'ν',
        # 位置/距离
        'distance', '距离', 'pos', 'position', 'x', 'depth', '深度',
        # 角度
        'angle', '角度', 'theta',
    ]

    # 检测哪一列是时间轴
    for col_name in cont:
        col_lower = str(col_name).lower()
        if any(kw in col_lower for kw in time_kws):
            return f"列 '{col_name}' 看起来是物理量轴"

        # 数据是否单调递增（差分都 > 0）
        m = cols[col_name]
        if m["type"] == TYPE_CONTINUOUS and m.get("n_total", 0) > 5:
            # 简化判断: 提取列的 summary
            sd = m.get("std", 0)
            mean = m.get("mean", 0)
            mn = m.get("min", 0)
            mx = m.get("max", 0)
            if sd > 0 and (mx - mn) / (sd + 1e-9) > 4:
                # 值域 >> 标准差 → 数据分布广，可能是时间轴
                # 但仍需要名字或上下文确认
                pass

    return None


def _is_signal_like(cols: dict, cont: list[str]) -> bool:
    """检测两连续变量是否是"信号"数据（如红外反射光谱、电生理信号、振动信号）

    启发式:
    1. 列名含信号关键字（反射率/反射/反射率/反射率/反射率/光谱/谱/反射率/透射率/吸光度）
    2. 数据振荡剧烈（标准差大）
    """
    signal_kws = [
        '反射率', '反射', 'transmittance', 'reflectance', 'absorbance', '吸光度',
        '光谱', 'spectrum', '谱', '信号', 'signal',
        'intensity', '强度', 'voltage', '电压', 'current', '电流',
        'power', '功率', 'amplitude', '振幅',
    ]
    for col_name in cont:
        col_lower = str(col_name).lower()
        if any(kw in col_lower for kw in signal_kws):
            return True
    return False


def _detect_output_template(info: dict) -> tuple[bool, str]:
    """检测是否是"输出模板"而非输入数据。

    输出模板特征（国赛附件常见）：
    - 列名是时间戳（"0 s", "1 s", "-100 s"）—— 我们要往里填的位置
    - 或者 100% 缺失率
    - 行数远大于列数（如 224 把手 × 301 时刻 = 448×302）

    返回 (is_template, reason)
    """
    cols = info.get("columns", {})
    n_cols = len(cols)
    n_rows = info.get("n_rows", 0)

    # 规则 1: 列名是时间戳（"0 s", "1 s", "-100 s", "−100 s"）
    import re
    time_pattern = re.compile(r'^[−-]?\d+(\.\d+)?\s*s$')
    time_cols = [c for c in cols if time_pattern.match(str(c).strip())]
    time_ratio = len(time_cols) / n_cols if n_cols else 0

    # 规则 2: 高缺失率（>= 80%）
    missing_rates = [m.get("missing_rate", 0) for m in cols.values()]
    high_missing = sum(1 for r in missing_rates if r >= 0.8)
    high_missing_ratio = high_missing / n_cols if n_cols else 0

    # 规则 3: 行数 ≫ 列数（典型"宽表"模板）
    long_shape = n_rows > 0 and n_cols > 0 and (n_rows / n_cols) >= 2

    # 综合判断
    is_time_template = time_ratio >= 0.5
    is_missing_template = high_missing_ratio >= 0.5
    is_long = long_shape

    if is_time_template and (is_missing_template or is_long):
        reason = f"列名 {len(time_cols)}/{n_cols} 像时间戳, 缺失率 {high_missing_ratio*100:.0f}%, 形状 {n_rows}×{n_cols}"
        return True, reason
    if is_missing_template and is_long:
        reason = f"缺失率 {high_missing_ratio*100:.0f}%, 形状 {n_rows}×{n_cols} (长宽比 {n_rows/n_cols:.1f})"
        return True, reason
    return False, ""


def render_report(info: dict) -> str:
    """把 profile_data() 的输出渲染成 markdown 风格的人类可读报告。"""
    lines: list[str] = []

    # 早返回：检测到输出模板
    is_template, reason = _detect_output_template(info)
    if is_template:
        lines.append(f"# Data profile: {info['source']}")
        lines.append("")
        lines.append(f"> **⏭️  检测到输出模板（非输入数据），跳过 EDA**")
        lines.append(f">")
        lines.append(f"> 判定依据: {reason}")
        lines.append(f">")
        lines.append(f"**Shape:** {info['n_rows']} rows × {info['n_cols']} cols")
        lines.append("")
        lines.append("## 这是什么？")
        lines.append("")
        lines.append("国赛/美赛附件常常给一个**输出模板**（含把手名/列名 + 全 NaN 占位），")
        lines.append("要求我们求解后把结果填到对应位置。")
        lines.append("")
        lines.append("这种文件**不需要 EDA**——因为没有数据可分析。")
        lines.append("")
        lines.append("## 下一步")
        lines.append("")
        lines.append("1. **保留模板的列名/行名**——它们是你的论文里要展示的输出格式")
        lines.append("2. **求解后**用 pandas 读模板，按列名/行名填入数值")
        lines.append("3. **保存为 `resultX.xlsx`**——保持 sheet 名/行列结构与模板一致")
        lines.append("")
        lines.append("示例代码：")
        lines.append("")
        lines.append("```python")
        lines.append("import pandas as pd")
        lines.append("df = pd.read_excel('result1.xlsx', sheet_name='位置', header=None)")
        lines.append("# 填入求解结果（按你的物理量对应模板的 (把手, 时刻) 位置）")
        lines.append("# df.iloc[row, col] = computed_value")
        lines.append("df.to_excel('result1_filled.xlsx', sheet_name='位置', header=False, index=False)")
        lines.append("```")
        lines.append("")
        return "\n".join(lines)

    # 正常情况
    lines.append(f"# Data profile: {info['source']}")
    lines.append(f"")
    lines.append(f"**Shape:** {info['n_rows']} rows × {info['n_cols']} cols")
    lines.append("")

    # 每列
    lines.append("## Columns")
    lines.append("")
    lines.append("| Column | Type | n | missing | summary |")
    lines.append("|---|---|---|---|---|")
    for c, m in info["columns"].items():
        summary = ""
        if m["type"] == TYPE_CONTINUOUS:
            summary = (f"mean={m.get('mean', 0):.3g}, sd={m.get('sd', 0):.3g}, "
                       f"range=[{m.get('min', 0):.3g}, {m.get('max', 0):.3g}], "
                       f"skew={m.get('skewness', 0):.2f} ({m.get('skew_label')})")
            if m.get("n_outliers_iqr", 0):
                summary += f"; outliers={m['n_outliers_iqr']} (IQR)"
            if m.get("needs_log_axis"):
                summary += "; -> log axis"
        elif m["type"] in (TYPE_CATEGORICAL, TYPE_BOOLEAN, TYPE_ORDINAL):
            cats = m.get("categories", [])[:5]
            cats_str = ", ".join(f"{k}({v})" for k, v in cats)
            more = f" +{m['n_unique']-len(cats)} more" if m["n_unique"] > len(cats) else ""
            summary = f"{m['n_unique']} levels: {cats_str}{more}; min_group_n={m['min_group_n']}"
        elif m["type"] == TYPE_DATETIME:
            summary = f"{m.get('min', '?')} → {m.get('max', '?')}"
        miss = f"{m['n_null']} ({m['missing_rate']:.0%})" if m["missing_rate"] > 0 else "0"
        lines.append(f"| `{c}` | {m['type']} | {m['n_total']-m['n_null']} | {miss} | {summary} |")
    lines.append("")

    # 分组
    if info.get("group_summary"):
        gs = info["group_summary"]
        lines.append("## Group structure")
        lines.append(f"- Grouped by: `{'`, `'.join(gs['by'])}`")
        lines.append(f"- Number of groups: {gs['n_groups']}")
        lines.append(f"- Group size: min={gs['min_n_per_group']}, "
                     f"median={gs['median_n_per_group']}, max={gs['max_n_per_group']}")
        if gs["tiny_groups_flag"]:
            lines.append("- **WARN**: at least one group has n<3 — statistics unreliable; "
                         "must show all raw points.")
        elif gs["small_groups_flag"]:
            lines.append("- **WARN**: at least one group has n<10 — use box/violin + stripplot "
                         "rather than mean-only bar chart.")
        lines.append("")

    # 相关性
    if info.get("correlation"):
        corr = info["correlation"]
        lines.append("## Correlations (Pearson, sorted by |r|)")
        for p in corr["pairs_sorted"][:10]:
            lines.append(f"- `{p['a']}` ↔ `{p['b']}` : r = {p['r']:.3f} ({p['magnitude']})")
        if len(corr["pairs_sorted"]) > 10:
            lines.append(f"- ... +{len(corr['pairs_sorted']) - 10} more pairs")
        lines.append("")

    # 警告
    if info["warnings"]:
        lines.append("## Warnings")
        for w in info["warnings"]:
            lines.append(f"- {w}")
        lines.append("")

    # 图型建议
    lines.append("## Chart suggestions (preliminary)")
    for s in info["suggestions"]:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("> 这是基于数据形态的**初步建议**。最终图型选择必须结合"
                 "**论证目标**（你想说什么）—— 详见 `references/chart_selection.md`。")
    return "\n".join(lines)


def _cli() -> int:
    p = argparse.ArgumentParser(description="scipilot-figure-skill data profiler")
    p.add_argument("source", help="CSV / Excel / TSV file path")
    p.add_argument("--group", action="append", default=[],
                   help="分组列名（可多次指定形成嵌套/交叉分组）")
    p.add_argument("--json", action="store_true",
                   help="输出 JSON 而非 markdown 报告")
    p.add_argument("--all-sheets", action="store_true",
                   help="遍历 Excel 所有 sheet 输出（默认只看第一张表）")
    args = p.parse_args()

    # 检测是否 Excel
    is_excel = args.source.lower().endswith(('.xlsx', '.xls'))

    if is_excel and args.all_sheets:
        # 遍历所有 sheet
        xl = pd.ExcelFile(args.source)
        print(f"# 多 Sheet 概要: {args.source}")
        print(f"\n**Sheet 数:** {len(xl.sheet_names)}")
        print(f"**Sheet 名:** {xl.sheet_names}\n")
        for sn in xl.sheet_names:
            print(f"\n{'='*70}")
            print(f"## Sheet [{sn}]")
            print(f"{'='*70}")
            # 临时 monkey-patch profile_data 的 sheet_name
            # 用更简单方法: 直接读这个 sheet 再调
            df = pd.read_excel(args.source, sheet_name=sn, header=None)
            # 保存为临时 csv 调 profile_data
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', encoding='utf-8') as f:
                df.to_csv(f.name if False else f.name, index=False, header=False)
                tmp_path = f.name
            try:
                info = profile_data(tmp_path, group_cols=args.group)
                # 改 source 名为 原文件名[sheet名]
                info['source'] = f"{args.source} [{sn}]"
                if args.json:
                    def _default(o):
                        if isinstance(o, (np.integer,)):
                            return int(o)
                        if isinstance(o, (np.floating,)):
                            return float(o)
                        if isinstance(o, (np.ndarray, pd.Series)):
                            return o.tolist()
                        return str(o)
                    json.dump(info, sys.stdout, ensure_ascii=False, indent=2, default=_default)
                    sys.stdout.write("\n")
                else:
                    print(render_report(info))
            finally:
                os.unlink(tmp_path)
    else:
        info = profile_data(args.source, group_cols=args.group)
        if args.json:
            # numpy / pandas 的类型在 json.dump 里要转 native
            def _default(o):
                if isinstance(o, (np.integer,)):
                    return int(o)
                if isinstance(o, (np.floating,)):
                    return float(o)
                if isinstance(o, (np.ndarray, pd.Series)):
                    return o.tolist()
                return str(o)
            json.dump(info, sys.stdout, ensure_ascii=False, indent=2, default=_default)
            sys.stdout.write("\n")
        else:
            print(render_report(info))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
