# -*- coding: utf-8 -*-
"""合并 绘图规范.md + 绘图避坑.md → 绘图规范与避坑.md"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

base = r'C:\Users\admin\.minimax\skills\li-mtrie（2026）\references'
spec = open(base + r'\绘图规范.md', 'r', encoding='utf-8').read()
pitfall = open(base + r'\绘图避坑.md', 'r', encoding='utf-8').read()

# 1. 提取 spec 的头部 + 决策三轴 (§0 第一部分到 §0 决策三轴 末尾)
# 找到 "### 18 条画图陷阱清单" 之前的所有内容
spec_split = spec.split('### 18 条画图陷阱清单')
spec_header = spec_split[0]  # 头部 + 决策三轴
# spec_rest = §1+ 内容
spec_rest = '### 18 条画图陷阱清单'.join(spec_split[1:])  # 18 条速查表 + 其后
# spec_rest 还需要去掉 §0 的 18 条速查表 (因为完整版在 pitfall)
spec_rest_split = spec_rest.split('### 出图后程序自检')
spec_18pitfall_quick = spec_rest_split[0]  # 18 条速查表部分
spec_after_18 = '### 出图后程序自检'.join(spec_rest_split[1:])  # 出图后自检 + 之后

# 2. 提取 pitfall 的目录 + 18 条 + 拦截话术
# pitfall 文件结构: §目录, §P1-P18, §拦截发生时的话术
pitfall_split = pitfall.split('## 目录')
pitfall_header = pitfall_split[0]  # 文件头部 (含 # 标题和警告)
pitfall_rest = '## 目录'.join(pitfall_split[1:])  # 目录 + 18 条 + 话术
pitfall_rest_split = pitfall_rest.split('## P1. 均值柱状图掩盖分布与样本量')
pitfall_toc = pitfall_rest_split[0]  # 目录
pitfall_18 = '## P1. 均值柱状图掩盖分布与样本量'.join(pitfall_rest_split[1:])  # P1-P18 + 话术
pitfall_18_split = pitfall_18.rsplit('## 拦截发生时的话术', 1)
pitfall_18_main = pitfall_18_split[0]  # P1-P18 完整
pitfall_18_end = pitfall_18_split[1] if len(pitfall_18_split) > 1 else ''  # 拦截话术

# 3. 合并: 头部 + spec_header (决策3轴) + spec_after_18 (出图后自检 + 后续) + pitfall 18 条 (作为权威) + 协同段
new_content = (
    spec_header  # 头部 + 决策三轴
    + '\n\n---\n\n## §2. 18 条画图陷阱清单 (What Not — 主动拦截, 完整版)\n\n'
    + '> 本节是 **权威完整版**, 来自 scipilot-figure-skill 的"主动拦截"清单. 画完**逐项对照**自检. 18 条按重要性 + 出现频次排序.\n\n'
    + pitfall_18_main  # P1-P18 完整
    + '\n\n---\n\n'
    + '## §3. 出图后程序自检 + 完整 matplotlib 设置\n\n'
    + spec_after_18  # 出图后自检 + §1 字号 + §2 线条 + ... + §12 机理题
    + '\n\n---\n\n'
    + '## §4. 协同路径 (How → What Not → 程序化合规)\n\n'
    + '**完整协同**:\n'
    + '1. **画图前** 看 §1 决策三轴 (选对图型)\n'
    + '2. **画图后** 用 §2 18 条陷阱清单逐项自检 (主动拦截错误)\n'
    + '3. **画图前/中** 看 §3 matplotlib 推荐值 + 字号/线宽/DPI (How, 怎么写对)\n'
    + '4. **提交前** 跑 `references/scripts/check_figure.py` 程序化合规 (DPI ≥ 200)\n\n'
    + '**与本文件合并的来源**:\n'
    + '- `references/绘图规范.md` (v1.5.7.5 — 21.4 KB) — How 部分 (§1 决策 + §3 matplotlib 设置)\n'
    + '- `references/绘图避坑.md` (v1.5.7.0 — 15.9 KB) — What Not 部分 (§2 18 条陷阱完整)\n\n'
    + '---\n\n'
    + '## §5. 与现有文档的协同\n\n'
    + '- `references/paper-spec.md §3 模型建立与求解` — 论文中图表写作规范\n'
    + '- `references/AIGC降重策略.md` (v1.5.7.18) — 图表也算 AIGC 检测维度 (模板化布局)\n'
    + '- `references/scripts/check_figure.py` — 程序化合规检查 (DPI ≥ 200)\n'
    + '- `references/scipilot-figure-skill/` (借鉴源) — 完整 18 条陷阱的原始出处\n\n'
    + '---\n\n'
    + '## §6. 版本历史\n\n'
    + '- **v1.5.7.19 (本文件)**: 合并 `references/绘图规范.md` (21.4 KB) + `references/绘图避坑.md` (15.9 KB) → 约 35 KB (新增协同段 + 去重). 总 KB 增加是因保留全部章节, 但避免了"两个绘图文档"造成的认知负担.\n'
    + '- **v1.5.7.5 之前**: 两个文档独立, 显式分工 (绘图规范 = How, 绘图避坑 = What Not).\n'
)

new_path = base + r'\绘图规范与避坑.md'
with open(new_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'已写入: {new_path}')
print(f'字数: {len(new_content)}')