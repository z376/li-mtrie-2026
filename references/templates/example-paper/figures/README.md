# figures/ — 示例图（仅形式参考，参赛前必须替换）

> 借鉴自 **数模陪跑独家 2026 国赛 LaTeX 模板** (其内部又引用自
> "2026 华数杯 A 论文" / "26 亚太杯中文赛 B 论文")。
> 本 skill **不主张**也**不支持**把这些图直接用于参赛论文。

## ⚠️ 三件必做

1. **整图替换** — 这些 PNG 都是从其他比赛获奖论文里截的真实图，
   参赛时必须换成你自己程序跑出来的图。
2. **删图题来源** — 原始 PNG 的图题里带
   `（来源：2026 华数杯 A 论文）` / `（来源：26 亚太杯中文赛 B 论文）`
   这样的元信息，使用前必须删掉。
3. **检查图例** — 有些图的颜色 / 线型是按其原始数据设计的，
   替换为自己的数据后颜色映射可能不再合理。

## 文件清单

| 文件名 | 形式参考 | 适用位置 |
|--------|---------|---------|
| `overall_route_example.png`      | 总体技术路线流程图 | `2.总体分析.tex` |
| `q1_route_example.png`           | 问题一求解流程图   | `5.1.1.分析与准备.tex` |
| `q2_route_example.png`           | 问题二求解流程图   | `5.1.2.建模与求解.tex`（或新增的 5.2） |
| `result_comparison_example.png`  | 多方案对比曲线     | `5.1.2.建模与求解.tex` 结果分析 |
| `result_contour_example.png`     | 等高线 / 可行域图 | `5.1.2.建模与求解.tex` 结果分析 |
| `result_target_example.png`      | 目标达成度 / 误差变化曲线 | `6.模型检验.tex` |
| `result_tradeoff_example.png`    | 多方案权衡分区图   | `6.模型检验.tex` |
| `robustness_distribution_example.png` | 鲁棒性扰动分布对比 | `6.模型检验.tex` 6.2 |
| `stability_example.png`          | 稳定性分析图       | `6.模型检验.tex` 6.2 |
| `validation_bootstrap_example.png` | Bootstrap 重抽样检验 | `6.模型检验.tex` 6.1 |

## 怎么用

1. 选一张形式上贴近你问题的图，参考其布局 / 坐标轴 / 图例
2. 用你自己的程序画一张新图（matplotlib / seaborn / plotly 都行）
3. 导出 PNG，覆盖同名的 `_example.png` 文件（或改个新名字同步更新 `\includegraphics` 引用）
4. 在 PDF 里核对：图是否清楚、图题是否唯一、坐标轴 / 单位 / 图例是否齐全

## 如果你不想用任何示例图

直接清空 `figures/`（保留这个 `README.md` 即可），
从 `\includegraphics` 引用里删掉对应的图片行。
