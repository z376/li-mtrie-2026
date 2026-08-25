# -*- coding: utf-8 -*-
"""
问题X：【问题简述 — 机理题】
方法：【主要方法 — 几何/运动学/物理推导】

═══════════════════════════════════════════════════════════════
🆕 **机理题专用模板**（与 code-template.py 区别）
═══════════════════════════════════════════════════════════════

适用题型：
- A 题（机理建模）：物理过程、几何运动、轨迹优化
- B 题（部分机理）：工程系统、调度网络
- D 题（评价决策）：AHP/TOPSIS 评分计算
- 美赛：连续型/离散型机制建模

与 code-template.py (数据驱动) 的区别：
- ✅ 物理参数集中定义（板长、螺距、阻尼系数等）
- ✅ 几何/运动学核心函数区（参数方程、约束、变换）
- ✅ 数值方法工具（scipy.optimize / integrate / linalg）
- ✅ 性能警示：O(N²) 循环 → numpy 向量化示例
- ✅ 时间步进模板（dt, t_array, snapshot）
- ❌ 不再强制"先加载数据再做分析"
- ❌ 不需要 KNN 插补 / 标准化 / 缺失值处理

⚠️ **使用建议**：
1. **不要复制数据驱动模板**到机理题——会浪费 30 分钟重写
2. **优先建立共享模块**（`求解/共享/物理模型.py`），多个问题复用
3. **每写完一个函数就验证**（用 print 或 assert），不要堆到最后

═══════════════════════════════════════════════════════════════
⚠️ **Windows GBK 终端兼容**（重要，2025 B 题踩坑）
═══════════════════════════════════════════════════════════════

**避免在 print 字符串中使用**（GBK 终端会报 `UnicodeEncodeError`）：
- ❌ Emoji: ✅ ❌ ⚠️ ⏭️ 🎉
- ❌ 特殊符号: ✓ ✗ → ← ※ ① ②
- ❌ Unicode 上下标: cm⁻¹ m² ½ ¹²
- ❌ 希腊字母 + 波浪线: ν̃ θ̃ Δν

**改用 ASCII 替代**：
- ✅ → `[OK]`
- ❌ → `[X]` 或 `False`
- ⚠️ → `[WARN]`
- → → `->`
- cm⁻¹ → `cm-1`
- ν̃ → `nu` 或 `nu_tilde`
- 希腊字母: θ → `theta`, μ → `mu`, Δ → `delta`

**或者**在脚本顶部加（强制 UTF-8 输出）：
```python
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

**经验**：写代码时**默认用 ASCII**，只在文档/字符串里用 Unicode 注释解释。

🆕 自检闭环集成（v1.0）：
- save_fig()   基础版：仅保存
- save_fig_with_qa()  增强版：保存后自动跑 visual_qa 缺字/越界/重叠自检
"""
import os, sys, time
import numpy as np
import pandas as pd

# ==================== ⚠️ Windows GBK 终端兼容(自动应用) ====================
# 模板里有 emoji (✅ ❌ ⚠️) 在 GBK 终端下 print 会报 UnicodeEncodeError
# 这里在 import 阶段就强制 UTF-8,调用方无需关心
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # Python < 3.7 或 stream 已关闭时降级到 TextIOWrapper
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass


# ==================== 数值方法（按需启用）====================
# 数值积分:  from scipy.integrate import quad, solve_ivp, odeint
# 方程求根:  from scipy.optimize import brentq, fsolve, root
# 最优化:    from scipy.optimize import minimize, linprog, milp
# 线性代数:  from scipy.linalg import solve, eig
# 插值:      from scipy.interpolate import interp1d, CubicSpline
# 信号处理:  from scipy.signal import savgol_filter

# ==================== ⚠️ 性能警示 ====================
# 机理题常见性能陷阱：
#   1. 时间步进循环里调用 scipy.optimize → 每步 1ms，1000 步 = 1s
#   2. O(N²) 距离计算（如碰撞检测）→ 224² = 50k 对，500 步 = 2500 万次
#   3. 反解方程 brentq 调用频繁 → 缓存结果

# ❌ 错误示例（O(N²) 循环，500 步会跑 2 分钟）：
# for t in times:
#     positions = np.zeros((N, 2))
#     for i in range(N):
#         for j in range(i+2, N):
#             sep = np.linalg.norm(positions[i] - positions[j])  # 慢！

# ✅ 正确示例（numpy 向量化，500 步 < 1 秒）：
# for t in times:
#     positions = np.zeros((N, 2))
#     diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]  # (N, N, 2)
#     dists = np.sqrt((diff * diff).sum(axis=2))  # (N, N) 距离矩阵
#     upper_dists = dists[np.triu(np.ones((N, N), dtype=bool), k=2)]
#     min_sep = upper_dists.min()

# ==================== visual_qa 集成 ====================
try:
    _SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _SCRIPTS = os.path.join(_SKILL_ROOT, 'references', 'scripts')
    if os.path.isdir(_SCRIPTS):
        sys.path.insert(0, _SCRIPTS)
        from visual_qa import audit_layout, render_preview
        _HAS_VISUAL_QA = True
    else:
        _HAS_VISUAL_QA = False
except Exception:
    _HAS_VISUAL_QA = False


# ==================== 绘图全局配置 ====================
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    # 字体（中文必须显式指定）
    'font.sans-serif': ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans'],
    'font.family': 'sans-serif',
    'axes.unicode_minus': False,
    # 字号（论文里要清晰可读）
    'font.size': 14,
    'axes.titlesize': 16,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 13,
    'figure.titlesize': 16,
    # 线条 / 标记
    'lines.linewidth': 2.0,
    'lines.markersize': 8,
    'axes.linewidth': 1.2,
    # 保存
    'figure.dpi': 120,
    'savefig.dpi': 200,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'savefig.facecolor': 'white',
    # 子图布局
    'figure.constrained_layout.use': True,
})


# ==================== 目录配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, '图片')
OUT_DIR = os.path.join(BASE_DIR, '结果')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)


# ==================== 数据目录自动扫描（备用，机理题通常无外部数据）====================
def scan_data_dir(data_dir='数据'):
    """扫描 数据/ 目录，自动发现数据文件并返回路径字典。

    机理题通常无外部数据, 但有些题目会给附件(如 2024 A 题给 result1/2/4.xlsx).
    此函数方便用户快速发现项目根目录或上层 数据/ 里的附件.

    返回:
        dict: { 'xlsx': [...], 'csv': [...], 'txt': [...], 'img': [...] }
              值为相对于 data_dir 的相对路径列表
    """
    data_dir = os.path.abspath(data_dir)
    if not os.path.isdir(data_dir):
        print(f"[WARN] 数据目录不存在: {data_dir}")
        return {}

    result = {'xlsx': [], 'csv': [], 'txt': [], 'img': [], 'other': []}
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), data_dir)
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.xlsx', '.xls'):
                result['xlsx'].append(rel)
            elif ext == '.csv':
                result['csv'].append(rel)
            elif ext in ('.txt', '.dat', '.tsv'):
                result['txt'].append(rel)
            elif ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif'):
                result['img'].append(rel)
            else:
                result['other'].append(rel)

    print(f"\n{'='*50}")
    print(f"数据目录扫描结果: {data_dir}")
    print(f"{'='*50}")
    for category, files in result.items():
        if files:
            print(f"\n{category.upper()} ({len(files)} 个):")
            for f in sorted(files):
                size_kb = os.path.getsize(os.path.join(data_dir, f)) / 1024
                print(f"  {f} ({size_kb:.1f} KB)")
    if not any(result.values()):
        print("\n[INFO] 数据目录为空（机理题通常无外部数据）")
    return result


# ==================== § 1  物理参数集中定义 ====================
# 命名规范：大写字母下划线分隔
# 例：PITCH（螺距）、L_HEAD（龙头板长）、MU（摩擦系数）

# TODO: 按题面填物理参数
# 示例（板凳龙）:
# L_HEAD = 3.41       # 龙头板长 (m)
# L_BODY = 2.20       # 龙身板长 (m)
# D_HANDLE = 0.275    # 把手到板头距离 (m)
# W_BOARD = 0.30      # 板宽 (m)
# PITCH = 0.55        # 螺距 (m)
# V_HEAD = 1.0        # 龙头速度 (m/s)
# N_SECTIONS = 223    # 板凳总节数

PHYSICAL_PARAMS = {
    # 'L_HEAD': 3.41,
    # 'PITCH': 0.55,
    # 'V_HEAD': 1.0,
    # ...
}


# ==================== § 2  几何/运动学核心函数 ====================

# TODO: 在这里定义你的几何/运动学函数
# 建议：每个函数都加 docstring，说明输入/输出/单位/物理意义
# 示例（螺线）:
# def xy_of_theta(theta, p):
#     """螺线 (x, y) 坐标
#     theta: 极角 (rad)
#     p: 螺距 (m)
#     返回: (x, y) (m)
#     """
#     r = p * theta / (2 * np.pi)
#     return r * np.cos(theta), r * np.sin(theta)


# ==================== § 3  数值求解器 ====================

# TODO: 按算法选型填
# 例:  反解方程
# from scipy.optimize import brentq
# theta_final = brentq(lambda th: arc_length(th, p) - s_target, 0, 200)
#
# 例: 二分搜索
# lo, hi = 0.1, 5.0
# for _ in range(50):
#     mid = (lo + hi) / 2
#     if check(mid): lo = mid
#     else: hi = mid
#
# 例: 数值积分
# from scipy.integrate import quad
# s, _ = quad(integrand, 0, theta, limit=200)


# ==================== § 4  时间步进 ====================
# 机理题标准时间步进模板
#
# T_TOTAL = 300.0       # 总时长 (s)
# DT = 1.0              # 采样间隔 (s)
# times = np.arange(0, T_TOTAL + DT, DT)
#
# # 状态量: (T, N, ...) — 时间 × 空间点 × 状态
# positions = np.zeros((len(times), N_HANDLES, 2))
# speeds = np.zeros((len(times), N_HANDLES))
#
# t0 = time.time()
# for ti, t in enumerate(times):
#     # TODO: 计算 t 时刻各点状态
#     #   positions[ti] = ...
#     #   speeds[ti] = ...
#     if ti % 50 == 0:
#         print(f'  t={t:.0f}s ({ti}/{len(times)})')
# print(f'耗时: {time.time() - t0:.2f}s')


# ==================== § 5  输出 result.xlsx ====================
# ⚠️ **国赛附件名是固定的（result1.xlsx / result2.xlsx / result4.xlsx）**——必须保留原名
# 但**保存路径**要明确放在对应问题目录下，避免与原附件混淆
#
# 推荐路径: 求解/问题X/结果/resultX.xlsx
# 例: 求解/问题1/结果/result1.xlsx
#
# ⚠️ **result 命名规则**（2024 国赛测试 A/C 两题命名规范对比）：
#
# | 题型        | 命名规则        | 例                      |
# |-------------|-----------------|-------------------------|
# | A 题（机理）| `resultX.xlsx`  | result1/2/4.xlsx        |
# | C 题（数据）| `resultX_Y.xlsx`| result1_1/1_2/2.xlsx（问题X 的子问题Y）|
# |             | `resultX.xlsx`  | result3.xlsx（单结果）  |
# | 通用        | **保留题面附件原名**，不要改名（如把 result1.xlsx 改成 my_result1.xlsx）|
#
# **错误示范**：
#   ❌ result_问题1.xlsx          # 题面附件不认这个名
#   ❌ 第1问结果.xlsx              # 中文名 + 空格，部分系统读不了
#   ❌ result1_v2_最终版.xlsx     # 带版本号，提交后评审不知道哪个是最终
#
# **正确示范**：
#   ✓ 求解/问题1/结果/result1.xlsx
#   ✓ 求解/问题3/结果/result1_1.xlsx  （C 题子问题 1.1）
#
# ⚠️ **xlsx 模板填写注意事项**（2024 C 题踩坑）：
#   1. 模板单元格混合 string（地块名/季次标签）和 float（NaN 数值）
#   2. 直接 `df.iloc[i, j] = 0.0` 会触发 string dtype 检查 → TypeError
#   3. **必须**先 `df = df.astype(object)` 再 iloc 写
#   4. 保存时**所有 sheet 都要重新转 object**，否则仍有 dtype 冲突
#
# ⚠️ **多 sheet 模板**（如 C 题 result1_1 有 7 sheet = 7 年）：
#   1. 用 `pd.ExcelFile` 读所有 sheet 名
#   2. 对每个 sheet 单独处理
#   3. 保存时用 `ExcelWriter` 写所有 sheet（不要只写改过的）

# 模板读取（不要动附件原文件）:
#   template = pd.read_excel('../../数据/result1.xlsx', sheet_name='位置', header=None)
#
# 填入示例（单 sheet）:
#   template = template.astype(object)  # ⭐ 关键: 先转 object
#   for ti, t in enumerate(times):
#       for hi in range(N_HANDLES):
#           template.iloc[2*hi, ti+1] = round(positions[ti, hi, 0], 6)
#           template.iloc[2*hi+1, ti+1] = round(positions[ti, hi, 1], 6)
#   template.astype(object).to_excel('结果/result1.xlsx', sheet_name='位置', header=False, index=False)
#
# 填入示例（多 sheet，如 7 年 7 sheet）:
#   all_sheets = {}
#   for sn in pd.ExcelFile('../../数据/附件3/result1_1.xlsx').sheet_names:
#       all_sheets[sn] = pd.read_excel('../../数据/附件3/result1_1.xlsx', sheet_name=sn, header=None).astype(object)
#   # 修改 all_sheets['2024'] 的某些单元格
#   all_sheets['2024'].iloc[1, 2] = 5.0  # 举例
#   # 保存所有 sheet
#   with pd.ExcelWriter('结果/result1_1_filled.xlsx', engine='openpyxl') as w:
#       for sn, df in all_sheets.items():
#           df.to_excel(w, sheet_name=sn, header=False, index=False)


# ==================== 工具函数 ====================

def save_csv(df, name_cn):
    """保存 CSV"""
    df.to_csv(os.path.join(OUT_DIR, name_cn), index=False, encoding='utf-8-sig')
    print(f"  [CSV] {name_cn} 已保存")


def print_stats(data, name="数据", cols=None):
    """打印数据统计信息（供论文引用）"""
    if cols is None:
        cols = data.select_dtypes(include=[np.number]).columns.tolist()
    print(f"\n{'='*60}")
    print(f"  {name} 统计摘要")
    print(f"{'='*60}")
    for col in cols:
        s = data[col].dropna()
        if len(s) == 0:
            continue
        print(f"  {col}:")
        print(f"    min={s.min():.4f}  max={s.max():.4f}  mean={s.mean():.4f}")
        cv_str = f"cv={s.std()/s.mean()*100:.1f}%" if s.mean() != 0 else "cv=N/A"
        print(f"    std={s.std():.4f}  {cv_str}  amp={s.max()-s.min():.4f}")
    print(f"{'='*60}\n")


def save_fig(fig, name_cn, dpi=200):
    """保存图片到 FIG_DIR"""
    out = os.path.join(FIG_DIR, name_cn)
    fig.savefig(out, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  [FIG] {name_cn} 已保存 ({os.path.getsize(out)//1024} KB)")


def save_fig_with_qa(fig, name_cn, dpi=200, ai_review=True):
    """🆕 增强版 save_fig：保存后自动跑 visual_qa 自检

    自动检测：
    - 缺字乱码（FAIL）：matplotlib 缺字警告
    - 文字越界裁切（WARN）：Text 超出画布
    - 刻度标签重叠（WARN）：相邻 tick label 包围盒相交

    可选 ai_review=True 时：同时渲一张中分辨率 PNG 预览（给 AI 读图复核感知性问题）
    """
    out = os.path.join(FIG_DIR, name_cn)
    fig.savefig(out, dpi=dpi, bbox_inches='tight', facecolor='white')

    if not _HAS_VISUAL_QA:
        print(f"  [FIG] {name_cn} 已保存 ({os.path.getsize(out)//1024} KB) [QA 不可用]")
        plt.close(fig)
        return

    issues = audit_layout(fig)
    fail = [m for s, m in issues if s == 'FAIL']
    warn = [m for s, m in issues if s == 'WARN']

    if fail:
        print(f"  [FIG] {name_cn} 已保存 ❌ QA 失败 ({len(fail)} FAIL):")
        for m in fail:
            print(f"        - {m}")
    elif warn:
        print(f"  [FIG] {name_cn} 已保存 ⚠️  QA 警告 ({len(warn)} WARN):")
        for m in warn[:3]:
            print(f"        - {m}")
        if len(warn) > 3:
            print(f"        - ... 等 {len(warn)-3} 条")
    else:
        print(f"  [FIG] {name_cn} 已保存 ✅ QA 通过")

    if ai_review:
        preview_path = out.rsplit('.', 1)[0] + '_预览.png'
        try:
            render_preview(fig, preview_path, dpi=120)
            print(f"        AI 读图预览: {os.path.basename(preview_path)}")
        except Exception as e:
            print(f"        (预览生成失败: {e})")

    plt.close(fig)


def gen_handle_names(n_total, n_head=1, n_tail=1):
    """🆕 自动生成把手/节点名称列表，避免长度错配

    用于序列型实体命名（如板凳龙的 224 个把手、桁架的 N 个节点）

    参数:
        n_total: 总数
        n_head: 头部实体数（默认 1）
        n_tail: 尾部实体数（默认 1）

    返回:
        list[str]: 名称列表
        例: gen_handle_names(224) →
            ['龙头前', '第1节龙身', ..., '第221节龙身', '龙尾前', '龙尾后']

    使用场景:
        n_handles = 224
        handle_names = gen_handle_names(n_handles)
        # = ['龙头前', '第1节龙身', ..., '第221节龙身', '龙尾前', '龙尾后']
        # 长度一定是 n_handles，不会出现 223 vs 224 错配
    """
    if n_total < n_head + n_tail:
        raise ValueError(f"n_total={n_total} < n_head+n_tail={n_head+n_tail}")

    names = []

    # 头部
    if n_head == 1:
        names.append('龙头前')
    else:
        for i in range(n_head):
            names.append(f'头{i+1}')

    # 中间（"龙身"）
    n_middle = n_total - n_head - n_tail
    if n_middle > 0:
        if n_middle == 1:
            # 头 + 1 中间 + 尾：合并命名
            names.append('龙身')  # 单节
        else:
            for i in range(1, n_middle + 1):
                names.append(f'第{i}节龙身')

    # 尾部
    if n_tail == 1:
        names.append('龙尾后')
    else:
        for i in range(n_tail):
            names.append(f'尾{i+1}')

    return names


# ==================== 第一阶段：物理建模 ====================
print("=" * 60)
print("  第一阶段：物理建模（参数定义 + 几何/运动学函数）")
print("=" * 60)
print(f"  物理参数: {len(PHYSICAL_PARAMS)} 项已配置")
print(f"  视觉自检: {'已启用' if _HAS_VISUAL_QA else '不可用'}")
print(f"  数据目录: {FIG_DIR}")
print(f"  结果目录: {OUT_DIR}")


# ==================== 第二阶段：求解 ====================
print("\n" + "=" * 60)
print("  第二阶段：求解（按算法选型）")
print("=" * 60)

# TODO: 求解逻辑
# ...


# ==================== 第三阶段：输出 + 可视化 ====================
print("\n" + "=" * 60)
print("  第三阶段：输出 result + 可视化")
print("=" * 60)

# TODO: 画图示例
# fig, ax = plt.subplots(figsize=(10, 6))
# ax.plot(times, y_values, linewidth=2)
# ax.set_xlabel('时间 (s)')
# ax.set_ylabel('位置 (m)')
# ax.grid(True, alpha=0.3)
# save_fig_with_qa(fig, '问题X_时间序列.png')  # 增强版带 QA 自检

print("\n✅ 问题X求解完成！")
print(f"  提示: 修改 {os.path.basename(__file__)} 顶部物理参数和 §2 函数区即可")
