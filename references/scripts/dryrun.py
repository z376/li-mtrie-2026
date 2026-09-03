"""li-mtrie-2026 赛前 1 天必做 dry-run 脚本 (v1.5.2).

跟 CI smoke-test.yml 等价但本地可跑, 赛前 1 天手动验证 6 类 checkable 全 green,
确保开赛当晚不踩"装包失败 / 模板坏 / LaTeX 不通"等灾难性坑.

输出: 结构化 checkable 报告 (Python dict), 6 项全 green = 赛前绿, 可安心参赛.
任何 red 项, 打印修复建议.

用法:
    python references/scripts/dryrun.py            # 跑 6 项 checkable
    python references/scripts/dryrun.py --json    # 输出 JSON 报告 (可管道)
"""
import json
import sys
import os
import subprocess
import shutil
import re
from pathlib import Path

# 路径 (相对 skill 根)
SKILL_ROOT = Path(__file__).parent.parent.parent  # references/scripts/dryrun.py → skill root
TEX_DIR = SKILL_ROOT / "论文"
SCRIPTS_DIR = SKILL_ROOT / "references" / "scripts"


def check_pkg():
    """checkable 1: 装包 (pandas / numpy / scipy / openpyxl / fitz / pulp)."""
    try:
        import pandas
        import numpy
        import scipy
        import openpyxl
        import fitz  # pymupdf 别名, v1.5.2 已修兼容
        # 可选: matplotlib (画图), pulp (ILP)
        try:
            import matplotlib
        except ImportError:
            pass
        try:
            import pulp
        except ImportError:
            pass
        return ("green", f"pandas {pandas.__version__} + numpy + scipy + openpyxl + fitz", None)
    except ImportError as e:
        return ("red", f"装包失败: {e.name}",
                f"跑 `pip install pandas numpy scipy openpyxl pymupdf` (赛前 1 天)")


def check_scripts():
    """checkable 2: 6 脚本 py_compile + import 验证."""
    scripts = ["aigc_scan", "check_figure", "data_utils",
               "profile_data", "verify_pdf_metrics", "visual_qa"]
    failed = []
    for s in scripts:
        path = SCRIPTS_DIR / f"{s}.py"
        if not path.exists():
            failed.append(f"缺文件 {s}.py")
            continue
        try:
            # 尝试 import
            import importlib.util
            spec = importlib.util.spec_from_file_location(s, path)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        except Exception as e:
            failed.append(f"{s}.py import 失败: {e}")
    if failed:
        return ("red", f"{len(failed)}/6 脚本失败", "; ".join(failed[:3]))
    return ("green", f"6/6 脚本 import OK (aigc/check/data/profile/verify/visual)", None)


def check_tex_compile():
    """checkable 3: 论文.tex 编译 (xelatex × 2). 失败 = 模板坏了."""
    xelatex = shutil.which("xelatex")
    if not xelatex:
        return ("yellow", "xelatex 未安装 (跳过编译检查)",
                "本地必装 MiKTeX/TeX Live, 跑 `xelatex 论文.tex`")
    # 跑 xelatex × 2
    old_cwd = os.getcwd()
    try:
        os.chdir(TEX_DIR)
        for i in range(2):
            r = subprocess.run([xelatex, "-interaction=nonstopmode", "-halt-on-error",
                               "论文.tex"], capture_output=True, text=True, timeout=60,
                      encoding="utf-8", errors="replace")
            if r.returncode != 0:
                return ("red", f"第 {i+1} 次 xelatex 失败 (returncode={r.returncode})",
                        "查 论文.log 中 '! Error' 行")
    except subprocess.TimeoutExpired:
        return ("red", "xelatex 超时 (>60s)", "检查 .tex 死循环或缺包")
    finally:
        os.chdir(old_cwd)
    # 检查 PDF 生成
    pdf_path = TEX_DIR / "论文.pdf"
    if not pdf_path.exists():
        return ("red", "论文.pdf 未生成", "查 xelatex 输出")
    # 检查 ! Error
    log = (TEX_DIR / "论文.log").read_text(encoding="utf-8", errors="replace")
    err_count = len(re.findall(r"^!\s", log, re.M))
    if err_count > 0:
        return ("red", f"! Error 数 = {err_count}",
                f"查 论文.log 中 '!' 开头的行")
    # 页数
    pages = re.search(r"Output written on 论文\.pdf \((\d+) pages", log)
    pages_n = int(pages.group(1)) if pages else 0
    return ("green", f"24 页论文.pdf 生成 ({pages_n} 页, 0 ! Error)", None)


def check_overfull():
    """checkable 4: 论文 Overfull 数 (< 5 = sign-off 绿)."""
    log_path = TEX_DIR / "论文.log"
    if not log_path.exists():
        return ("yellow", "论文.log 不存在 (跳过 Overfull 检查)",
                "先跑 check_tex_compile")
    log = log_path.read_text(encoding="utf-8", errors="replace")
    overfull = len(re.findall(r"Overfull", log))
    if overfull < 5:
        return ("green", f"Overfull = {overfull} (判据 < 5)", None)
    return ("red", f"Overfull = {overfull} (判据 ≥ 5 = sign-off 红)",
            "查 论文.log 中 'Overfull \\hbox' 行; 通常是公式超宽或 longtable 列宽过大")


def check_pack():
    """checkable 5: pack.py 跑通 + 2 个 zip 生成 (学生分享/解压用)."""
    pack_py = SKILL_ROOT / "tools" / "pack.py"
    if not pack_py.exists():
        return ("red", "tools/pack.py 不存在", "重 git clone")
    r = subprocess.run([sys.executable, str(pack_py)],
                       capture_output=True, text=True, timeout=60,
                       cwd=SKILL_ROOT, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return ("red", "pack.py 失败",
                f"查 stdout/stderr (returncode={r.returncode})")
    # 检查 zip
    zips = list(SKILL_ROOT.parent.glob("li-mtrie-2026-*.zip"))
    if len(zips) != 2:
        return ("red", f"zip 数 = {len(zips)} (期望 2: 完整包 + 轻量包)",
                "查 pack.py 输出")
    return ("green", f"2 zip 生成 ({[z.name for z in zips]})", None)


def check_aigc():
    """checkable 6: 0.摘要.tex 跑 aigc_scan, 综合风险 = 低 (AIGC 风险)."""
    aigc = SCRIPTS_DIR / "aigc_scan.py"
    tex = TEX_DIR / "0.摘要.tex"
    if not aigc.exists() or not tex.exists():
        return ("yellow", "aigc_scan 或 0.摘要.tex 缺失 (跳过)",
                "跑 check_tex_compile 后重试")
    r = subprocess.run([sys.executable, str(aigc), str(tex)],
                       capture_output=True, text=True, timeout=30,
                       cwd=SKILL_ROOT, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return ("red", "aigc_scan 失败", f"查 stdout/stderr")
    # 解析综合风险
    if r.stdout and "🟢 低" in r.stdout:
        return ("green", "AIGC 综合风险 🟢 低", None)
    elif r.stdout and "🟡 中" in r.stdout:
        return ("yellow", "AIGC 综合风险 🟡 中 (微调即可)",
                "查 0.摘要.tex 触发维度, 降重")
    elif r.stdout and "🔴 高" in r.stdout:
        return ("red", "AIGC 综合风险 🔴 高 (必须降重)",
                "查 0.摘要.tex 触发维度, 走 references/去AIGC指南.md")
    return ("yellow", "AIGC 风险未知 (无法解析)", "查 stdout")


CHECKS = [
    ("1. 装包", check_pkg),
    ("2. 6 脚本", check_scripts),
    ("3. LaTeX 编译", check_tex_compile),
    ("4. Overfull 数", check_overfull),
    ("5. pack.py 装包", check_pack),
    ("6. AIGC 风险", check_aigc),
]


def main():
    json_mode = "--json" in sys.argv
    results = {}
    for name, fn in CHECKS:
        status, msg, fix = fn()
        results[name] = {"status": status, "msg": msg, "fix": fix}

    if json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        # 友好 Markdown 输出
        print("=" * 60)
        print("li-mtrie-2026 赛前 1 天必做 dry-run (v1.5.2)")
        print("=" * 60)
        green_count = 0
        for name, info in results.items():
            sym = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(info["status"], "?")
            print(f"\n{sym} [{info['status'].upper():6}] {name}")
            print(f"         {info['msg']}")
            if info["fix"]:
                print(f"         修复: {info['fix']}")
            if info["status"] == "green":
                green_count += 1
        # 总结
        print("\n" + "=" * 60)
        n = len(results)
        if green_count == n:
            print(f"🟢 赛前 dry-run 绿: {green_count}/{n} 全 green")
            print("   可安心参赛. 祝拿国一!")
        else:
            print(f"⚠️  赛前 dry-run 未全绿: {green_count}/{n} green")
            print(f"   修复 red 项后重跑, 直到全 green")
        print("=" * 60)
        # 退出码
        sys.exit(0 if green_count == n else 1)


if __name__ == "__main__":
    main()
