"""删中间产物 + 重新编译 AI工具使用详情 (electronic 模式)"""
import os
import subprocess

ROOT = r"C:\Users\admin\.minimax\skills\li-mtrie（2026）\论文"
os.chdir(ROOT)

# 删中间产物 + 旧 PDF
for ext in [".aux", ".log", ".out", ".toc", ".synctex.gz", ".pdf"]:
    p = f"AI工具使用详情{ext}"
    if os.path.exists(p):
        os.remove(p)
        print(f"删 {p}")

# 编译 2 次
xelatex = r"D:\MiKTeX\miktex\bin\x64\xelatex.exe"
for i in range(2):
    p = subprocess.Popen(
        [xelatex, "-interaction=nonstopmode", "AI工具使用详情.tex"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    p.wait()
    print(f"编译 {i+1}: exit code {p.returncode}")

# 验证
import fitz
doc = fitz.open("AI工具使用详情.pdf")
print(f"\n总页数: {doc.page_count}")
for i in range(min(3, doc.page_count)):
    text = doc[i].get_text()[:300].replace(chr(10), " | ")
    print(f"页 {i+1}: {text}")

# 自删
print(f"\n自删 {os.path.basename(__file__)}")
os.remove(__file__)
