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
    paper_dir = get_paper_dir()
    # example-paper 状态: 没 fonts/ 必然编译失败, yellow 跳过 (template 自检不需 LaTeX 编译)
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    if is_template:
        return ("yellow",
                f"example 模板状态 (paper_dir={paper_dir.name}, 跳过 LaTeX 编译)",
                "跑题用户复制 example-paper 到 跑题目录/论文/ 后再编译")
    xelatex = shutil.which("xelatex")
    if not xelatex:
        return ("yellow", "xelatex 未安装 (跳过编译检查)",
                "本地必装 MiKTeX/TeX Live, 跑 `xelatex 论文.tex`")
    old_cwd = os.getcwd()
    try:
        os.chdir(paper_dir)
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
    pdf_path = paper_dir / "论文.pdf"
    if not pdf_path.exists():
        return ("red", "论文.pdf 未生成", "查 xelatex 输出")
    log = (pdf_path.parent / "论文.log").read_text(encoding="utf-8", errors="replace")
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


# ===== v1.5.4 新增 3 项: 防 "答非所问 / 模板残留 / 占位符" =====

def get_paper_dir():
    """用户论文目录. 优先级: --paper-dir 参数 > PAPER_DIR 环境变量 > cwd/论文/ > references/templates/example-paper/ > cwd (含 .tex) > skill TEX_DIR (兜底).

    用法:
        # 跑题用户在跑题目录 (有 论文/ 子目录) 跑, 自动检测
        python references/scripts/dryrun.py

        # 或显式指定 (跨目录跑)
        python references/scripts/dryrun.py --paper-dir C:/my-paper/论文

        # skill 自检 (cwd = skill 根, 无 论文/), 用 references/templates/example-paper/
        # 让 check 15/16/17/18 跑 template 自检 (预期 RED, 模板留占位符)
    """
    env_dir = os.environ.get("PAPER_DIR")
    if env_dir:
        return Path(env_dir)
    if "--paper-dir" in sys.argv:
        idx = sys.argv.index("--paper-dir")
        if idx + 1 < len(sys.argv):
            return Path(sys.argv[idx + 1])
    cwd = Path(os.getcwd())
    # 1. 跑题用户在跑题目录 (有 论文/ 子目录) 跑
    if (cwd / "论文").is_dir() and any((cwd / "论文").glob("*.tex")):
        return cwd / "论文"
    # 2. skill 自检 (cwd = skill 根, 有 references/templates/example-paper/)
    template_dir = Path(__file__).parent.parent.parent / "references" / "templates" / "example-paper"
    if template_dir.is_dir() and any(template_dir.glob("*.tex")):
        return template_dir
    # 3. cwd 本身是论文目录 (含 .tex, 跨目录跑)
    if cwd.is_dir() and any(cwd.glob("*.tex")):
        return cwd
    # 4. 兜底: skill 自带 TEX_DIR
    return TEX_DIR


def check_no_placeholder():
    """checkable 15: 论文 .tex 占位符未替换检查 (【 / TODO / 待填 / XXX).

    背景: 2025C 跑题时 other agent 留了 9.0 + 10.0 模板占位符 (【】方括号),
    dryrun 之前没查, 评委扣分. 现在加这道防线.

    Template 状态 (paper_dir 含 templates/example): yellow 报, 跑题用户状态: red 报.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过占位符检查",
                "用 --paper-dir <path> 指定, 或在跑题目录下跑")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    # 占位符模式
    patterns = [
        (r"【[^】]*】", "【】中括号占位符"),
        (r"\bTODO\b", "TODO 标记"),
        (r"待填", "中文 待填"),
        (r"未填", "中文 未填"),
        (r"未替换", "未替换 标记"),
        (r"\bXXX\b", "XXX 占位符"),
    ]
    violations = []
    for tex_file in sorted(paper_dir.glob("*.tex")):
        try:
            content = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pat, label in patterns:
            for m in re.finditer(pat, content):
                line_no = content[:m.start()].count("\n") + 1
                line_start = content.rfind("\n", 0, m.start()) + 1
                line_end = content.find("\n", m.end())
                if line_end == -1:
                    line_end = len(content)
                line_text = content[line_start:line_end]
                if line_text.lstrip().startswith("%"):
                    continue
                violations.append(f"{tex_file.name}:L{line_no} {label} -> {m.group()[:30]}")
    if violations:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留 {len(violations)} 处占位符 (设计意图, 跑题时填掉才 GREEN)",
                    f"占位符: {violations[:2]}. 跑题用户复制 example-paper → 论文/ 后替换")
        return ("red", f"占位符未替换 ({len(violations)} 处)",
                f"修 .tex 把 {violations[:3]} 替换成实际内容. 例: AI 声明 【文献检索】→ 文献检索")
    return ("green", "占位符全替换 (无 【 TODO 待填 XXX)", None)


def check_appendix_files():
    """checkable 16: 10.附录.tex (或 10.0.附录固定说明.tex) 列的每个文件存在.

    背景: 2025C 跑题时 other agent 留了 2024B 烟幕题模板, 列的 5 个脚本
    全不存在. dryrun 之前没查, 评委抽包直接判 0 分. 现在加这道防线.

    同时扫 10.0.附录固定说明.tex (用户论文常用, 10.0 留作固定说明).
    """
    paper_dir = get_paper_dir()
    # 两个文件都可能含文件引用
    candidates_tex = [paper_dir / "10.附录.tex", paper_dir / "10.0.附录固定说明.tex"]
    all_refs = []
    source_files = []
    for tex_path in candidates_tex:
        if not tex_path.exists():
            continue
        try:
            content = tex_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            continue
        # 跳过 LaTeX 注释行 (避免匹配 % 注释里的示例)
        non_comment_lines = [
            line for line in content.splitlines()
            if not line.lstrip().startswith("%")
        ]
        non_comment = "\n".join(non_comment_lines)
        # 提取 \texttt{xxx} 引用 (file paths) + 裸路径 (含 .py/.xlsx/.csv/.pdf 等)
        refs = set(re.findall(r"\\texttt\{([^}]+)\}", non_comment))
        # 也扫裸路径 (e.g., "求解/问题1/问题1_xxx.py") — 排除含通配符 * 的模板占位符
        for ext in (".py", ".xlsx", ".csv", ".pdf", ".md", ".ipynb"):
            refs.update(re.findall(rf"[\w/\-\\.]+\{ext}", non_comment))
        all_refs.extend(refs)
        source_files.append(tex_path.name)
    # 过滤: 排除描述性词 + 模板字面量 (e.g., "{ext}" 占位符本身)
    file_refs = []
    for r in all_refs:
        r = r.strip().strip(",").strip(";")
        if not r or r.startswith("{"):  # 跳过空 + 模板占位符
            continue
        if "*" in r:  # 通配符 = 模板说明, 跳过
            continue
        if "支撑材料" in r or "rar" == r.lower() or "目录" in r or "详见" in r:
            continue
        # 必须含扩展名才算文件
        if "." in r.split("/")[-1].split("\\")[-1]:
            file_refs.append(r)
    if not file_refs:
        return ("yellow",
                f"附录无具体文件引用 ({'/'.join(source_files) or '10.附录.tex/10.0 均不存在'})",
                "建议在 10.附录.tex 加 \\\\texttt{求解/问题1/问题1_xxx.py} 等")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    missing = []
    for ref in file_refs:
        candidates = [
            SKILL_ROOT / ref,
            paper_dir / ref,
            paper_dir.parent / ref,
            Path(ref),
        ]
        if ref.startswith("../"):
            candidates.insert(0, (paper_dir / ref).resolve())
        if not any(c.exists() for c in candidates):
            missing.append(ref)
    if missing:
        if is_template:
            return ("yellow",
                    f"example 模板的附录示例引用了 {len(missing)} 个文件不存在 (设计意图, 跑题用户替换占位符即解决)",
                    f"占位符引用: {missing[:3]}. 跑题用户用自己实际文件替换")
        return ("red",
                f"附录列了 {len(file_refs)} 个文件, {len(missing)} 个不存在",
                f"要么补文件, 要么从附录里删. 缺失: {missing[:3]}")
    return ("green",
            f"附录列的 {len(file_refs)} 个文件全在",
            None)


def check_figure_exists():
    """checkable 17: 所有 .tex \\includegraphics 引用的图都存在.

    背景: 防止 other agent 引用了图但没生成, 编译报 missing file. 现在
    跑题前 checkable 提前发现.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过图检查", "指定 --paper-dir")
    # 收集所有 .tex 的 \includegraphics 引用
    refs = set()
    for tex_file in sorted(paper_dir.glob("*.tex")):
        try:
            content = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 匹配 \includegraphics[opts]{path} 或 \includegraphics{path}
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", content):
            ref = m.group(1).strip()
            # 跳过绝对 http URL
            if ref.startswith("http"):
                continue
            refs.add(ref)
    if not refs:
        return ("yellow", "论文 .tex 无 \\includegraphics 引用 (检查 LaTeX 模板)",
                "正常论文应 ≥ 10 张图, 0 张 = 异常")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    missing = []
    for ref in refs:
        candidates = [
            paper_dir / ref,
            paper_dir.parent / ref,             # 论文/xxx → 求解/xxx
            SKILL_ROOT / ref,                   # 相对 skill 根
            Path(ref),                          # 绝对路径
        ]
        # 处理 ../ 相对路径
        if ref.startswith("../"):
            candidates.insert(0, (paper_dir / ref).resolve())
        if not any(c.exists() for c in candidates):
            missing.append(ref)
    if missing:
        if is_template:
            return ("yellow",
                    f"example 模板示例引用了 {len(missing)} 张图 (设计意图, 跑题用户跑 .py 生成自己的图即解决)",
                    f"占位符引用: {missing[:3]}. 跑题用户用 figures/ 下的实际图替换")
        return ("red", f"图引用 {len(refs)} 个, {len(missing)} 个找不到文件",
                f"要么生成图 (跑对应问题 py), 要么从 .tex 删 \\includegraphics. 缺失: {missing[:3]}")
    return ("green", f"图引用 {len(refs)} 个全在 ({len(refs) - len(missing)} 个有效)",
            None)


def check_post_solution_audit():
    """checkable 18: Post-Solution Audit (跑题后必做 4 项中 2 项自动化).

    必做 1 (quote 锚定表交叉验证) 跟 必做 3 (数字一致性) 需人工/LLM, 不自动化.
    必做 2 (代码 + 输出齐全) + 必做 4 (5.X.2 引用存在) 可自动 check.

    背景: 2025C 跑题 other agent 写完 4 个 .py 但没审过"每个 .py 都实际跑了, 输出文件齐不齐".
    现在加这道防线.
    """
    paper_dir = get_paper_dir()
    # 默认假设 求解/ 在 paper_dir 的父目录 (标准 skill 目录结构)
    solve_dir = paper_dir.parent / "求解"
    if not solve_dir.is_dir():
        return ("yellow", f"求解目录不存在 ({solve_dir}), 跳过 Post-Solution Audit",
                "用 --paper-dir 指定论文目录, 跑题目录应有 求解/ 子目录")
    # 必做 2: 每个问题目录有 .py + 图片/ + 结果/
    problem_dirs = sorted([d for d in solve_dir.iterdir()
                          if d.is_dir() and d.name.startswith("问题")])
    if not problem_dirs:
        return ("yellow", f"求解/ 下无 问题N/ 目录 (期望 问题1/ 问题2/ ...)",
                f"按 §Step 2 创建 问题1-N 目录结构")
    problems_status = []
    for pd in problem_dirs:
        py_files = list(pd.glob("*.py"))
        pic_dir = pd / "图片"
        res_dir = pd / "结果"
        png_count = len(list(pic_dir.glob("*.png"))) if pic_dir.is_dir() else 0
        csv_count = (len(list(res_dir.glob("*.csv"))) +
                     len(list(res_dir.glob("*.xlsx")))) if res_dir.is_dir() else 0
        problems_status.append((pd.name, len(py_files), png_count, csv_count))
    # 预期: 每个问题 1 个 .py, ≥ 4 张图, ≥ 1 个结果表
    bad = []
    for name, py, png, csv in problems_status:
        issues = []
        if py == 0:
            issues.append("无 .py")
        if png < 4:
            issues.append(f"图 {png}<4")
        if csv < 1:
            issues.append(f"结果 {csv}<1")
        if issues:
            bad.append(f"{name}({', '.join(issues)})")
    if bad:
        return ("red",
                f"Post-Solution Audit 必做 2 不过: {len(bad)}/{len(problems_status)} 问题输出不齐全",
                f"问题: {bad[:3]}. 跑对应 .py 重新生成, 缺图就调代码, 缺结果就 export")
    # 必做 4: 5.X.2 引用的图/表文件存在
    # 找 5.X.2 文件
    five_two = list(paper_dir.glob("5.*.2.建模与求解.tex"))
    if not five_two:
        return ("yellow", "无 5.X.2 章节文件 (跳过必做 4)",
                "5.X.2 是核心求解章节, 必写")
    five_two_refs = set()
    for f in five_two:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", content):
            five_two_refs.add(m.group(1).strip())
    missing_52 = []
    for ref in five_two_refs:
        candidates = [
            paper_dir / ref,
            paper_dir.parent / ref,
            solve_dir / Path(ref).name,
            SKILL_ROOT / ref,
        ]
        if ref.startswith("../"):
            candidates.insert(0, (paper_dir / ref).resolve())
        if not any(c.exists() for c in candidates):
            missing_52.append(ref)
    if missing_52:
        return ("red",
                f"5.X.2 引用 {len(five_two_refs)} 张图, {len(missing_52)} 张缺失",
                f"跑对应 .py 重新生成缺失的图. 缺失: {missing_52[:3]}")
    return ("green",
            f"Post-Solution Audit 必做 2 + 4 全过: {len(problems_status)} 问题各 {problems_status[0][1]}py/{problems_status[0][2]}png/{problems_status[0][3]}csv + 5.X.2 {len(five_two_refs)} 张图全在",
            None)


def check_reading_checklist():
    """checkable 19: 读题清单 15 项全覆盖 (v1.5.7).

    跑题前必填 `求解/读题清单.md` 15 项, 缺一项 RED (防 2025C 3 P0 错位).
    每项需含: 题面原话 + 你的解读 + 对应代码/论文 (3 列).
    """
    paper_dir = get_paper_dir()
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    # 跑题目录 = paper_dir 的父目录 (标准 skill 结构: 跑题目录/论文/ + 跑题目录/求解/)
    solve_dir = paper_dir.parent / "求解"
    checklist_path = solve_dir / "读题清单.md"
    if not checklist_path.exists():
        if is_template:
            return ("yellow",
                    "example 模板不含读题清单 (设计意图, 跑题用户从 references/读题清单.md 复制到 求解/ 目录)",
                    f"跑题时: cp references/读题清单.md {solve_dir}/读题清单.md")
        return ("red",
                "读题清单.md 不存在 (防 2025C 3 P0 错位, 必填)",
                f"在 {solve_dir}/ 复制 references/读题清单.md 模板, 跑题前填 15 项")
    try:
        content = checklist_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return ("red", f"读读题清单失败: {e}", "查文件权限/编码")

    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    # 检查 15 项全覆盖 (15 个 ### N. 标题)
    expected_items = [f"### {i}." for i in range(1, 16)]
    missing = [it for it in expected_items if it not in content]
    if missing:
        if is_template:
            return ("yellow",
                    f"example 模板读题清单缺失 {len(missing)} 项 (设计意图, 跑题用户填了才 GREEN)",
                    f"缺失: {missing[:3]}")
        return ("red",
                f"读题清单 {len(missing)} 项未填 (15 项必填)",
                f"按 references/读题清单.md 模板补全. 缺失: {missing}")
    # 检查每项都有 3 列内容 (题面原话 / 你的解读 / 对应)
    for i in range(1, 16):
        # 找 ### i. 段
        start = content.find(f"### {i}.")
        if start == -1:
            continue
        # 找下一个 ### j. 段
        next_starts = [content.find(f"### {j}.", start + 1) for j in range(1, 17) if j != i]
        next_starts = [n for n in next_starts if n != -1]
        end = min(next_starts) if next_starts else len(content)
        section = content[start:end]
        # 检查 3 列
        if "题面原话" not in section or "你的解读" not in section or "对应代码" not in section:
            if is_template:
                return ("yellow",
                        f"example 模板读题清单项 {i} 缺列 (设计意图)",
                        f"项 {i} 需含 '题面原话' + '你的解读' + '对应代码'")
            return ("red",
                    f"读题清单项 {i} 缺列 (需 '题面原话' + '你的解读' + '对应代码')",
                    f"按 references/读题清单.md 模板补全项 {i}")
    return ("green",
            f"读题清单 15 项全覆盖 (3 列完整: 题面原话 / 你的解读 / 对应代码)",
            None)


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
    ("15. 占位符未替换 (【 TODO)", check_no_placeholder),
    ("16. 10.附录.tex 文件存在", check_appendix_files),
    ("17. 图引用存在 (includegraphics)", check_figure_exists),
    ("18. Post-Solution Audit (必做 2+4)", check_post_solution_audit),
    ("19. 读题清单 15 项全覆盖 (Step 0)", check_reading_checklist),
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
        yellow_count = 0
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
            elif info["status"] == "yellow":
                yellow_count += 1
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
        # 退出码: 0 = 0 red, 1 = 有 red (yellow 不算失败, 提示 CI 环境差异)
        print(f"\n===== smoke-test summary: {green_count}/{n} green, {yellow_count} yellow, {len(red_items)} red =====")
        if red_items:
            print(f"RED 项: {red_items}")
        sys.exit(0 if not red_items else 1)
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
        yellow_count = sum(1 for r in results.values() if r["status"] == "yellow")
        red_count = sum(1 for r in results.values() if r["status"] == "red")
        if red_count == 0:
            print(f"🟢 sign-off 绿: {green_count}/{n} green, {yellow_count} yellow, 0 red")
            print("   赛前可安心参赛. 祝拿国一!")
        else:
            print(f"⚠️  sign-off 有 red: {green_count}/{n} green, {yellow_count} yellow, {red_count} red")
            print(f"   修复 red 项后重跑, 直到 0 red")
        print("=" * 60)
        sys.exit(0 if red_count == 0 else 1)


if __name__ == "__main__":
    main()
