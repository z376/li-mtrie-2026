# -*- coding: utf-8 -*-
"""
问题X：【问题简述】
方法：【主要方法】

说明：本文件是求解代码模板，复制到 求解/问题X/ 下后，按 TODO 填充。
绘图库不限制（matplotlib / seaborn / plotly / Pillow 均可）。
"""
import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

# ==================== 绘图全局配置（论文图片专用 · 必须复制到画图脚本顶部） ====================
# ⚠️ 这些设置是为了让图打印到论文（A4 0.8\textwidth ≈ 12cm × 9cm）时文字、线条、点足够清晰
# 默认 matplotlib 字号 10pt 在论文里看不清，必须调大
# 完整规范见 references/绘图规范.md

import matplotlib
matplotlib.use('Agg')  # 无 GUI 后端
import matplotlib.pyplot as plt

# 全局 rcParams（一次性设置，画图脚本里所有 plt.* 都生效）
plt.rcParams.update({
    # ===== 字体（中文必须显式指定） =====
    'font.sans-serif': ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans'],
    'font.family': 'sans-serif',
    'axes.unicode_minus': False,  # 负号正常显示
    # ===== 字号（论文里要清晰可读） =====
    'font.size': 14,           # 基础字号
    'axes.titlesize': 16,      # 子图标题（一般不用，论文里 caption 承担）
    'axes.labelsize': 16,      # 坐标轴标签 ★
    'xtick.labelsize': 14,      # x 轴刻度
    'ytick.labelsize': 14,      # y 轴刻度
    'legend.fontsize': 13,      # 图例 ★
    'figure.titlesize': 16,    # 总标题（一般不用）
    # ===== 线条 / 标记（避免打印糊掉） =====
    'lines.linewidth': 2.0,        # 折线粗细（默认 1.5 太细）
    'lines.markersize': 8,         # 标记点大小
    'axes.linewidth': 1.2,         # 坐标轴边框线宽
    'grid.linewidth': 0.6,         # 网格线宽
    'xtick.major.width': 1.0,
    'ytick.major.width': 1.0,
    # ===== 保存（高 DPI 防止糊） =====
    'figure.dpi': 120,          # 屏幕显示
    'savefig.dpi': 200,        # ★ 保存文件 dpi（150 是底线，200 更清晰）
    'savefig.bbox': 'tight',   # 去掉多余白边
    'savefig.pad_inches': 0.1,
    'savefig.facecolor': 'white',
    # ===== 子图布局 =====
    'figure.constrained_layout.use': True,  # 自动避免标签重叠
})

# ==================== 目录配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE_DIR, '图片')
OUT_DIR = os.path.join(BASE_DIR, '结果')
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ==================== 工具函数 ====================

def save_csv(df, name_cn):
    """保存CSV"""
    df.to_csv(os.path.join(OUT_DIR, name_cn), index=False, encoding='utf-8-sig')
    print(f"  [CSV] {name_cn} 已保存")


def print_stats(data, name="数据", cols=None):
    """打印数据统计信息（供论文引用）"""
    if cols is None:
        cols = data.select_dtypes(include=[np.number]).columns.tolist()
    print(f"\n{'='*60}")
    print(f"  {name} 统计摘要")
    print(f"{'='*60}")
    for col in cols:
        s = data[col].dropna()
        if len(s) == 0:
            continue
        print(f"  {col}:")
        print(f"    min={s.min():.4f}  max={s.max():.4f}  mean={s.mean():.4f}")
        cv_str = f"cv={s.std()/s.mean()*100:.1f}%" if s.mean() != 0 else "cv=N/A"
        print(f"    std={s.std():.4f}  {cv_str}  amp={s.max()-s.min():.4f}")
    print(f"{'='*60}\n")


def save_fig(fig, name_cn, dpi=200):
    """统一保存图片到 FIG_DIR，文件名用中文

    使用方法：先 plt.subplots() 拿到 fig，画完后调 save_fig(fig, 'xxx.png')
    """
    out = os.path.join(FIG_DIR, name_cn)
    fig.savefig(out, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  [FIG] {name_cn} 已保存 ({os.path.getsize(out)//1024} KB)")


# ==================== 第一阶段：数据加载与预处理 ====================
print("=" * 60)
print("  第一阶段：数据加载与预处理")
print("=" * 60)

# TODO: 加载数据
# df = pd.read_excel('../../数据/xxx.xlsx')
# print(f"数据规模：{df.shape}")

# TODO: 数据预处理
# ...

# ==================== 第二阶段：建模与求解 ====================
print("\n" + "=" * 60)
print("  第二阶段：建模与求解")
print("=" * 60)

# TODO: 模型建立
# ...

# TODO: 模型求解
# ...

# ==================== 第三阶段：结果输出与可视化 ====================
print("\n" + "=" * 60)
print("  第三阶段：结果输出与可视化")
print("=" * 60)

# TODO: 打印统计信息
# print_stats(result_df, "求解结果")

# TODO: 画图（示例 ↓↓↓）
#
# import matplotlib.pyplot as plt
# fig, ax = plt.subplots(figsize=(8, 5))  # 单图建议 8x5 inch
#
# ax.plot(x, y, marker='o', label='实验值', color='#1f77b4')
# ax.plot(x, y_pred, '--', label='预测值', color='#ff7f0e')
#
# ax.set_xlabel('时间')                  # 中文坐标轴标签（14-16pt 已配）
# ax.set_ylabel('销售额 / 万元')          # 中文 y 轴标签
# ax.legend(loc='best')                  # 图例
# ax.grid(True, alpha=0.3)               # 浅色网格
#
# save_fig(fig, '问题X_销售额预测.png')  # 保存到 图片/ 目录
#                                                       # 论文里用 \includegraphics 引用

# TODO: 保存结果
# save_csv(result_df, '问题X_结果.csv')

print("\n✅ 问题X求解完成！")
