# -*- coding: utf-8 -*-
"""问题 4: 双源逃生 (附件 1 + 附件 2)

第二突水点突水 1min 后, 调整逃生方案.
输入: Q3 的水流到达/充满时刻
输出: 3 工人调整后最佳逃生路径 → result4-1.xlsx, result4-2.xlsx
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
from escape import time_varying_dijkstra
from constants import (
    SOURCE_A1, SOURCE_B1, T_B_DELAY_1,
    SOURCE_A2, SOURCE_B2, T_B_DELAY_2,
    EXIT_1_1, EXIT_1_2, WORKER_1_1, WORKER_1_2, WORKER_1_3,
    EXIT_2_1, EXIT_2_2, WORKER_2_1, WORKER_2_2, WORKER_2_3,
    T_ALARM,
)
from result_writer import write_escape_result

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def draw_q4_3d(G, worker_paths, out_path, title):
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    xs, ys, zs = [], [], []
    for n, d in G.nodes(data=True):
        x, y, z = d['xyz']
        xs.append(x); ys.append(y); zs.append(z)
    ax.scatter(xs, ys, zs, c='lightgray', s=4, alpha=0.5)
    for u, v, d in G.edges(data=True):
        a = G.nodes[u]['xyz']; b = G.nodes[v]['xyz']
        ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]],
                color='gray', linewidth=0.3, alpha=0.3)

    colors = ['red', 'blue', 'green']
    for i, (worker_xyz, path) in enumerate(worker_paths):
        if not path:
            continue
        ax.scatter([worker_xyz[0]], [worker_xyz[1]], [worker_xyz[2]],
                   c=colors[i], s=120, marker='o', label=f'Worker {i+1} start',
                   edgecolors='black', linewidth=1.5)
        px = [worker_xyz[0]] + [p[0] for p in path]
        py = [worker_xyz[1]] + [p[1] for p in path]
        pz = [worker_xyz[2]] + [p[2] for p in path]
        ax.plot(px, py, pz, color=colors[i], linewidth=2.0, marker='.', markersize=6, alpha=0.85)
        last = path[-1]
        ax.scatter([last[0]], [last[1]], [last[2]],
                   c=colors[i], s=150, marker='*', edgecolors='black', linewidth=1.5,
                   label=f'Worker {i+1} end')

    for ex_xyz in [EXIT_1_1, EXIT_1_2, EXIT_2_1, EXIT_2_2]:
        ax.scatter([ex_xyz[0]], [ex_xyz[1]], [ex_xyz[2]],
                   c='yellow', s=200, marker='X', edgecolors='black', linewidth=2.0)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    ax.legend(loc='upper right', fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  -> {out_path}')


def draw_q4_time(worker_results, out_path, title):
    fig, ax = plt.subplots(figsize=(10, 6))
    workers = ['Worker 1', 'Worker 2', 'Worker 3']
    exits = ['Exit 1', 'Exit 2']
    width = 0.35
    x = np.arange(len(workers))
    for i, exit_label in enumerate(exits):
        times = []
        for w in worker_results:
            t = w.get(f'arrive_exit_{i+1}', None)
            times.append(t if t is not None else 0)
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, times, width, label=exit_label, alpha=0.8)
        for bar, t in zip(bars, times):
            if t > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                        f'{t:.2f}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(workers)
    ax.set_ylabel('Arrival time (min from t=0)')
    ax.set_title(title)
    ax.legend(); ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'  -> {out_path}')


def main():
    t_total = time.time()
    for attach_n, src_a, src_b, t_delay, exits, workers, suffix in [
        (1, SOURCE_A1, SOURCE_B1, T_B_DELAY_1,
         [EXIT_1_1, EXIT_1_2],
         [WORKER_1_1, WORKER_1_2, WORKER_1_3],
         '4-1'),
        (2, SOURCE_A2, SOURCE_B2, T_B_DELAY_2,
         [EXIT_2_1, EXIT_2_2],
         [WORKER_2_1, WORKER_2_2, WORKER_2_3],
         '4-2'),
    ]:
        print(f'\n=== Q4 附件 {attach_n} ===')
        t0 = time.time()
        attach_path = os.path.join('..', '..', '数据', '附件', f'附件{attach_n}.xlsx')
        points, segments = load_attach(attach_path)
        G = build_graph(points, segments)
        print(f'  网络: {len(points)} 端点, {len(segments)} 巷道')

        # Q3 双源
        flow = run_dual_source(G, points, segments, src_a, src_b, t_delay)
        t_arr = flow['t_arr']
        t_full = flow['t_full']

        # 工人起跑时刻: 第二突水点 + 1min 报警
        # Q4 题面: "在第二突水点突水 1 分钟后, 安全生产部门发布调整后的逃生方案"
        # 第二突水点在 A 后 t_delay min 突水, 1min 后发布
        t_start = t_delay + 1.0
        print(f'  工人起跑时刻: t = {t_start} min (Q3 第二源后 1 min)')

        worker_results = []
        worker_paths = []
        for w_idx, worker_xyz in enumerate(workers):
            print(f'  Worker {w_idx+1} 起点: {worker_xyz}')
            res = time_varying_dijkstra(G, points, segments, t_arr, t_full,
                                         worker_xyz, exits, t_start=t_start)
            best_exit = None; best_time = None; best_path = []
            for exit_xyz, r in res.items():
                if r['arrive_time'] is not None and (best_time is None or r['arrive_time'] < best_time):
                    best_time = r['arrive_time']
                    best_exit = exit_xyz
                    best_path = r['path']
            print(f'    最佳出口: {best_exit}, 到达时刻: {best_time} min')
            if best_path:
                print(f'    路径 {len(best_path)} 步')
            success = best_time is not None
            worker_results.append({
                'worker_xyz': worker_xyz,
                'start_time': t_start,
                'path': best_path,
                'success': success,
                'arrive_time': best_time,
                'best_exit': best_exit,
                'arrive_exit_1': res.get(exits[0], {}).get('arrive_time'),
                'arrive_exit_2': res.get(exits[1], {}).get('arrive_time'),
            })
            worker_paths.append((worker_xyz, best_path))

        out_path = os.path.join('结果', f'result{suffix}.xlsx')
        tpl_path = os.path.join('..', '..', '数据', '附件', '附件3', f'result{suffix}.xlsx')
        write_escape_result(tpl_path, out_path, worker_results, points)
        print(f'  -> {out_path}')

        draw_q4_3d(G, worker_paths,
                   os.path.join('图片', f'问题4_附件{attach_n}_3D逃生.png'),
                   f'Q4 附件{attach_n}: 双源后 3 工人调整逃生路径')
        draw_q4_time(worker_results,
                     os.path.join('图片', f'问题4_附件{attach_n}_时间对比.png'),
                     f'Q4 附件{attach_n}: 双源后 3 工人到达 2 出口时间对比')

        print(f'  附件{attach_n} 耗时: {time.time() - t0:.2f}s')

    print(f'\n总耗时: {time.time() - t_total:.2f}s')


if __name__ == '__main__':
    main()
