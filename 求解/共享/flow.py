"""水流漫延: 单源 / 双源 Dijkstra

按用户选择 (1/K 均分, 双源独立取 min).
"""
# -*- coding: utf-8 -*-
import heapq
import math
import numpy as np
from collections import defaultdict

from 共享.geometry import snap_to_network
from 共享.constants import (
    B, H_MAX, H_0, Q_IN, U_FLOW, WADE_LIMIT,
    T_ALARM, T_B_DELAY_1, T_B_DELAY_2,
    RESULT_TPL,
)


def dijkstra_single_source(G, source_node, source_t=0.0):
    """单源 Dijkstra: 边权 = L / U_FLOW (min)

    Args:
        G: networkx Graph (含 length 属性)
        source_node: 源端点 (必须在 G.nodes 里)
        source_t: 源在 t=0 已有水 (默认 0)

    Returns:
        t_arr: dict {端点: 到达时刻 (min)}
    """
    t_arr = {source_node: source_t}
    pq = [(source_t, source_node)]
    while pq:
        t, u = heapq.heappop(pq)
        if t > t_arr.get(u, math.inf):
            continue
        for v in G.neighbors(u):
            L = G[u][v]['length']
            w = L / U_FLOW
            nt = t + w
            if nt < t_arr.get(v, math.inf):
                t_arr[v] = nt
                heapq.heappush(pq, (nt, v))
    return t_arr


def split_factor(G, pa, pb, source_node, source_t_arr, depth=0, memo=None):
    """估算巷道 (pa, pb) 上的"分摊系数" K_path

    简化方案 (按"分摊 + 几何平均"):
    端点 i 处分摊系数 d[i] = max(1, G.degree(i) - 1)
    巷道 k = (pa, pb) 的分摊系数 = 端点 pa 的 d 和 pb 的 d 的几何平均 (向上取整)
    K_path[k] = max(1, round(sqrt(d[pa] * d[pb])))
    """
    if memo is None:
        memo = {}
    if pa in memo and pb in memo[pa]:
        return memo[pa][pb]
    if pb in memo and pa in memo[pb]:
        return memo[pb][pa]
    d_pa = max(1, G.degree(pa) - 1)
    d_pb = max(1, G.degree(pb) - 1)
    K = max(1, int(round(math.sqrt(d_pa * d_pb))))
    memo.setdefault(pa, {})[pb] = K
    memo.setdefault(pb, {})[pa] = K
    return K


def compute_t_full(G, t_arr, points, segments):
    """计算每条巷道的"充满时刻" t_full

    简化方案: t_full[k] = max(t_arr[pa], t_arr[pb]) + 0.4 * K_path * L
    其中 K_path 是分摊系数, 充满时间跟单巷道流量成反比.
    """
    t_full = {}
    for sid, (pa, pb) in segments.items():
        if pa not in t_arr or pb not in t_arr:
            t_full[sid] = None
            continue
        L = G[pa][pb]['length']
        K = split_factor(G, pa, pb, None, t_arr)
        # 单巷道流量 = Q_IN / K, 充满时间 = 12*L / (Q_IN/K) = 0.4*K*L
        fill_time = 0.4 * K * L
        # 水到达两端点后才开始算充满 (用 max)
        t_start = max(t_arr[pa], t_arr[pb])
        t_full[sid] = t_start + fill_time
    return t_full


def run_single_source(G, points, segments, source_xyz, source_label="A"):
    """从非端点 source_xyz 跑单源水流漫延

    Returns:
        result dict: {
            't_arr': {端点: min},
            't_full': {巷道: min or None},
            'snap': (seg_id, t, snap_xyz, dist),
        }
    """
    snap = snap_to_network(source_xyz, points, segments, k=1)[0]
    seg_id, t_snap, snap_xyz, dist = snap
    pa, pb = segments[seg_id]
    L_full = G[pa][pb]['length']
    L_a = t_snap * L_full
    L_b = (1 - t_snap) * L_full

    # 虚拟源点
    VIRT = '__SRC__'
    G2 = G.copy()
    G2.add_node(VIRT, xyz=snap_xyz)
    G2.add_edge(VIRT, pa, length=L_a, seg_id=f'{seg_id}*a')
    G2.add_edge(VIRT, pb, length=L_b, seg_id=f'{seg_id}*b')

    t_arr = dijkstra_single_source(G2, VIRT, source_t=0.0)
    # 去掉虚拟节点
    t_arr.pop(VIRT, None)
    t_full = compute_t_full(G, t_arr, points, segments)
    return {'t_arr': t_arr, 't_full': t_full, 'snap': snap}


def run_dual_source(G, points, segments, source_a_xyz, source_b_xyz, t_b_delay):
    """双源: 独立 Dijkstra 后 t_arr / t_full 各取 min

    Returns:
        result dict: {
            't_arr': {端点: min},  # t_arr = min(t_arr_A, t_arr_B + t_b_delay)
            't_full': {巷道: min},
            'snap_a': ..., 'snap_b': ...,
        }
    """
    r_a = run_single_source(G, points, segments, source_a_xyz, 'A')
    r_b = run_single_source(G, points, segments, source_b_xyz, 'B')

    t_arr = {}
    for n in G.nodes():
        ta = r_a['t_arr'].get(n, math.inf)
        tb = r_b['t_arr'].get(n, math.inf) + t_b_delay
        t_arr[n] = min(ta, tb)

    t_full = {}
    for sid in segments:
        tfa = r_a['t_full'].get(sid)
        tfb = r_b['t_full'].get(sid)
        if tfa is None and tfb is None:
            t_full[sid] = None
        elif tfa is None:
            t_full[sid] = tfb + t_b_delay
        elif tfb is None:
            t_full[sid] = tfa
        else:
            t_full[sid] = min(tfa, tfb + t_b_delay)

    return {
        't_arr': t_arr,
        't_full': t_full,
        'snap_a': r_a['snap'],
        'snap_b': r_b['snap'],
    }
