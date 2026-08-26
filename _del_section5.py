"""删 AI 工具使用详情.tex §五 风险声明与禁用场景 整段"""
import os

ROOT = r"C:\Users\admin\.minimax\skills\li-mtrie（2026）\论文"
os.chdir(ROOT)

p = "AI工具使用详情.tex"
with open(p, encoding="utf-8") as f:
    lines = f.readlines()

# 找 §五 起点
start = None
end = None
for i, line in enumerate(lines):
    if r"\section{风险声明与禁用场景}" in line:
        start = i
    elif start is not None and r"\vspace{2em}" in line:
        end = i  # 保留 \vspace 作为分隔
        break

if start is None or end is None:
    print(f"未找到: start={start}, end={end}")
else:
    print(f"删 lines {start+1}-{end}: {lines[start].strip()} ... {lines[end-1].strip()}")
    new = lines[:start] + lines[end:]
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(new)
    print(f"原 {len(lines)} 行 → 新 {len(new)} 行")

# 重编 PDF
for ext in [".aux", ".log", ".out", ".toc", ".synctex.gz", ".pdf"]:
    f2 = f"AI工具使用详情{ext}"
    if os.path.exists(f2):
        os.remove(f2)

import subprocess
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
for i in range(min(2, doc.page_count)):
    text = doc[i].get_text()[:300]
    with open(f"_p{i+1}.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print(f"页 {i+1}: 写 _p{i+1}.txt")

# 自删
os.remove(__file__)
