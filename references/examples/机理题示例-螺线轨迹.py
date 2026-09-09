# -*- coding: utf-8 -*-
"""
【示例】机理题最小可跑样例：等距螺线轨迹
═══════════════════════════════════════════════════════════════

来源：2024 国赛 A 题"板凳龙"问题 1 简化版
目的：展示机理题代码的标准结构
用法：直接 `py 机理题示例-螺线轨迹.py`，输出到当前目录的 `图片/` 和 `结果/`

[OK] 演示的工程实践：
- 物理参数集中定义（§1）
- 几何核心函数（§2）
- numpy 向量化（避免 O(N²) 循环）
- 时间步进 + 增量保存
- save_fig_with_qa 自动 QA
- 输出 result 模板（保持行列结构）
"""
import os, sys
import numpy as np
import pandas as pd
from scipy.integrate import quad

# ==================== § 1 物理参数 ====================
PITCH = 0.55       # 螺距 (m)
V_HEAD = 1.0       # 龙头速度 (m/s)
T_TOTAL = 10.0     # 总时长 (s) — 演示用 10s（实际题 300s）
DT = 1.0           # 采样间隔 (s)
N_HANDLES = 5      # 演示用 5 把手（实际题 224）

# ==================== § 2 几何核心函数 ====================

def r_of_theta(theta, p):
    """等距螺线 r = pθ / (2π)"""
    return p * theta / (2 * np.pi)


def xy_of_theta(theta, p):
    """(x, y) 坐标"""
    r = r_of_theta(theta, p)
    return r * np.cos(theta), r * np.sin(theta)


def arc_length(theta, p):
    """从 0 到 θ 的弧长 s(θ) = (p/(2π)) * ∫₀^θ √(t²+1) dt"""
    integrand = lambda t: np.sqrt(t * t + 1)
    result, _ = quad(integrand, 0, theta, limit=200)
    return (p / (2 * np.pi)) * result


# ==================== § 3 时间步进 ====================
S_HEAD_0 = arc_length(16 * 2 * np.pi, PITCH)  # 龙头在第 16 圈
print(f"龙头初始弧长: s = {S_HEAD_0:.4f} m")

times = np.arange(0, T_TOTAL + DT, DT)
# 5 把手，各滞后固定物理距离（演示用）
HANDLE_LAG = np.array([0.0, 0.5, 1.0, 1.5, 2.0])  # m

# 状态数组: (T, N_HANDLES, 2)
positions = np.zeros((len(times), N_HANDLES, 2))
speeds = np.zeros((len(times), N_HANDLES))

for ti, t in enumerate(times):
    s_head = S_HEAD_0 - V_HEAD * t  # 龙头沿弧长向内走
    for hi in range(N_HANDLES):
        s_h = s_head + HANDLE_LAG[hi]  # 后把手 s 更大
        if s_h < 0:
            positions[ti, hi] = np.nan
            continue
        # 数值反解 θ
        from scipy.optimize import brentq
        try:
            theta_h = brentq(lambda t_: arc_length(t_, PITCH) - s_h, 0, 200)
        except ValueError:
            positions[ti, hi] = np.nan
            continue
        positions[ti, hi] = xy_of_theta(theta_h, PITCH)
        speeds[ti, hi] = V_HEAD


# ==================== § 4 输出 result 模板 ====================
# 模板结构: 2N 行 (x, y) × (T+1) 列
OUT_DIR = os.path.join(os.path.dirname(__file__), '结果')
FIG_DIR = os.path.join(os.path.dirname(__file__), '图片')
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

handle_names = [f'把手{i+1}' for i in range(N_HANDLES)]
pos_rows = []
for hi, name in enumerate(handle_names):
    pos_rows.append((f'{name}x (m)', positions[:, hi, 0]))
    pos_rows.append((f'{name}y (m)', positions[:, hi, 1]))
vel_rows = [(name, speeds[:, hi]) for hi, name in enumerate(handle_names)]

time_labels = [f'{int(t)} s' for t in times]
pos_df = pd.DataFrame(
    {**{'把手': [r[0] for r in pos_rows]},
     **{tl: [r[1][i] for r in pos_rows] for i, tl in enumerate(time_labels)}}
)
vel_df = pd.DataFrame(
    {**{'把手': [r[0] for r in vel_rows]},
     **{tl: [r[1][i] for r in vel_rows] for i, tl in enumerate(time_labels)}}
)
# 6 位小数（数模国赛标准）
pos_df.iloc[:, 1:] = pos_df.iloc[:, 1:].round(6)
vel_df.iloc[:, 1:] = vel_df.iloc[:, 1:].round(6)

# 演示用：保存为 "示例_result.xlsx"（实际题用 "问题1_result1.xlsx"）
result_path = os.path.join(OUT_DIR, '示例_result.xlsx')
with pd.ExcelWriter(result_path, engine='openpyxl') as w:
    pos_df.to_excel(w, sheet_name='位置', index=False)
    vel_df.to_excel(w, sheet_name='速度', index=False)
print(f"[OK] {result_path} 已保存 ({os.path.getsize(result_path)/1024:.1f} KB)")


# ==================== § 5 画图 ====================
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({
    'font.sans-serif': ['SimHei', 'Microsoft YaHei', 'DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 14,
    'axes.labelsize': 16,
    'lines.linewidth': 2.0,
    'savefig.dpi': 200,
    'figure.constrained_layout.use': True,
})

# 图 1: 几个时刻的轨迹叠加
fig, ax = plt.subplots(figsize=(10, 8))
for ti, t in enumerate(times):
    xs = positions[ti, :, 0]
    ys = positions[ti, :, 1]
    ax.plot(xs, ys, '-o', markersize=6, linewidth=1.5, alpha=0.7, label=f't={int(t)}s')
ax.set_xlabel('x (m)')
ax.set_ylabel('y (m)')
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
ax.legend()
ax.set_title('机理题示例: 螺线轨迹（不同时刻叠加）')
fig_path = os.path.join(FIG_DIR, '示例_轨迹演化.png')
fig.savefig(fig_path, dpi=200, bbox_inches='tight')
plt.close(fig)
print(f"[OK] {fig_path} 已保存")

# 图 2: 速度验证（应全部 = 1 m/s）
fig, ax = plt.subplots(figsize=(10, 5))
for hi in range(N_HANDLES):
    ax.plot(times, speeds[:, hi], '-o', label=handle_names[hi], linewidth=2)
ax.set_xlabel('时间 (s)')
ax.set_ylabel('速度 (m/s)')
ax.grid(True, alpha=0.3)
ax.legend()
ax.set_title(f'机理题示例: 各把手速度（应均 = {V_HEAD} m/s）')
fig_path = os.path.join(FIG_DIR, '示例_速度验证.png')
fig.savefig(fig_path, dpi=200, bbox_inches='tight')
plt.close(fig)
print(f"[OK] {fig_path} 已保存")

print("\n[OK] 机理题示例运行完成！")
print(f"  结果: {OUT_DIR}")
print(f"  图片: {FIG_DIR}")
print(f"  提示: 修改 §1 物理参数 + §2 几何函数即可适配其他机理题")
