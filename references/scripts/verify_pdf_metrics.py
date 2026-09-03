# -*- coding: utf-8 -*-
"""
li-mtrie-2026 PDF 成品结构程序化体检（PyMuPDF）
=============================================
借鉴自 cumcm-live-workflow-skill v5.0 references/verify_pdf_metrics.py
(2.4 KB, 66 lines) 并适配到 li-mtrie-2026 2026 规范 + CUMCMthesis 格式。

用途: 论文 PDF 交付前做 4 项体检:
  1. 结构: 每页首行/字数 → 摘要是否单页、正文页码范围
  2. 越界: bbox 检测表格/内容是否越右边界 (max x ≤ 右边距)
  3. 匿名: PDF 元数据 (author/title/keywords) 应为空
  4. 关键数字: compact 去空白匹配 (规避字体间距导致匹配失败)

用法:
  python verify_pdf_metrics.py <论文.pdf> [关键数字1 关键数字2 ...]

  示例:
    python verify_pdf_metrics.py 论文/论文.pdf
    python verify_pdf_metrics.py 论文/电子版.pdf 0.4503 412.47 8.25

依赖:
  pip install PyMuPDF
"""
import sys
import re

# Windows GBK console 兼容 (verify_pdf_metrics.py 用 emoji, 必修)
# Python 3.7+
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass  # 旧 Python / 非 stdout 对象, 跳过

# 2026 规范第一条: 上下左右页边距 ≥ 2.5 cm
# CUMCMthesis 实际是 2.5 cm (= 0.984 inch ≈ 70.85pt)
# 1 cm ≈ 28.3465 pt (PostScript point)
RIGHT_MARGIN_PT = 2.5 * 28.3465  # = 70.87 pt
TOP_MARGIN_PT = 2.5 * 28.3465
BOTTOM_MARGIN_PT = 2.5 * 28.3465
LEFT_MARGIN_PT = 2.5 * 28.3465


def verify(path, key_numbers=()):
    """主体检函数. 返回 0 = 通过, 1 = 有警告."""
    try:
        import pymupdf as fitz  # PyMuPDF ≥1.24 推荐, fitz 旧别名仍兼容
    except ImportError:
        import fitz  # PyMuPDF <1.24 fallback
    doc = fitz.open(path)
    print(f'页数: {len(doc)}')

    # 1) 结构: 每页首行 + 字数
    print('\n[1] 结构 (每页首行 + 字数)')
    for i, page in enumerate(doc):
        lines = [l for l in page.get_text().split('\n') if l.strip()]
        head = lines[0][:50] if lines else '(空)'
        chars = len(page.get_text())
        marker = ' <- 摘要页' if i == 0 and '关键词' in page.get_text() else ''
        print(f'  p{i+1}: {head} | {chars}字符{marker}')

    # 2) 越界检测
    print('\n[2] 越界检测 (max_x > 右边距 = 2.5cm)')
    boundary_violations = 0
    for i, page in enumerate(doc):
        words = page.get_text('words')
        if not words:
            continue
        maxx = max(w[2] for w in words)
        maxy = max(w[3] for w in words)
        minx = min(w[0] for w in words)
        limit_right = page.rect.width - RIGHT_MARGIN_PT
        limit_top = TOP_MARGIN_PT
        limit_bottom = page.rect.height - BOTTOM_MARGIN_PT
        limit_left = LEFT_MARGIN_PT
        if maxx > limit_right + 1:
            print(f'  ⚠ p{i+1}: 右越界 max_x={maxx:.1f}pt > 右边距 {limit_right:.1f}pt')
            boundary_violations += 1
        if minx < limit_left - 1:
            print(f'  ⚠ p{i+1}: 左越界 min_x={minx:.1f}pt < 左边距 {limit_left:.1f}pt')
            boundary_violations += 1
        if maxy > limit_bottom + 1:
            print(f'  ⚠ p{i+1}: 下越界 max_y={maxy:.1f}pt > 下边距 {limit_bottom:.1f}pt')
            boundary_violations += 1
    if boundary_violations == 0:
        print('  ✓ 全部页内容在 2.5cm 边距内')

    # 3) 元数据匿名
    print('\n[3] 元数据匿名 (author/title/keywords 应为空)')
    md = doc.metadata
    leak = {k: v for k, v in md.items() if v and k in ('title', 'author', 'subject', 'keywords')}
    if not leak:
        print('  ✓ OK(空) - 匿名通过')
    else:
        print(f'  ⚠ 有信息: {leak}')
        print('  → 修复: 在 format.cls / 论文.tex 顶部加 \\hypersetup{pdfauthor={}, pdftitle={}, pdfkeywords={}}')

    # 4) 关键数字出现次数
    print('\n[4] 关键数字出现次数 (compact 去空白)')
    full = re.sub(r'\s+', '', '\n'.join(p.get_text() for p in doc))
    for num in key_numbers:
        n = full.count(str(num))
        marker = ' ✓' if n >= 1 else ' ⚠ 未出现'
        print(f'  {num}: {n} 次{marker}')

    # 5) LaTeX 未定义引用
    undefined = full.count('??')
    print(f'\n[5] LaTeX 未定义引用: {undefined} 处')
    if undefined > 0:
        print('  ⚠ 存在 ?? 标记, 需跑第二次 xelatex 稳定交叉引用')

    # 6) 摘要页判断 (第1页是否只有摘要 + 关键词)
    print('\n[6] 摘要页判断')
    p1 = re.sub(r'\s+', '', doc[0].get_text())
    has_keywords = '关键词' in p1
    has_problem = '问题重述' in p1
    has_ai = 'AI工具使用声明' in p1 or 'AI 工具使用声明' in p1
    print(f'  含"关键词": {has_keywords} {"✓" if has_keywords else "⚠ 摘要页无关键词"}')
    print(f'  含"问题重述": {has_problem} (应为 False = 摘要未溢出)')
    if has_problem:
        print('  ⚠ 摘要页包含问题重述, 可能超 1 页 (2026 规范第三条: 摘要 ≤ 1 页)')
    print(f'  含"AI 工具使用声明": {has_ai} (正常情况下, 论文版摘要页应不包含)')

    # 总评
    has_issues = boundary_violations > 0 or leak or undefined > 0 or has_problem
    print('\n========== 总评 ==========')
    if not has_issues:
        print('✓ 全部通过, 可提交')
        return 0
    else:
        print('⚠ 有问题, 见上方提示')
        return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python verify_pdf_metrics.py <论文.pdf> [关键数字1 关键数字2 ...]')
        print('示例: python verify_pdf_metrics.py 论文/论文.pdf 0.4503 412.47')
        print('依赖: pip install PyMuPDF')
        sys.exit(1)
    sys.exit(verify(sys.argv[1], sys.argv[2:]))
