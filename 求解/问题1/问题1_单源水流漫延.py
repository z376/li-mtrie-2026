# -*- coding: utf-8 -*-
"""问题 1: 单源水流漫延 (附件 1 + 附件 2)

按 user 决策:
- snap: 点到最近巷道中点
- 分流: 1/K 均分
- 输出: result1-1.xlsx, result1-2.xlsx
- 4-6 张图
"""
import os
import sys
import time

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)  # 求解/
os.chdir(_HERE)
sys.path.insert(0, _PARENT)  # 共享模块在父目录

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

from graph import load_attach, build_graph
from flow import run_single_source
from constants import SOURCE_A1, SOURCE_A2
from result_writer import write_flow_result

# 设置中文
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def draw_3d_network(G, t_arr, source_xyz, snap, out_path, title):
    """画 3D 网络 + 水流到达时刻热力图"""
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    # 节点
    xs, ys, zs, ts = [], [], [], []
    for n, d in G.nodes(data=True):
        x, y, z = d['xyz']
        xs.append(x)
        ys.append(y)
        zs.append(z)
        ts.append(t_arr.get(n, 0))
    sc = ax.scatter(xs, ys, zs, c=ts, cmap='viridis_r', s=8, alpha=0.7)
    plt.colorbar(sc, ax=ax, label='Water arrival time (min)')

    # 边
    for u, v, d in G.edges(data=True):
        a = G.nodes[u]['xyz']
        b = G.nodes[v]['xyz']
        ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]],
                color='gray', linewidth=0.3, alpha=0.4)

    # 突水点 (snap 后)
    sx, sy, sz = snap[2]
    ax.scatter([sx], [sy], [sz], c='red', s=200, marker='*',
               label=f'Source A (snap to {snap[0]})', edgecolors='black', linewidth=1.5)
    ax.legend(loc='upper right', fontsize=10)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')

    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  -> {out_path}')


def draw_arrival_histogram(t_arr, t_full, out_path, title):
    """画水流到达时刻 + 巷道充满时刻直方图"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    t_arr_vals = list(t_arr.values())
    axes[0].hist(t_arr_vals, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    axes[0].set_xlabel('Node water arrival time (min)')
    axes[0].set_ylabel('Node count')
    axes[0].set_title('Distribution of water arrival time at nodes')
    axes[0].axvline(np.mean(t_arr_vals), color='red', linestyle='--', label=f'mean={np.mean(t_arr_vals):.1f}')
    axes[0].legend()

    t_full_vals = [t for t in t_full.values() if t is not None]
    axes[1].hist(t_full_vals, bins=50, color='darkorange', edgecolor='black', alpha=0.7)
    axes[1].set_xlabel('Tunnel water-full time (min)')
    axes[1].set_ylabel('Tunnel count')
    axes[1].set_title('Distribution of tunnel full-water time')
    axes[1].axvline(np.mean(t_full_vals), color='red', linestyle='--', label=f'mean={np.mean(t_full_vals):.1f}')
    axes[1].legend()

    fig.suptitle(title, fontsize=14)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  -> {out_path}')


def main():
    t_total = time.time()
    for attach_n, source_xyz, suffix in [
        (1, SOURCE_A1, '1-1'),
        (2, SOURCE_A2, '1-2'),
    ]:
        print(f'\n=== Q1 附件 {attach_n}: 突水点 {source_xyz} ===')
        t0 = time.time()
        attach_path = os.path.join('..', '..', '数据', '附件', f'附件{attach_n}.xlsx')
        points, segments = load_attach(attach_path)
        G = build_graph(points, segments)
        print(f'  网络: {len(points)} 端点, {len(segments)} 巷道')

        res = run_single_source(G, points, segments, source_xyz, source_label=f'A{attach_n}')
        snap = res['snap']
        print(f'  Snap: 巷道 {snap[0]} t={snap[1]:.3f} 距离 {snap[3]:.2f}m')

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

        # 画图 1: 3D 网络
        draw_3d_network(G, res['t_arr'], source_xyz, snap,
                        os.path.join('图片', f'问题1_附件{attach_n}_3D网络水流.png'),
                        f'Q1 附件{attach_n}: 3D 网络水流漫延时序 (A{attach_n} 突水)')

        # 画图 2: 到达时刻直方图
        draw_arrival_histogram(res['t_arr'], res['t_full'],
                               os.path.join('图片', f'问题1_附件{attach_n}_时刻分布.png'),
                               f'Q1 附件{attach_n}: 水流到达 + 巷道充满时刻分布')

        print(f'  附件{attach_n} 耗时: {time.time() - t0:.2f}s')

    print(f'\n总耗时: {time.time() - t_total:.2f}s')


if __name__ == '__main__':
    main()
