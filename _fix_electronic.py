"""改 bwprint -> electronic, 删除中间产物, 重新编译"""
import os
import subprocess

ROOT = r"C:\Users\admin\.minimax\skills\li-mtrie（2026）\论文"
os.chdir(ROOT)

# 1. 改 .tex
tex_path = "AI工具使用详情.tex"
with open(tex_path, encoding="utf-8") as f:
    content = f.read()

# 替换 documentclass 行
old = r"\documentclass[bwprint]{format}   % 跟论文/电子版共享 format.cls"
new = r"\documentclass[electronic]{format}   % electronic 模式: 不含承诺书+编号页 (那 2 个只能出现在论文.pdf)"
content = content.replace(old, new)

with open(tex_path, "w", encoding="utf-8") as f:
    f.write(content)
print("改 bwprint -> electronic OK")

# 2. 删中间产物
for ext in [".aux", ".log", ".out", ".toc", ".synctex.gz"]:
    p = f"AI工具使用详情{ext}"
    if os.path.exists(p):
        os.remove(p)
        print(f"删 {p}")

# 3. 编译 2 次
xelatex = r"D:\MiKTeX\miktex\bin\x64\xelatex.exe"
for i in range(2):
    result = subprocess.run(
        [xelatex, "-interaction=nonstopmode", "AI工具使用详情.tex"],
        capture_output=True, text=True
    )
    out = (result.stdout + result.stderr)
    err = [l for l in out.splitlines() if "Error" in l and "warning" not in l.lower()]
    print(f"  编译 {i+1}: {'OK' if not err else 'ERR'} ({[e[:80] for e in err[:2]]})")

# 4. 验证 PDF
import fitz
doc = fitz.open("AI工具使用详情.pdf")
print(f"\n总页数: {doc.page_count}")
for i in range(min(2, doc.page_count)):
    text = doc[i].get_text()[:200].replace(chr(10), " / ")
    print(f"页 {i+1}: {text}")

# 5. 自删
print(f"\n自删 {os.path.basename(__file__)}")
os.remove(__file__)
