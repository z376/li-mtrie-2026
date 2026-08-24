"""写 result xlsx 模板 (保留原格式 + dtype 修复)

按 C-3 测试报告踩坑: xlsx 模板 string/float dtype 混合, 必须 astype(object) 再 iloc.
"""
# -*- coding: utf-8 -*-
import os
import pandas as pd
import shutil


def write_flow_result(template_path, output_path, t_arr_dict, t_full_dict,
                      points, segments):
    """写 result1-x / result3-x 模板

    Args:
        template_path: 模板路径
        output_path: 输出路径
        t_arr_dict: {端点编号: 到达时刻 (min)}
        t_full_dict: {巷道编号: 充满时刻 (min) or None}
    """
    shutil.copyfile(template_path, output_path)
    xl = pd.ExcelFile(output_path)

    # sheet1: 端点水流到达时刻
    if '端点水流到达时刻' in xl.sheet_names:
        df = pd.read_excel(output_path, sheet_name='端点水流到达时刻', header=None)
        df = df.astype(object)
        # 数据从行 2 开始, 列 1 (第 0 列是端点编号, 不要改)
        for i, pid in enumerate(points.keys()):
            row = 2 + i
            if row >= len(df):
                break
            t = t_arr_dict.get(pid)
            if t is not None:
                df.iloc[row, 1] = round(float(t), 2)
        with pd.ExcelWriter(output_path, engine='openpyxl', mode='a',
                            if_sheet_exists='replace') as w:
            df.to_excel(w, sheet_name='端点水流到达时刻', index=False, header=False)

    # sheet2: 巷道水流充满时刻
    if '巷道水流充满时刻' in xl.sheet_names:
        df = pd.read_excel(output_path, sheet_name='巷道水流充满时刻', header=None)
        df = df.astype(object)
        for i, sid in enumerate(segments.keys()):
            row = 2 + i
            if row >= len(df):
                break
            t = t_full_dict.get(sid)
            if t is not None:
                df.iloc[row, 1] = round(float(t), 2)
        with pd.ExcelWriter(output_path, engine='openpyxl', mode='a',
                            if_sheet_exists='replace') as w:
            df.to_excel(w, sheet_name='巷道水流充满时刻', index=False, header=False)


def write_escape_result(template_path, output_path, worker_results,
                        points):
    """写 result2-x / result4-x 模板

    Args:
        template_path: 模板路径
        output_path: 输出路径
        worker_results: list of 3 个 dict, 每个 dict {
            'worker_xyz': (x,y,z),  # 起点
            'path': [(x, y, z, t, seg_id), ...],  # 路径节点 + 到达时刻 + 走的巷道
        }
    """
    shutil.copyfile(template_path, output_path)
    xl = pd.ExcelFile(output_path)

    worker_sheets = [s for s in xl.sheet_names if s.startswith('工人')]
    for sheet_name, worker_data in zip(worker_sheets, worker_results):
        df = pd.read_excel(output_path, sheet_name=sheet_name, header=None)
        df = df.astype(object)
        # 行 2 = 起点 (序号 0), 已知 worker_xyz
        wx, wy, wz = worker_data['worker_xyz']
        df.iloc[2, 0] = 0
        df.iloc[2, 1] = wx
        df.iloc[2, 2] = wy
        df.iloc[2, 3] = wz
        df.iloc[2, 4] = worker_data.get('start_time', 1.0)
        df.iloc[2, 5] = None  # 起点不走巷道
        # 行 3-7 = 序号 1-5 (5 步, 总 6 段)
        path = worker_data.get('path', [])
        for step_i, (px, py, pz, pt, sid) in enumerate(path[:5]):
            row = 3 + step_i
            if row >= len(df) - 1:  # 留 "……" 行
                break
            df.iloc[row, 0] = step_i + 1
            df.iloc[row, 1] = px
            df.iloc[row, 2] = py
            df.iloc[row, 3] = pz
            df.iloc[row, 4] = round(float(pt), 2) if pt is not None else None
            df.iloc[row, 5] = sid
        with pd.ExcelWriter(output_path, engine='openpyxl', mode='a',
                            if_sheet_exists='replace') as w:
            df.to_excel(w, sheet_name=sheet_name, index=False, header=False)
