# -*- coding: utf-8 -*-
"""
问题X：【问题简述】
方法：【主要方法】

说明：本文件是求解代码模板，复制到 求解/问题X/ 下后，按 TODO 填充。
绘图库不限制（matplotlib / seaborn / plotly / Pillow 均可）。

═══════════════════════════════════════════════════════════════
⚠️ **数据驱动题模板** — 适用：评价/预测/分类/统计类题
═══════════════════════════════════════════════════════════════

**机理题**（A 题为主、部分 B/D）请改用 `references/mechanism-template.py`，它有：
- 物理参数集中定义区
- 几何/运动学核心函数区
- 数值方法（scipy）导入提示
- numpy 向量化示例

═══════════════════════════════════════════════════════════════
⚠️ **Windows GBK 终端兼容**（重要，2025 B 题踩坑）
═══════════════════════════════════════════════════════════════

**避免在 print 字符串中使用**（GBK 终端会报 `UnicodeEncodeError`）：
- ❌ Emoji: ✅ ❌ ⚠️ ⏭️ 🎉
- ❌ 特殊符号: ✓ ✗ → ← ※ ① ②
- ❌ Unicode 上下标: cm⁻¹ m² ½ ¹²
- ❌ 希腊字母 + 波浪线: ν̃ θ̃ Δν

**改用 ASCII 替代**：
- ✅ → `[OK]`
- ❌ → `[X]` 或 `False`
- ⚠️ → `[WARN]`
- → → `->`
- cm⁻¹ → `cm-1`
- ν̃ → `nu` 或 `nu_tilde`
- 希腊字母: θ → `theta`, μ → `mu`, Δ → `delta`

**或者**在脚本顶部加（强制 UTF-8 输出）：
```python
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

**经验**：写代码时**默认用 ASCII**，只在文档/字符串里用 Unicode 注释解释。

═══════════════════════════════════════════════════════════════
⚠️ **性能警示** — O(N²) 循环会爆栈，用 numpy 向量化
═══════════════════════════════════════════════════════════════

❌ 错误（O(N²) 距离计算, 500 步 = 2500 万次，2 分钟）：
    for t in times:
        for i in range(N):
            for j in range(i+2, N):
                sep = np.linalg.norm(positions[i] - positions[j])  # 慢！

✅ 正确（numpy 向量化, 500 步 < 1 秒）：
    for t in times:
        diff = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        dists = np.sqrt((diff * diff).sum(axis=2))
        upper_dists = dists[np.triu(np.ones((N, N), dtype=bool), k=2)]
        min_sep = float(upper_dists.min())

🆕 自检闭环集成（v1.3）：
- save_fig()   基础版：仅保存
- save_fig_with_qa()  增强版：保存后自动跑 visual_qa 缺字/越界/重叠自检
                       并渲 PNG 预览给 AI 读图复核
"""
import pandas as pd
import numpy as np
import os, sys, warnings
warnings.filterwarnings('ignore')

# ==================== ⚠️ Windows GBK 终端兼容(自动应用) ====================
# 模板里有 emoji (✅ ❌ ⚠️) 在 GBK 终端下 print 会报 UnicodeEncodeError
# 这里在 import 阶段就强制 UTF-8,调用方无需关心
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # Python < 3.7 或 stream 已关闭时降级到 TextIOWrapper
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass


# ==================== 数据目录自动扫描 ====================
def scan_data_dir(data_dir='数据'):
    """扫描 数据/ 目录，自动发现数据文件并返回路径字典。

    返回:
        dict: { 'xlsx': [...], 'csv': [...], 'txt': [...], 'img': [...] }
              值为相对于 data_dir 的相对路径列表
    """
    data_dir = os.path.abspath(data_dir)
    if not os.path.isdir(data_dir):
        print(f"[WARN] 数据目录不存在: {data_dir}")
        return {}

    result = {'xlsx': [], 'csv': [], 'txt': [], 'img': [], 'other': []}
    for root, dirs, files in os.walk(data_dir):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), data_dir)
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.xlsx', '.xls'):
                result['xlsx'].append(rel)
            elif ext == '.csv':
                result['csv'].append(rel)
            elif ext in ('.txt', '.dat', '.tsv'):
                result['txt'].append(rel)
            elif ext in ('.png', '.jpg', '.jpeg', '.bmp', '.gif'):
                result['img'].append(rel)
            else:
                result['other'].append(rel)

    print(f"\n{'='*50}")
    print(f"数据目录扫描结果: {data_dir}")
    print(f"{'='*50}")
    for category, files in result.items():
        if files:
            print(f"\n{category.upper()} ({len(files)} 个):")
            for f in sorted(files):
                size_kb = os.path.getsize(os.path.join(data_dir, f)) / 1024
                print(f"  {f} ({size_kb:.1f} KB)")
    if not any(result.values()):
        print("\n[INFO] 数据目录为空，请放入题目附件数据文件")
    return result

# 使用示例（取消注释运行）:
# data_files = scan_data_dir()
# if data_files.get('xlsx'):
#     df = pd.read_excel(os.path.join('数据', data_files['xlsx'][0]))

# ==================== visual_qa 集成（程序自检闭环） ====================
# 借鉴自 scipilot-figure-skill —— 拦截缺字、文字越界、刻度重叠三类确定性错误
# 导入失败时降级（不影响主流程），用户可手动安装到 references/scripts/ 后启用
try:
    _SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _SCRIPTS = os.path.join(_SKILL_ROOT, 'references', 'scripts')
    if os.path.isdir(_SCRIPTS):
        sys.path.insert(0, _SCRIPTS)
        from visual_qa import audit_layout, render_preview
        _HAS_VISUAL_QA = True
    else:
        _HAS_VISUAL_QA = False
except Exception:
    _HAS_VISUAL_QA = False

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


def save_fig_with_qa(fig, name_cn, dpi=200, ai_review=True):
    """🆕 增强版 save_fig：保存后自动跑 visual_qa 自检

    自动检测：
    - 缺字乱码（FAIL）：matplotlib 缺字警告
    - 文字越界裁切（WARN）：Text 超出画布
    - 刻度标签重叠（WARN）：相邻 tick label 包围盒相交

    可选 ai_review=True 时：同时渲一张中分辨率 PNG 预览（给 AI 读图复核感知性问题）

    用法（替换 save_fig）:
        save_fig_with_qa(fig, '问题1_预测对比.png')
    """
    out = os.path.join(FIG_DIR, name_cn)
    fig.savefig(out, dpi=dpi, bbox_inches='tight', facecolor='white')

    if not _HAS_VISUAL_QA:
        print(f"  [FIG] {name_cn} 已保存 ({os.path.getsize(out)//1024} KB) [QA 不可用: visual_qa 未导入]")
        plt.close(fig)
        return

    # 程序自检
    issues = audit_layout(fig)
    fail = [m for s, m in issues if s == 'FAIL']
    warn = [m for s, m in issues if s == 'WARN']

    if fail:
        print(f"  [FIG] {name_cn} 已保存 ❌ QA 失败 ({len(fail)} FAIL):")
        for m in fail:
            print(f"        - {m}")
    elif warn:
        print(f"  [FIG] {name_cn} 已保存 ⚠️  QA 警告 ({len(warn)} WARN):")
        for m in warn[:3]:  # 只列前 3 条
            print(f"        - {m}")
        if len(warn) > 3:
            print(f"        - ... 等 {len(warn)-3} 条")
    else:
        print(f"  [FIG] {name_cn} 已保存 ✅ QA 通过")

    # AI 读图用 PNG 预览
    if ai_review:
        preview_path = out.rsplit('.', 1)[0] + '_预览.png'
        try:
            render_preview(fig, preview_path, dpi=120)
            print(f"        AI 读图预览: {os.path.basename(preview_path)}")
        except Exception as e:
            print(f"        (预览生成失败: {e})")

    plt.close(fig)


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

# ⚠️ xlsx 模板填写注意事项（2024 C 题踩坑）：
#   1. 模板单元格混合 string（标签）和 float（NaN 数值）
#   2. 直接 `df.iloc[i, j] = 0.0` 会触发 string dtype 检查 → TypeError
#   3. **必须**先 `df = df.astype(object)` 再 iloc 写
#
# 多 sheet 模板：先遍历所有 sheet，每个 sheet 都转 object，最后用 ExcelWriter 写
# 例（多 sheet 7 年）:
#   all_sheets = {}
#   for sn in pd.ExcelFile('数据/附件3/result1_1.xlsx').sheet_names:
#       all_sheets[sn] = pd.read_excel('数据/附件3/result1_1.xlsx', sheet_name=sn, header=None).astype(object)
#   all_sheets['2024'].iloc[1, 2] = 5.0  # 修改
#   with pd.ExcelWriter('结果/result1_1_filled.xlsx', engine='openpyxl') as w:
#       for sn, df in all_sheets.items():
#           df.to_excel(w, sheet_name=sn, header=False, index=False)
#

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
# save_fig_with_qa(fig, '问题X_销售额预测.png')  # 🆕 增强版：自动跑 QA 自检
#                                                        # 普通版用 save_fig(fig, ...)
#                                                       # 论文里用 \includegraphics 引用

# TODO: 保存结果
# save_csv(result_df, '问题X_结果.csv')

print("\n✅ 问题X求解完成！")
