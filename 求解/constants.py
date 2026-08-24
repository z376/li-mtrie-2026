"""2025 D 题 全局常量（跨问题复用）

按 skill/references/导入规范.md 要求：所有跨问题物理常量集中定义。
"""
# -*- coding: utf-8 -*-

# ========== 巷道几何 ==========
B = 4.0          # 巷道断面宽 (m)
H_MAX = 3.0      # 巷道断面高 (m)
H_0 = 0.1        # 初始水位 (m)

# ========== 突水参数 ==========
Q_IN = 30.0      # 单源突水量 (m^3/min)
U_FLOW = Q_IN / (B * H_0)   # 单源流速 (m/min) = 75
# 分摊后单条巷道流量 Q_k = Q_IN / K_path, 流速仍 = Q_k / (B*H_0) = U_FLOW
# (水位 h 不变, 所以流速 u 不变, 只影响充满时间)

# 巷道充满 3m 水位所需时间 (流量 Q_k 时): 12*L / Q_k
# 若 Q_k = Q_IN/K: 12*L*K / Q_IN = 0.4*K*L (min)

# ========== 工人速度 (m/s, 都要换算成 m/min) ==========
V_DRY = 4.0      # 无水
V_UP = 1.0       # 逆水, 水深 <= 0.3m
V_DOWN = 2.0     # 顺水, 水深 <= 0.3m
V_DRY_MIN = V_DRY * 60
V_UP_MIN = V_UP * 60
V_DOWN_MIN = V_DOWN * 60
WADE_LIMIT = 0.3  # 涉水深度上限 (m), 超过禁止通行

# ========== 时序参数 ==========
T_ALARM = 1.0    # 报警延迟 (min), 突水后 1 min 工人才开始逃
T_B_DELAY_1 = 4.0  # 附件1 第二突水点延迟 (min)
T_B_DELAY_2 = 5.0  # 附件2 第二突水点延迟 (min)

# ========== 突水点 (附件 1 / 附件 2) ==========
SOURCE_A1 = (5349.03, 4931.90, 10.00)  # 附件1 突水点 A1
SOURCE_A2 = (4143.12, 4376.28,  6.33)  # 附件2 突水点 A2
SOURCE_B1 = (3760.40, 3808.33, 10.00)  # 附件1 第二突水点 B1 (Q3)
SOURCE_B2 = (5883.14, 5643.35, 40.37)  # 附件2 第二突水点 B2 (Q3)

# ========== 出入口 + 工人位置 ==========
# 附件 1
EXIT_1_1 = (3252.16, 3326.63, 10.00)   # 出入口 1
EXIT_1_2 = (3173.10, 2819.97, 10.00)   # 出入口 2
WORKER_1_1 = (5808.18, 5367.75, 10.00)  # 工人 1
WORKER_1_2 = (5194.00, 4785.31, 10.00)  # 工人 2
WORKER_1_3 = (6190.81, 3434.29, 10.00)  # 工人 3
# 附件 2
EXIT_2_1 = (6336.99, 6073.22, 36.15)
EXIT_2_2 = (6416.05, 6579.88,  8.69)
WORKER_2_1 = (4395.15, 4614.53,  6.59)
WORKER_2_2 = (3398.34, 5965.56,  1.31)
WORKER_2_3 = (3879.44, 4125.47,  6.22)

# ========== 文件路径 ==========
import os
# 用相对于工作目录的路径, 避免 Python sys.path GBK 编码问题
# 调用方必须先 chdir 到 求解/ 目录
BASE_DIR = os.path.abspath('..')
DATA_DIR = os.path.join(BASE_DIR, '数据', '附件')
TEMPLATE_DIR = os.path.join(DATA_DIR, '附件3')
RESULT_TPL = {
    1: os.path.join(TEMPLATE_DIR, 'result1-{j}.xlsx'),
    2: os.path.join(TEMPLATE_DIR, 'result2-{j}.xlsx'),
    3: os.path.join(TEMPLATE_DIR, 'result3-{j}.xlsx'),
    4: os.path.join(TEMPLATE_DIR, 'result4-{j}.xlsx'),
}

# 中文 sheet 名 (用变量避免 Python 解析路径时 GBK 问题)
SHEET_NODE = '\u7aef\u70b9'   # 端点
SHEET_SEG = '\u5df7\u9053'     # 巷道
SHEET_NODE_ARR = '\u7aef\u70b9\u6c34\u6d41\u5230\u8fbe\u65f6\u523b'  # 端点水流到达时刻
SHEET_SEG_FULL = '\u5df7\u9053\u6c34\u6d41\u5145\u6ee1\u65f6\u523b'  # 巷道水流充满时刻
