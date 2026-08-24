"""Snap 一个 3D 点到最近的巷道中点 (snap-proj 策略)

按用户选择: 点 P 找最近巷道 H_k (点到线段距离), 把 P 当 H_k 上的虚拟源.
返回 (巷道编号, P 在该巷道上的参数 t in [0,1], snap 后的 3D 坐标)
"""
# -*- coding: utf-8 -*-
import numpy as np


def point_to_segment_distance(p, a, b):
    """3D 点 P 到线段 AB 的最短距离 + 参数 t (0..1, 在 AB 上的投影位置)"""
    p = np.asarray(p, dtype=float)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ab = b - a
    L2 = float(np.dot(ab, ab))
    if L2 < 1e-12:
        return float(np.linalg.norm(p - a)), 0.0
    ap = p - a
    t = float(np.dot(ap, ab) / L2)
    t = max(0.0, min(1.0, t))
    closest = a + t * ab
    return float(np.linalg.norm(p - closest)), t


def snap_to_network(point, points_dict, segments_dict, k=1):
    """Snap point 到最近 (k 条) 巷道

    Args:
        point: 3D 点 (x, y, z)
        points_dict: {端点编号: (x, y, z)}
        segments_dict: {巷道编号: (端点A, 端点B)}
        k: 返回 k 个候选 (默认 1)

    Returns:
        list of (segment_id, t, snap_xyz, dist) 按距离升序
    """
    candidates = []
    for seg_id, (pa_id, pb_id) in segments_dict.items():
        d, t = point_to_segment_distance(point, points_dict[pa_id], points_dict[pb_id])
        a = np.asarray(points_dict[pa_id], dtype=float)
        b = np.asarray(points_dict[pb_id], dtype=float)
        snap_xyz = tuple(a + t * (b - a))
        candidates.append((seg_id, t, snap_xyz, d))
    candidates.sort(key=lambda x: x[3])
    return candidates[:k]


def split_path_by_t(seg_id, t, points_dict, segments_dict):
    """把巷道 H_k 按 snap 参数 t 分成两段, 返回两段的新巷道编号

    因为我们的图是基于 networkx 的简单图, snap 后想"插入虚拟节点"需要:
    方案 A: 暂时用 snap 点当作一个端点 (实际计算时不修改原图, 只在 Dijkstra
            时临时改边权)
    方案 B: 在图上插入虚拟节点, 改拓扑

    这里采用方案 A 的轻量版: 返回 (H_k, t, 端点A, 端点B) 元数据, 求解时按 t 切分.
    """
    pa_id, pb_id = segments_dict[seg_id]
    pa = points_dict[pa_id]
    pb = points_dict[pb_id]
    return seg_id, t, pa_id, pb_id
