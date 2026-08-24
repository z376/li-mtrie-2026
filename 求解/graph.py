"""图构建: 读 xlsx → (端点 dict, 巷道 dict, networkx 图)

按导入规范: 显式列全函数.
"""
# -*- coding: utf-8 -*-
import pandas as pd
import os
import networkx as nx
import numpy as np

# 用 Unicode escape 避免 sys.path GBK 问题
SHEET_NODE = '\u7aef\u70b9'   # 端点
SHEET_SEG = '\u5df7\u9053'     # 巷道


def load_attach(attach_path):
    """读 附件1.xlsx / 附件2.xlsx

    Returns:
        points: dict {端点编号: (x, y, z)}
        segments: dict {巷道编号: (端点A编号, 端点B编号)}
    """
    df_p = pd.read_excel(attach_path, sheet_name=SHEET_NODE, header=1)
    df_s = pd.read_excel(attach_path, sheet_name=SHEET_SEG, header=0)
    # 端点列: 端点编号 / x(m) / y(m) / z(m)
    points = {}
    for _, row in df_p.iterrows():
        pid = str(row.iloc[0]).strip()
        if not pid or pid == 'nan':
            continue
        try:
            x, y, z = float(row.iloc[1]), float(row.iloc[2]), float(row.iloc[3])
        except (TypeError, ValueError):
            continue
        points[pid] = (x, y, z)
    # 巷道列: 巷道编号 / 巷道端点1 / 巷道端点2
    segments = {}
    for _, row in df_s.iterrows():
        sid = str(row.iloc[0]).strip()
        if not sid or sid == 'nan':
            continue
        pa = str(row.iloc[1]).strip()
        pb = str(row.iloc[2]).strip()
        if pa and pb and pa != 'nan' and pb != 'nan':
            segments[sid] = (pa, pb)
    return points, segments


def build_graph(points, segments):
    """构建 networkx Graph (无向), 边权 = 3D 长度 (m)"""
    G = nx.Graph()
    for pid, (x, y, z) in points.items():
        G.add_node(pid, xyz=(x, y, z))
    for sid, (pa, pb) in segments.items():
        a = np.array(points[pa], dtype=float)
        b = np.array(points[pb], dtype=float)
        L = float(np.linalg.norm(b - a))
        G.add_edge(pa, pb, seg_id=sid, length=L)
    return G


def adjacency_with_length(G):
    """返回 {端点: [(邻居, 边长)]}"""
    return {n: [(nbr, G[n][nbr]['length']) for nbr in G.neighbors(n)] for n in G.nodes()}


def neighbor_count(G):
    """返回 {端点: 邻接巷道数}"""
    return {n: G.degree(n) for n in G.nodes()}
