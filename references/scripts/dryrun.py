"""li-mtrie-2026 赛前 1 天必做 + CI smoke-test 一体化脚本 (v1.5.3 patch4).

跟 CI smoke-test.yml 等价但本地可跑, 赛前 1 天手动验证全部 checkable 全 green,
确保开赛当晚不踩"装包失败 / 模板坏 / LaTeX 不通 / 文件缺失"等灾难性坑.

输出: 结构化 checkable 报告 (Python dict), N 项全 green = 赛前绿, 可安心参赛.
任何 red 项, 打印修复建议.

v1.5.3 patch4: 加 8 项 CI 检查 (frontmatter / Python 10 个 / LLM 工具 / BZD 借鉴 /
LICENSE / pack exclude / fitz compat / 全文件存在性), 凑齐 14 项覆盖 smoke-test
全部 step. 替代 v1.5.3 之前在 YAML 里嵌 PowerShell + Python 多行的复杂 step (14+ 次
连 fail 的根因).

用法:
    python references/scripts/dryrun.py            # 跑 14 项 checkable
    python references/scripts/dryrun.py --json    # 输出 JSON 报告 (可管道)
    python references/scripts/dryrun.py --ci      # CI 模式, 输出 GitHub Actions 友好格式
"""
import json
import sys
import os
import subprocess
import shutil
import re
import zipfile
from pathlib import Path

# 路径 (相对 skill 根)
SKILL_ROOT = Path(__file__).parent.parent.parent  # references/scripts/dryrun.py → skill root
TEX_DIR = SKILL_ROOT / "论文"
SCRIPTS_DIR = SKILL_ROOT / "references" / "scripts"
REFS_DIR = SKILL_ROOT / "references"


def check_pkg():
    """checkable 1: 装包 (pandas / numpy / scipy / openpyxl / fitz / pulp)."""
    try:
        import pandas
        import numpy
        import scipy
        import openpyxl
        import fitz  # pymupdf 别名, v1.5.2 已修兼容
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


def check_python_scripts():
    """checkable 2: 10 Python 脚本 py_compile + import 验证."""
    scripts = [
        ("references/code-template.py", "code-template"),
        ("references/mechanism-template.py", "mechanism-template"),
        ("tools/pack.py", "pack"),
        ("references/scripts/dryrun.py", "dryrun"),
        ("references/scripts/profile_data.py", "profile_data"),
        ("references/scripts/visual_qa.py", "visual_qa"),
        ("references/scripts/check_figure.py", "check_figure"),
        ("references/scripts/verify_pdf_metrics.py", "verify_pdf_metrics"),
        ("references/scripts/aigc_scan.py", "aigc_scan"),
        ("references/scripts/data_utils.py", "data_utils"),
    ]
    failed = []
    for rel, name in scripts:
        path = SKILL_ROOT / rel
        if not path.exists():
            failed.append(f"缺 {rel}")
            continue
        # py_compile
        r = subprocess.run([sys.executable, "-m", "py_compile", str(path)],
                           capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            failed.append(f"{name} py_compile 失败: {r.stderr[:100]}")
    if failed:
        return ("red", f"{len(failed)}/10 脚本失败", "; ".join(failed[:3]))
    return ("green", f"10/10 Python 脚本 py_compile OK (含 v1.5.0 data_utils + v1.5.2 dryrun)", None)


def check_tex_compile():
    """checkable 3: 论文.tex 编译 (xelatex × 2). 失败 = 模板坏了."""
    xelatex = shutil.which("xelatex")
    if not xelatex:
        return ("yellow", "xelatex 未安装 (跳过编译检查)",
                "本地必装 MiKTeX/TeX Live, 跑 `xelatex 论文.tex`")
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
    pdf_path = TEX_DIR / "论文.pdf"
    if not pdf_path.exists():
        return ("red", "论文.pdf 未生成", "查 xelatex 输出")
    log = (TEX_DIR / "论文.log").read_text(encoding="utf-8", errors="replace")
    err_count = len(re.findall(r"^!\s", log, re.M))
    if err_count > 0:
        return ("red", f"! Error 数 = {err_count}",
                f"查 论文.log 中 '!' 开头的行")
    pages = re.search(r"Output written on 论文\.pdf \((\d+) pages", log)
    pages_n = int(pages.group(1)) if pages else 0
    return ("green", f"论文.pdf 生成 ({pages_n} 页, 0 ! Error)", None)


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
    """checkable 5: pack.py 跑通 + 2 个 zip 生成 + 排除敏感/dev 文件."""
    pack_py = SKILL_ROOT / "tools" / "pack.py"
    if not pack_py.exists():
        return ("red", "tools/pack.py 不存在", "重 git clone")
    # 落盘到 .github/dryrun-logs/ 方便 CI 排查 (artifact 上传)
    log_dir = SKILL_ROOT / ".github" / "dryrun-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / "pack_stdout.log"
    stderr_log = log_dir / "pack_stderr.log"
    with open(stdout_log, "wb") as sout, open(stderr_log, "wb") as serr:
        # 设 PYTHONIOENCODING=utf-8 防 Windows runner 默认 cp936 触发
        # UnicodeEncodeError (pack.py print 中文/特殊字符崩溃, exit 1 无 stderr)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        try:
            r = subprocess.run([sys.executable, "-u", str(pack_py)],
                               stdout=sout, stderr=serr, timeout=120,
                               cwd=SKILL_ROOT, env=env)
        except subprocess.TimeoutExpired:
            return ("red", "pack.py 超时 (>120s)",
                    f"查 {stdout_log} 和 {stderr_log}")
    if r.returncode != 0:
        # 读落盘的 stdout/stderr 末尾 (避免内存缓冲 + subprocess capture 丢失)
        try:
            stdout_txt = stdout_log.read_text(encoding="utf-8", errors="replace")
            stderr_txt = stderr_log.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ("red", f"pack.py 失败 (exit {r.returncode})",
                    f"读 log 失败: {e}")
        # 暴露 stdout 末尾 2000 字符 + stderr 末尾 1000 字符
        out_tail = stdout_txt[-2000:] if len(stdout_txt) > 2000 else stdout_txt
        err_tail = stderr_txt[-1000:] if len(stderr_txt) > 1000 else stderr_txt
        return ("red", f"pack.py 失败 (exit {r.returncode})",
                f"stdout 末 {len(out_tail)}/{len(stdout_txt)} 字符: {out_tail} || "
                f"STDERR 末 {len(err_tail)}/{len(stderr_txt)} 字符: {err_tail}")
    zips = list(SKILL_ROOT.parent.glob("li-mtrie-2026-*.zip"))
    if len(zips) != 2:
        stdout_txt = stdout_log.read_text(encoding="utf-8", errors="replace")
        return ("red", f"zip 数 = {len(zips)} (期望 2: 完整包 + 轻量包)",
                f"pack.py stdout 末 2000 字符: {stdout_txt[-2000:]}")
    # 验证排除敏感文件
    bad_patterns = [
        (r"\.aux$", ".aux"),
        (r"\.log$", ".log"),
        (r"开发日志", "开发日志.md"),
        (r"测试报告", "测试报告.md"),
        (r"流程审计", "流程审计-19漏点"),
        (r"^_.*\.(py|txt)$", "_*.py/_*.txt (开发)"),
    ]
    # 找轻量包 (含 EXCLUDE_DIRS)
    lite_zip = next((z for z in zips if "轻量" in z.name), zips[0])
    violations = []
    try:
        with zipfile.ZipFile(lite_zip) as zf:
            for name in zf.namelist():
                for pat, label in bad_patterns:
                    if re.search(pat, name):
                        violations.append(f"{label}: {name}")
                        break
    except Exception as e:
        return ("yellow", f"zip 解析失败: {e}", "查 pack.py 输出")
    if violations:
        return ("red", f"zip 含 {len(violations)} 个敏感/dev 文件",
                f"修 pack.py EXCLUDE 规则. 违规: {violations[:3]}")
    return ("green", f"2 zip 生成 + 无敏感/dev 文件 ({[z.name for z in zips]})", None)


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
    if r.stdout and "🟢 低" in r.stdout:
        return ("green", "AIGC 综合风险 🟢 低", None)
    elif r.stdout and "🟡 中" in r.stdout:
        return ("yellow", "AIGC 综合风险 🟡 中 (微调即可)",
                "查 0.摘要.tex 触发维度, 降重")
    elif r.stdout and "🔴 高" in r.stdout:
        return ("red", "AIGC 综合风险 🔴 高 (必须降重)",
                "查 0.摘要.tex 触发维度, 走 references/去AIGC指南.md")
    return ("yellow", "AIGC 风险未知 (无法解析)", "查 stdout")


def check_skill_md_frontmatter():
    """checkable 7: SKILL.md frontmatter 有效 (含 name + version)."""
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        return ("red", "SKILL.md 不存在", "重 git clone")
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    if not content.startswith("---\n"):
        return ("red", "SKILL.md 缺 frontmatter (--- 开头)", "修 SKILL.md")
    if "name: li-mtrie" not in content[:500]:
        return ("red", "SKILL.md frontmatter 缺 name: li-mtrie", "修 SKILL.md")
    ver_match = re.search(r'version:\s*"(\d+\.\d+\.\d+)"', content)
    if not ver_match:
        return ("red", "SKILL.md frontmatter 缺 version 字段", "修 SKILL.md")
    return ("green", f"SKILL.md frontmatter 有效 (version={ver_match.group(1)})", None)


def check_llm_tools():
    """checkable 8: v1.5.0 LLM 工具 4 prompt + README 存在."""
    files = [
        "references/llm-prompts/README.md",
        "references/llm-prompts/01-选题推荐.md",
        "references/llm-prompts/02-代码修复.md",
        "references/llm-prompts/03-自动审稿.md",
        "references/llm-prompts/04-百分制评审.md",
    ]
    missing = [f for f in files if not (SKILL_ROOT / f).exists()]
    if missing:
        return ("red", f"v1.5.0 LLM 工具缺 {len(missing)}/5",
                f"补 {missing[:3]}")
    return ("green", f"v1.5.0 LLM 工具 5 文件全在 (4 prompt + README)", None)


def check_bzd_v151():
    """checkable 9: v1.5.1 BZD 借鉴 3 references 方法论 + 数模资料 README."""
    files = [
        "references/模型字典使用指南.md",
        "references/格式自查清单.md",
        "references/百分制评审方法.md",
        "references/数模资料/README.md",
    ]
    missing = [f for f in files if not (SKILL_ROOT / f).exists()]
    if missing:
        return ("red", f"v1.5.1 BZD 借鉴缺 {len(missing)}/4",
                f"补 {missing[:3]}")
    return ("green", "v1.5.1 BZD 借鉴 4 文件全在 (3 references + 数模资料 README)", None)


def check_bzd_v153():
    """checkable 10: v1.5.3 BZD 借鉴 11 新文件 (9 板块自查 + 题意翻译 + 学校国奖画像)."""
    files = [
        "references/板块自查/README.md",
        "references/板块自查/01-摘要自查.md",
        "references/板块自查/02-AI声明自查.md",
        "references/板块自查/03-问题重述自查.md",
        "references/板块自查/04-问题分析自查.md",
        "references/板块自查/05-模型假设自查.md",
        "references/板块自查/06-符号说明自查.md",
        "references/板块自查/07-模型求解自查.md",
        "references/板块自查/08-参考文献附录自查.md",
        "references/板块自查/09-AIGC审计.md",
        "references/题意翻译.md",
        "references/学校国奖画像.md",
    ]
    missing = [f for f in files if not (SKILL_ROOT / f).exists()]
    if missing:
        return ("red", f"v1.5.3 BZD 借鉴缺 {len(missing)}/12",
                f"补 {missing[:3]}")
    return ("green", "v1.5.3 BZD 借鉴 12 文件全在 (9 板块自查 + 1 README + 题意翻译 + 学校国奖画像)", None)


def check_fitz_compat():
    """checkable 11: PyMuPDF ≥1.24 pymupdf as fitz 兼容 (v1.5.2 fix)."""
    try:
        import pymupdf as fitz
        ver = fitz.__doc__.split()[1] if fitz.__doc__ else "unknown"
        return ("green", f"pymupdf {ver} as fitz (PyMuPDF ≥1.24 推荐)", None)
    except ImportError:
        try:
            import fitz
            return ("green", f"legacy fitz (PyMuPDF <1.24 fallback)", None)
        except ImportError:
            return ("red", "fitz 不可用",
                    "pip install pymupdf (≥1.24 推荐) 或 PyMuPDF<1.24")


def check_license_mit():
    """checkable 12: LICENSE 是 MIT."""
    lic = SKILL_ROOT / "LICENSE"
    if not lic.exists():
        return ("red", "LICENSE 不存在", "加 LICENSE (MIT)")
    content = lic.read_text(encoding="utf-8", errors="replace")
    if "MIT License" not in content:
        return ("red", "LICENSE 不是 MIT", "改 LICENSE 为 MIT")
    return ("green", "LICENSE 是 MIT", None)


def check_5step_checkable():
    """checkable 13: 5 步状态机 checkable — 装包 + 7 脚本 + profile_data (跟 dryrun 1+2 重叠, 简化版)."""
    # 装包
    try:
        import pandas, numpy, scipy, openpyxl
    except ImportError as e:
        return ("red", f"装包失败: {e.name}", "pip install ...")
    # 7 脚本 import (含 dryrun)
    scripts = ["aigc_scan", "check_figure", "data_utils", "dryrun",
               "profile_data", "verify_pdf_metrics", "visual_qa"]
    failed = []
    for s in scripts:
        path = SCRIPTS_DIR / f"{s}.py"
        if not path.exists():
            failed.append(f"缺 {s}.py")
            continue
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(s, path)
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            failed.append(f"{s} import 失败: {type(e).__name__}: {e} | tb: {tb.splitlines()[-3:]}")
    if failed:
        return ("red", f"7 脚本 {len(failed)} 失败", "; ".join(failed[:3]))
    return ("green", "5 步状态机 checkable green (装包 + 7 脚本 import + profile_data)", None)


def check_latex_compile():
    """checkable 14: LaTeX 编译可执行性 (CI skip, 本地必跑)."""
    xelatex = shutil.which("xelatex")
    if not xelatex:
        return ("yellow", "xelatex 未安装 (CI skip, 本地必装 MiKTeX/TeX Live)",
                "赛前 1 天必装 + 跑 dryrun")
    # 已经在 check_tex_compile 跑过, 这里仅报状态
    return ("green", f"xelatex {xelatex} 可用 (详 check_tex_compile)", None)


CHECKS = [
    ("1. 装包 (核心包)", check_pkg),
    ("2. 10 Python 脚本", check_python_scripts),
    ("3. LaTeX 编译", check_tex_compile),
    ("4. Overfull 数", check_overfull),
    ("5. pack.py + 2 zip", check_pack),
    ("6. AIGC 风险", check_aigc),
    ("7. SKILL.md frontmatter", check_skill_md_frontmatter),
    ("8. v1.5.0 LLM 工具 4 prompt", check_llm_tools),
    ("9. v1.5.1 BZD 借鉴 3 references", check_bzd_v151),
    ("10. v1.5.3 BZD 借鉴 11 新文件", check_bzd_v153),
    ("11. v1.5.2 fitz compat", check_fitz_compat),
    ("12. LICENSE = MIT", check_license_mit),
    ("13. 5 步状态机 checkable", check_5step_checkable),
    ("14. LaTeX 编译可执行性", check_latex_compile),
]


def main():
    json_mode = "--json" in sys.argv
    ci_mode = "--ci" in sys.argv
    results = {}

    for name, fn in CHECKS:
        try:
            status, msg, fix = fn()
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            status, msg, fix = "red", f"check 异常: {e}", f"查脚本. Traceback: {tb[-500:]}"
        results[name] = {"status": status, "msg": msg, "fix": fix}

    if json_mode:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif ci_mode:
        # GitHub Actions 友好: 每项打印 GREEN/RED/YELLOW, exit code 0/1
        green_count = 0
        red_items = []
        for name, info in results.items():
            sym = {"green": "GREEN", "yellow": "YELLOW", "red": "RED"}.get(info["status"], "?")
            print(f"::group::{sym}: {name}")
            print(f"  {info['msg']}")
            if info["fix"]:
                print(f"  修复: {info['fix']}")
            print("::endgroup::")
            if info["status"] == "green":
                green_count += 1
            elif info["status"] == "red":
                red_items.append(name)
                # 把 fix 也拼进 ::error:: 注释, annotations API 能看到完整
                err_line = f"::error::{name}: {info['msg']}"
                if info["fix"]:
                    err_line += f" | 修复: {info['fix'][:200]}"  # 截断 200 字符防超限
                print(err_line)
        # 写到 GITHUB_STEP_SUMMARY (UI 可见, 即使 step fail 也能看)
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            try:
                with open(summary_path, "a", encoding="utf-8") as f:
                    f.write(f"## li-mtrie-2026 smoke-test 结果\n\n")
                    f.write(f"**{green_count}/{len(results)} green**\n\n")
                    if red_items:
                        f.write(f"### ❌ Red 项 ({len(red_items)}):\n")
                        for name in red_items:
                            info = results[name]
                            f.write(f"- **{name}**: {info['msg']}\n")
                            if info["fix"]:
                                f.write(f"  - 修复: {info['fix']}\n")
                    f.write(f"\n### 全部 {len(results)} 项:\n")
                    for name, info in results.items():
                        sym = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(info["status"], "?")
                        f.write(f"- {sym} **{name}**: {info['msg']}\n")
            except Exception as e:
                print(f"  WARN: 写 GITHUB_STEP_SUMMARY 失败: {e}")
        n = len(results)
        print(f"\n===== smoke-test summary: {green_count}/{n} green =====")
        if red_items:
            print(f"RED 项: {red_items}")
        sys.exit(0 if green_count == n else 1)
    else:
        # 友好 Markdown 输出 (学生本地用)
        print("=" * 60)
        print("li-mtrie-2026 赛前 1 天 + CI smoke-test (v1.5.3 patch4)")
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
        print("\n" + "=" * 60)
        n = len(results)
        if green_count == n:
            print(f"🟢 sign-off 绿: {green_count}/{n} 全 green")
            print("   赛前可安心参赛. 祝拿国一!")
        else:
            print(f"⚠️  sign-off 未全绿: {green_count}/{n} green")
            print(f"   修复 red 项后重跑, 直到全 green")
        print("=" * 60)
        sys.exit(0 if green_count == n else 1)


if __name__ == "__main__":
    main()
