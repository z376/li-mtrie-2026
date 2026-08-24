"""时变 Dijkstra 逃生

输入: 工人起点, 出口列表, t_arr[], t_full[]
输出: 每个出口的"最早到达时刻" + 路径

边权 = 工人在巷道 k 通过时间, 跟水深时变耦合.
- 水深 <= 0.3m: 可走, 顺水 2 m/s, 逆水 1 m/s, 无水 4 m/s
- 水深 > 0.3m: 不可走 (权 = inf)
- 路径长度 <= 7 步 (result 模板限制)
"""
# -*- coding: utf-8 -*-
import heapq
import math
from collections import defaultdict

from geometry import snap_to_network
from constants import (
    V_DRY, V_UP, V_DOWN, V_DRY_MIN, V_UP_MIN, V_DOWN_MIN,
    WADE_LIMIT, T_ALARM, H_0, H_MAX,
)


def water_depth_at(t, t_arr_down, t_full):
    """工人在 t 时刻到达巷道下游端点, 计算该时刻的水深

    Args:
        t: 工人到达下游端的时刻 (min)
        t_arr_down: 水流到达下游端的时刻 (min)
        t_full: 巷道充满时刻 (min)

    Returns:
        depth (m) 0..H_MAX; 若 t >= t_full 返回 H_MAX (满)
    """
    if t < t_arr_down:
        return 0.0  # 水还没到, 无水
    if t >= t_full:
        return H_MAX  # 满
    # 线性上升 0.1m → 3m
    frac = (t - t_arr_down) / max(t_full - t_arr_down, 1e-9)
    return H_0 + frac * (H_MAX - H_0)


def is_downstream(worker_from, worker_to, t_arr):
    """判定工人方向是否跟水流方向一致 (顺水/逆水)

    水从 t_arr 小的一端流向 t_arr 大的一端.
    - 工人从 t_arr 小端 → t_arr 大端 = 顺水 (V=2)
    - 工人从 t_arr 大端 → t_arr 小端 = 逆水 (V=1)
    - 任意端 t_arr 缺失: 视为无水 (V=4)
    """
    ta = t_arr.get(worker_from, None)
    tb = t_arr.get(worker_to, None)
    if ta is None or tb is None:
        return 'dry'
    if tb < ta:
        return 'down'  # 工人从 t_arr 大→小? 不对, 顺水是 t_arr 小→大
    if tb > ta:
        return 'down'  # 工人从 t_arr 小(a) 走到大(b) = 顺水
    return 'dry'


def traverse_time(L, depth, direction):
    """通过时间 (min): L / V
    L: 巷道长 m
    depth: 水深 m
    direction: 'down'/'up'/'dry'
    """
    if depth > WADE_LIMIT:
        return math.inf
    if direction == 'dry' or depth < 1e-6:
        V = V_DRY_MIN
    elif direction == 'down':
        V = V_DOWN_MIN
    else:  # 'up'
        V = V_UP_MIN
    return L / V


def time_varying_dijkstra(G, points, segments, t_arr, t_full,
                          worker_xyz, exits_xyz, t_start=T_ALARM,
                          max_steps=50):
    """时变 Dijkstra: 工人从 worker_xyz 出发, 找每个 exit 的最短到达时间 + 路径

    Args:
        G: 图
        points, segments: 端点/巷道 dict
        t_arr, t_full: 水流到达/充满时刻
        worker_xyz: 工人起点 3D
        exits_xyz: 出口 3D 列表
        t_start: 报警时刻 (默认 T_ALARM=1 min)
        max_steps: 路径最大步数 (默认 7 步)

    Returns:
        dict {exit_xyz: {'arrive_time': float, 'path': [(xyz, t, seg_id), ...]}}
        path 是从工人起点开始, 每到一个端点记录 (坐标, 到达时刻, 进入该端点走的巷道)
    """
    # Snap 工人到最近巷道
    snap_w = snap_to_network(worker_xyz, points, segments, k=1)[0]
    seg_id_w, t_snap_w, snap_xyz_w, dist_w = snap_w
    pa_w, pb_w = segments[seg_id_w]
    L_full = G[pa_w][pb_w]['length']
    L_a = t_snap_w * L_full
    L_b = (1 - t_snap_w) * L_full

    # 构造虚拟工人起点 + 虚拟出口
    G2 = G.copy()
    VIRT_W = '__WORKER__'
    G2.add_node(VIRT_W, xyz=snap_xyz_w)
    G2.add_edge(VIRT_W, pa_w, length=L_a)
    G2.add_edge(VIRT_W, pb_w, length=L_b)

    virt_exits = []
    for k, exit_xyz in enumerate(exits_xyz):
        snap_e = snap_to_network(exit_xyz, points, segments, k=1)[0]
        seg_id_e, t_snap_e, snap_xyz_e, _ = snap_e
        pa_e, pb_e = segments[seg_id_e]
        L_full_e = G[pa_e][pb_e]['length']
        L_a_e = t_snap_e * L_full_e
        L_b_e = (1 - t_snap_e) * L_full_e
        V = f'__EXIT_{k}__'
        G2.add_node(V, xyz=snap_xyz_e)
        G2.add_edge(V, pa_e, length=L_a_e)
        G2.add_edge(V, pb_e, length=L_b_e)
        virt_exits.append((V, exit_xyz, snap_xyz_e))

    INF = math.inf
    dist = {VIRT_W: t_start}
    prev = {}  # (node, t) -> (prev_node, prev_t, via_seg_id)
    step_count = {VIRT_W: 0}
    pq = [(t_start, 0, VIRT_W)]

    while pq:
        t_now, steps_now, u = heapq.heappop(pq)
        if t_now > dist.get(u, INF):
            continue
        for v in G2.neighbors(u):
            seg_data = G2[u][v]
            L = seg_data['length']
            if u == VIRT_W:
                depth = 0.0
                direction = 'dry'
            elif v in [ve[0] for ve in virt_exits]:
                depth = 0.0
                direction = 'dry'
            else:
                ta = t_arr.get(u)
                tb = t_arr.get(v)
                if ta is None or tb is None:
                    depth = 0.0
                    direction = 'dry'
                else:
                    if ta < tb:
                        direction = 'down'
                    elif ta > tb:
                        direction = 'up'
                    else:
                        direction = 'dry'
                    sid = seg_data.get('seg_id', None)
                    if sid is None:
                        t_full_k = INF
                    else:
                        t_full_k = t_full.get(sid, INF) or INF
                    t_enter = t_now
                    t_exit = t_now + L / V_DRY_MIN
                    t_mid = (t_enter + t_exit) / 2
                    depth = water_depth_at(t_mid, tb, t_full_k)

            tt = traverse_time(L, depth, direction)
            if math.isinf(tt):
                continue
            nt = t_now + tt
            ns = steps_now + 1
            if ns > max_steps:
                continue
            if nt < dist.get(v, INF):
                dist[v] = nt
                step_count[v] = ns
                prev[(v, nt)] = (u, t_now, seg_data.get('seg_id', None))
                heapq.heappush(pq, (nt, ns, v))

    # 重建路径
    results = {}
    for V, exit_xyz, snap_xyz_e in virt_exits:
        if V not in dist:
            results[exit_xyz] = {'arrive_time': None, 'path': []}
            continue
        # 逆推
        path_nodes = []  # [(node, t)]
        cur_n, cur_t = V, dist[V]
        while cur_n != VIRT_W:
            path_nodes.append((cur_n, cur_t))
            p = prev.get((cur_n, cur_t))
            if p is None:
                break
            cur_n, cur_t, _ = p
        path_nodes.append((VIRT_W, t_start))
        path_nodes.reverse()

        # 转成 (xyz, 到达时刻, 走的巷道) 格式
        # 第 0 个是 VIRT_W (snap 起点), 后续是真实端点
        # 路径上每个端点: 走的巷道 = 上一段 (u, v) 的 seg_id
        path_out = []
        for i in range(1, len(path_nodes)):
            prev_n, prev_t = path_nodes[i - 1]
            cur_n, cur_t = path_nodes[i]
            seg_id_used = G2[prev_n][cur_n].get('seg_id', None)
            # 坐标
            if cur_n == VIRT_W or cur_n.startswith('__EXIT_'):
                xyz = G2.nodes[cur_n].get('xyz', (0, 0, 0))
            else:
                xyz = G2.nodes[cur_n].get('xyz', (0, 0, 0))
            path_out.append((xyz[0], xyz[1], xyz[2], cur_t, seg_id_used))

        # 起点 (工人位置 + t=t_start) 作为第 0 行
        # path_out[i] 表示"第 i 步到达的端点" + "走过的巷道"
        results[exit_xyz] = {
            'arrive_time': dist[V],
            'path': path_out,
        }
    return results
