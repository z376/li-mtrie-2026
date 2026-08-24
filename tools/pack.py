"""打包 li-mtrie-2026 skill 为 zip (v3 修复 GBK).

两个版本:
- 完整包 (含 fonts/):  ~19MB, 开箱即用, 编译无需装字体
- 轻量包 (不含 fonts/): ~0.5MB, 适合分享/备份, 编译需自装思源宋体

排除:
- .git/, .vscode/, .idea/, __pycache__/
- *.aux/*.log/*.out/*.toc/*.synctex.gz/*.bbl/*.blg/*.fdb_latexmk/*.fls
- *.pyc, *.bak, *.tmp, *.swp
- Thumbs.db, desktop.ini, .DS_Store, nul

保留:
- fonts/  (可选, 仅完整包)
- *.pdf   (已编译 PDF, 效果展示)
- 所有 .tex/.md/.py/.cls/.bib
"""
import os
import sys
import zipfile
from pathlib import Path

# 路径用相对（不依赖绝对路径，方便他人复用）
ROOT = Path(__file__).parent.parent
OUT_BASE = Path(__file__).parent.parent.parent

EXCLUDE_DIRS = {
    '.git', '.vscode', '.idea', '__pycache__', 'node_modules',
    # 排除测试/分享时可能含敏感数据的目录（用户实际填的题/数据/求解结果不进 skill 包）
    '求解',       # 求解过程产物 (脚本、图片、result xlsx)
    '求解_C',     # C 题测试过程产物
    '_archive',   # 历史归档（A 题数据已挪到 _archive/）
    '题目',       # 赛题 PDF（版权）
    '数据',       # 附件 xlsx（版权）
}
EXCLUDE_EXTS = {
    '.aux', '.log', '.out', '.toc',
    '.synctex.gz', '.synctex',
    '.bbl', '.blg', '.fdb_latexmk', '.fls',
    '.pyc', '.pyo', '.pyd',
    '.bak', '.tmp', '.swp',
    '.ds_store',
}
EXCLUDE_EXACT = {'nul', 'Thumbs.db', 'desktop.ini', '.DS_Store'}

# 排除根目录的测试/调试文件
EXCLUDE_ROOT_FILES = {
    '测试报告.md',     # 本工作区测试产物
    'pack_skill.py',   # 打包脚本本身
}


def should_skip(path: Path, skip_fonts: bool = False) -> bool:
    parts = {p for p in path.parts}
    if parts & EXCLUDE_DIRS:
        return True
    if skip_fonts and 'fonts' in parts:
        return True
    if path.name in EXCLUDE_EXACT:
        return True
    # 根目录的测试/调试文件
    if path.parent == ROOT and path.name in EXCLUDE_ROOT_FILES:
        return True
    if path.is_file():
        name_lower = path.name.lower()
        for ext in EXCLUDE_EXTS:
            if name_lower.endswith(ext):
                return True
    return False


def collect_files(skip_fonts: bool):
    files = []
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and not should_skip(path, skip_fonts=skip_fonts):
            files.append(path.relative_to(ROOT.parent))
    return files


def make_zip(out_path: Path, files, label: str):
    if out_path.exists():
        out_path.unlink()
    total_bytes = sum((ROOT.parent / f).stat().st_size for f in files)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in files:
            zf.write(ROOT.parent / rel, arcname=str(rel).replace(os.sep, '/'))
    out_size = out_path.stat().st_size
    print(f'[{label}] {out_path.name}')
    print(f'  文件数: {len(files)}')
    print(f'  原始:   {total_bytes/1024/1024:.2f} MB')
    print(f'  压缩:   {out_size/1024/1024:.2f} MB')
    if total_bytes:
        print(f'  压缩率: {out_size/total_bytes*100:.1f}%')

    # 验证
    with zipfile.ZipFile(out_path) as zf:
        bad = [n for n in zf.namelist() if any(n.lower().endswith(e)
               for e in ('.aux', '.log', '.out', '.toc', '.pyc'))]
        git = [n for n in zf.namelist() if '/.git/' in n or n.endswith('/.git')]
        print(f'  验证:   中间产物={len(bad)} .git={len(git)} (都应为 0)')
    print()
    return out_size


# 打两个版本
print('=' * 60)
print('完整包 (含 fonts/ 思源宋体) — 适合自留 / 跨机器交付')
print('=' * 60)
files_full = collect_files(skip_fonts=False)
size_full = make_zip(OUT_BASE / 'li-mtrie-2026-完整包.zip', files_full, 'FULL')

print('=' * 60)
print('轻量包 (不含 fonts/) — 适合分享 / 上传 / 备份源码')
print('  (编译时需自己装思源宋体, 或改 format.cls 用系统字体)')
print('=' * 60)
files_lite = collect_files(skip_fonts=True)
size_lite = make_zip(OUT_BASE / 'li-mtrie-2026-轻量包.zip', files_lite, 'LITE')

print('=' * 60)
print(f'总产出: 2 个 zip')
print(f'  完整包: {size_full/1024/1024:.2f} MB')
print(f'  轻量包: {size_lite/1024/1024:.2f} MB')
print(f'  合计:   {(size_full+size_lite)/1024/1024:.2f} MB')
