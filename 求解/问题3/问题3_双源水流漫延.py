# -*- coding: utf-8 -*-
"""问题 3: 双突水点水流漫延 (附件 1 + 附件 2)

按 user 决策: 两源独立 Dijkstra 取 min
- 端点 t_arr = min(t_arr_A, t_arr_B + t_b_delay)
- 巷道 t_full: 先到者定
- 输出: result3-1.xlsx, result3-2.xlsx
"""
import os
import sys
import time

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
os.chdir(_HERE)
sys.path.insert(0, _PARENT)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

from graph import load_attach, build_graph
from flow import run_dual_source
from constants import (
    SOURCE_A1, SOURCE_B1, T_B_DELAY_1,
    SOURCE_A2, SOURCE_B2, T_B_DELAY_2,
)
from result_writer import write_flow_result

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def draw_dual_source_3d(G, t_arr, snap_a, snap_b, out_path, title):
    """3D 网络 + 双源水流 + 2 突水点"""
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    xs, ys, zs, ts = [], [], [], []
    for n, d in G.nodes(data=True):
        x, y, z = d['xyz']
        xs.append(x)
        ys.append(y)
        zs.append(z)
        ts.append(t_arr.get(n, 0))
    sc = ax.scatter(xs, ys, zs, c=ts, cmap='viridis_r', s=8, alpha=0.7)
    plt.colorbar(sc, ax=ax, label='Earliest water arrival time (min)')

    for u, v, d in G.edges(data=True):
        a = G.nodes[u]['xyz']
        b = G.nodes[v]['xyz']
        ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]],
                color='gray', linewidth=0.3, alpha=0.4)

    # 源点 A (红星)
    sx, sy, sz = snap_a[2]
    ax.scatter([sx], [sy], [sz], c='red', s=300, marker='*',
               label=f'Source A (snap to {snap_a[0]})', edgecolors='black', linewidth=1.5)
    # 源点 B (蓝星)
    sx, sy, sz = snap_b[2]
    ax.scatter([sx], [sy], [sz], c='blue', s=300, marker='*',
               label=f'Source B (snap to {snap_b[0]})', edgecolors='black', linewidth=1.5)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.legend(loc='upper right', fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  -> {out_path}')


def draw_dual_vs_single_compare(t_arr_single, t_arr_dual, out_path, title):
    """对比 单源 vs 双源 水流到达时刻"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    s_vals = [t_arr_single.get(n, 0) for n in t_arr_single]
    d_vals = [t_arr_dual.get(n, 0) for n in t_arr_dual]

    axes[0].hist(s_vals, bins=50, color='steelblue', edgecolor='black', alpha=0.7, label='Single')
    axes[0].hist(d_vals, bins=50, color='orange', edgecolor='black', alpha=0.5, label='Dual')
    axes[0].set_xlabel('Water arrival time (min)')
    axes[0].set_ylabel('Node count')
    axes[0].set_title('Distribution: single vs dual source')
    axes[0].legend()

    # 散点: x = single, y = dual
    n_common = [n for n in t_arr_single if n in t_arr_dual]
    s_list = [t_arr_single[n] for n in n_common]
    d_list = [t_arr_dual[n] for n in n_common]
    axes[1].scatter(s_list, d_list, alpha=0.4, s=8, color='darkgreen')
    mn = min(min(s_list), min(d_list))
    mx = max(max(s_list), max(d_list))
    axes[1].plot([mn, mx], [mn, mx], 'r--', alpha=0.6, label='y=x')
    axes[1].set_xlabel('Single source t_arr (min)')
    axes[1].set_ylabel('Dual source t_arr (min)')
    axes[1].set_title('Per-node: dual is earlier or same?')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=14)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  -> {out_path}')


def main():
    t_total = time.time()
    for attach_n, src_a, src_b, t_delay, suffix in [
        (1, SOURCE_A1, SOURCE_B1, T_B_DELAY_1, '3-1'),
        (2, SOURCE_A2, SOURCE_B2, T_B_DELAY_2, '3-2'),
    ]:
        print(f'\n=== Q3 附件 {attach_n} ===')
        t0 = time.time()
        attach_path = os.path.join('..', '..', '数据', '附件', f'附件{attach_n}.xlsx')
        points, segments = load_attach(attach_path)
        G = build_graph(points, segments)
        print(f'  网络: {len(points)} 端点, {len(segments)} 巷道')

        # Q1 单源（用于对比）
        from flow import run_single_source
        res_single = run_single_source(G, points, segments, src_a, 'A')

        # Q3 双源
        res = run_dual_source(G, points, segments, src_a, src_b, t_delay)
        print(f'  Snap A: 巷道 {res["snap_a"][0]}, B: 巷道 {res["snap_b"][0]}')
        print(f'  双源延迟: B 在 A 之后 {t_delay} min 开始')

        t_arr_vals = list(res['t_arr'].values())
        t_full_vals = [t for t in res['t_full'].values() if t is not None]
        print(f'  t_arr 范围: {min(t_arr_vals):.2f} ~ {max(t_arr_vals):.2f} min')
        print(f'  t_full 范围: {min(t_full_vals):.2f} ~ {max(t_full_vals):.2f} min')

        # 写 result
        out_path = os.path.join('结果', f'result{suffix}.xlsx')
        tpl_path = os.path.join('..', '..', '数据', '附件', '附件3', f'result{suffix}.xlsx')
        write_flow_result(tpl_path, out_path, res['t_arr'], res['t_full'],
                          points, segments)
        print(f'  -> {out_path}')

        # 图 1: 3D 双源
        draw_dual_source_3d(G, res['t_arr'], res['snap_a'], res['snap_b'],
                            os.path.join('图片', f'问题3_附件{attach_n}_3D双源水流.png'),
                            f'Q3 附件{attach_n}: 3D 双源水流漫延 (A{t_delay}min后B)')

        # 图 2: 单源 vs 双源对比
        draw_dual_vs_single_compare(res_single['t_arr'], res['t_arr'],
                                    os.path.join('图片', f'问题3_附件{attach_n}_单双源对比.png'),
                                    f'Q3 附件{attach_n}: 单源 vs 双源水流到达时刻对比')

        print(f'  附件{attach_n} 耗时: {time.time() - t0:.2f}s')

    print(f'\n总耗时: {time.time() - t_total:.2f}s')


if __name__ == '__main__':
    main()
