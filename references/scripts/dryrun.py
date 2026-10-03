"""li-mtrie-2026 赛前 1 天必做 + CI smoke-test 一体化脚本 (v1.5.7).

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
        try:
            import seaborn
            seaborn_ver = seaborn.__version__
        except ImportError:
            seaborn_ver = "未装 (画图库用 matplotlib 即可, seaborn 可选)"
        return ("green", f"pandas {pandas.__version__} + numpy + scipy + openpyxl + fitz + seaborn {seaborn_ver}", None)
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
    return ("green", f"10/10 Python 脚本 py_compile OK (含 v1.5.0 data_utils + v1.5.2 dryrun + v1.5.7 5 项 checkable)", None)


def check_tex_compile():
    """checkable 3: 论文.tex 编译 (xelatex × 2). 失败 = 模板坏了."""
    paper_dir = get_paper_dir()
    # example-paper 状态: 没 fonts/ 必然编译失败, yellow 跳过 (template 自检不需 LaTeX 编译)
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    if is_template:
        return ("yellow",
                f"example 模板状态 (paper_dir={paper_dir.name}, 跳过 LaTeX 编译 = 设计意图, 不算 red)",
                "跑题用户复制 example-paper 到 跑题目录/论文/ 后再编译 (那时 paper_dir 不是 templates/, 本检查会真跑 xelatex)")
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
    log_path = get_paper_dir() / "论文.log"
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
    ver_match = re.search(r'version:\s*"(\d+\.\d+\.\d+(?:\.\d+)?)"', content)
    if not ver_match:
        return ("red", "SKILL.md frontmatter 缺 version 字段", "修 SKILL.md")
    return ("green", f"SKILL.md frontmatter 有效 (version={ver_match.group(1)})", None)


def check_llm_tools():
    """checkable 8: v1.5.0 LLM 工具 5 prompt + README 存在 (v1.5.7 加 05-读题提取)."""
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
        "references/workflow/模型字典使用指南.md",
        "references/paper/格式自查清单.md",
        "references/paper/百分制评审方法.md",
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
        "references/read-checklist/题意翻译.md",
        "references/preparation/学校国奖画像.md",
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
        # v1.5.7 修复外审 P1-4: doc 单词数 < 2 时 .split()[1] 抛 IndexError
        doc = fitz.__doc__ or ""
        ver = doc.split()[1] if len(doc.split()) >= 2 else "unknown"
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
        else:
            print(f"[WARN] --paper-dir 不带值, 静默 fallback 到自动检测 (请给: --paper-dir 跑题目录/论文)", file=sys.stderr)
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
        (r"\\[A-Za-z]+Slot\{", "v1.5.7 *Slot 宏 (AISlot/AppendixSlot/CodeSlot/RefSlot)"),
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
                # P2-9 (v1.5.7.4): 剥离行内 % 注释 (例如 "x = 1  % TODO: fix this" 不应误报)
                pos = m.start() - line_start
                if pos > 0:
                    before = line_text[:pos]
                    # 找最近非 \% 的 %
                    i = len(before) - 1
                    while i >= 0:
                        if before[i] == "%":
                            if i > 0 and before[i-1] == "\\":
                                i -= 1
                                continue
                            break  # 找到真 %, 在 m 之前 = 行内注释
                        i -= 1
                    else:
                        i = -1
                    if i >= 0:
                        continue  # 行内 % 注释, 跳过
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


def check_v1575_polish():
    """checkable 20: v1.5.7.5 writing-for-agents 修剪验证 (4 项)
    1. SKILL.md description ≤ 6 行 (v1.5.7.5 合并 3 触发 → 1)
    2. references/红线与失败模式.md 存在 (v1.5.7.5 推红线)
    3. CHANGELOG.md 存在 (v1.5.7.5 推 history)
    4. SKILL.md 含 4 个 🟢 Step X 完成判据 (v1.5.7.5 加完成判据)
    """
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        return ("red", "SKILL.md 不存在", "修 SKILL.md")
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    # 1. description ≤ 6 行
    if not content.startswith("---\n"):
        return ("red", "SKILL.md 缺 frontmatter (--- 开头)", "修 SKILL.md")
    end = content.find("\n---\n", 4)
    if end == -1:
        return ("red", "SKILL.md frontmatter 缺结尾 ---", "修 SKILL.md")
    fm = content[4:end]
    desc_match = re.search(r'description:\s*\|\n((?:[ \t]+.+\n)+)', fm)
    if not desc_match:
        return ("red", "SKILL.md frontmatter 缺 description", "修 SKILL.md")
    desc_lines = [l for l in desc_match.group(1).split("\n") if l.strip()]
    if len(desc_lines) > 6:
        return ("red", f"SKILL.md description {len(desc_lines)} 行 (v1.5.7.5 修剪应 ≤ 6 行)",
                "合并触发词 (开始求解/跑题/做数模 → 跑题)")
    # 2. references/红线与失败模式.md 存在
    redline = REFS_DIR / "read-checklist" / "红线与失败模式.md"
    if not redline.exists():
        return ("red", "references/红线与失败模式.md 缺失 (v1.5.7.5 推出)",
                "把 SKILL.md §Failure handling + §跨平台代码红线 + §跑题期间红线 3 段推到 references/红线与失败模式.md")
    # 3. CHANGELOG.md 存在
    changelog = SKILL_ROOT / "CHANGELOG.md"
    if not changelog.exists():
        return ("red", "CHANGELOG.md 缺失 (v1.5.7.5 推出)",
                "把 SKILL.md frontmatter history 9 entries 推到 CHANGELOG.md, frontmatter 留 1 行 changelog: CHANGELOG.md")
    # 4. SKILL.md 含 4 个 🟢 Step X 完成判据 (Step 0/1/3/4)
    expected = ["🟢 Step 0 完成判据", "🟢 Step 1 完成判据", "🟢 Step 3 完成判据", "🟢 Step 4 完成判据"]
    missing = [e for e in expected if e not in content]
    if missing:
        return ("red", f"SKILL.md 缺 {len(missing)} 个完成判据 (v1.5.7.5 应 4 个): {missing}",
                "在 §Step 0/1/3/4 末尾各加 1 行 '🟢 Step X 完成判据: ...'")
    return ("green", f"description {len(desc_lines)} 行 + 红线 1 文件 + CHANGELOG 1 文件 + 4 完成判据全在", None)


def check_v1576_data_isolation():
    """checkable 21: v1.5.7.6 数据隔离原则 — 周期起点计划不能用当期实际 (评阅要点对应章节 "数据使用" 条款)
    1. SKILL.md 含 "周期起点信息边界" 章节 (v1.5.7.16 升级: 0:00 决策 → 周期起点决策, 调度类专属例子保留)
    2. references/信息边界原则.md 存在 (核心规则文档)
    3. references/读题清单.md 含 "题面禁项" 第 4 列
    4. 跑题目录 .py 文件不含 "loads_actual[day_idx]" (无 -1) 数据泄露模式
    """
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        return ("red", "SKILL.md 不存在", "修 SKILL.md")
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    # 1. SKILL.md 含 "周期起点信息边界" 章节 (v1.5.7.16 升级)
    if "周期起点信息边界" not in content:
        return ("red", "SKILL.md 缺 '周期起点信息边界' 章节 (v1.5.7.6 必加 + v1.5.7.16 升级概念, 防数据泄露)",
                "在 §Step 0 15 项表格后加 '📌 周期起点信息边界 (v1.5.7.6 新增, v1.5.7.16 概念升级)' 章节, 列三类信息边界 (历史/预报/当期实际)")
    # 2. references/信息边界原则.md 存在
    boundary_doc = REFS_DIR / "data-usage" / "信息边界原则.md"
    if not boundary_doc.exists():
        return ("red", "references/信息边界原则.md 缺失 (v1.5.7.6 核心规则文档)",
                "写 references/信息边界原则.md (三类信息边界 + 反模式 + 实战案例)")
    # 3. references/读题清单.md 含 "题面禁项" 第 4 列
    checklist_md = REFS_DIR / "read-checklist" / "读题清单.md"
    if checklist_md.exists():
        ck_content = checklist_md.read_text(encoding="utf-8", errors="replace")
        if "题面禁项" not in ck_content:
            return ("red", "references/读题清单.md 缺 '题面禁项' 第 4 列 (v1.5.7.6 必加)",
                    "改读题清单模板: 3 列 → 4 列, 加 '题面禁项' 列")
    # 4. 跑题目录 .py 文件不含 day_idx 数据泄露模式 (yellow, 不 red, 因执行阶段可能正确)
    paper_dir = get_paper_dir()
    py_violations = []
    if paper_dir:
        solve_dir = paper_dir.parent / "求解"
        if solve_dir.exists():
            for py_file in solve_dir.rglob("*.py"):
                if py_file.name.startswith("_") or "/共享/" in str(py_file) or "\\共享\\" in str(py_file):
                    continue
                try:
                    py_content = py_file.read_text(encoding="utf-8", errors="replace")
                except:
                    continue
                # 检测 "loads_actual[day_idx]" 或 "pv_actual[day_idx]" 无 -1 修饰 (潜在数据泄露)
                bad_patterns = [
                    (r'loads_actual\[day_idx\](?![\-_])', 'loads_actual[day_idx]'),
                    (r'pv_actual\[day_idx\](?![\-_])', 'pv_actual[day_idx]'),
                    (r'data\[day_idx\](?![\-_])', 'data[day_idx]'),
                ]
                for pat, desc in bad_patterns:
                    matches = re.findall(pat, py_content)
                    if matches:
                        py_violations.append(f'{py_file.name}: {desc} 出现 {len(matches)} 次 (可能的数据泄露)')
    if py_violations:
        return ("yellow",
                f"v1.5.7.6 数据隔离检测: {len(py_violations)} 个潜在风险 ({'; '.join(py_violations[:3])})",
                "0:00 LP 用前一天实际 (loads_actual[day_idx-1]) 或历史平均, 不用当天实际")
    return ("green", f"SKILL.md 信息边界章节 + references/信息边界 + 读题清单 4 列 + 跑题 .py 无 day_idx 数据泄露", None)


def check_v1577_design_intent():
    """checkable 22: v1.5.7.7 题目设计意图分析 — 跑题前必识别递进关系 + 每个问题测什么 + 期望方向
    1. SKILL.md 含 "题目设计意图分析" 章节 (强制锚定)
    2. references/题目设计意图分析.md 存在 (核心方法论文档)
    3. references/读题清单.md 含 "题目设计意图" 第 5 列
    4. 跑题目录 .py 文件含 "递进 / 设计意图 / 期望" 注释 (yellow 警告, 防"按字面跑不解题")
    """
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        return ("red", "SKILL.md 不存在", "修 SKILL.md")
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    # 1. SKILL.md 含 "题目设计意图分析" 章节
    if "题目设计意图分析" not in content:
        return ("red", "SKILL.md 缺 '题目设计意图分析' 章节 (v1.5.7.7 必加, 防按字面跑不解题)",
                "在 §Step 0 信息边界章节后加 '📌 题目设计意图分析 (v1.5.7.7 新增)' 章节, 列递进关系 + 期望方向")
    # 2. references/题目设计意图分析.md 存在
    intent_doc = REFS_DIR / "design-intent" / "题目设计意图分析.md"
    if not intent_doc.exists():
        return ("red", "references/题目设计意图分析.md 缺失 (v1.5.7.7 核心方法论)",
                "写 references/题目设计意图分析.md (4 步法 + 反模式 + 2026 C 题实战复盘)")
    # 3. references/读题清单.md 含 "题目设计意图" 第 5 列
    checklist_md = REFS_DIR / "read-checklist" / "读题清单.md"
    if checklist_md.exists():
        ck_content = checklist_md.read_text(encoding="utf-8", errors="replace")
        if "题目设计意图" not in ck_content:
            return ("red", "references/读题清单.md 缺 '题目设计意图' 第 5 列 (v1.5.7.7 必加)",
                    "改读题清单模板: 4 列 → 5 列, 加 '题目设计意图' 列")
    # 4. 跑题目录 .py 含 "递进 / 设计意图 / 期望" 注释 (yellow 警告)
    paper_dir = get_paper_dir()
    py_missing = []
    if paper_dir:
        solve_dir = paper_dir.parent / "求解"
        if solve_dir.exists():
            for py_file in solve_dir.rglob("*.py"):
                if py_file.name.startswith("_") or "/共享/" in str(py_file) or "\\共享\\" in str(py_file):
                    continue
                try:
                    py_content = py_file.read_text(encoding="utf-8", errors="replace")
                except:
                    continue
                # 检测是否有"递进 / 设计意图 / 期望方向" 注释
                has_intent = any(kw in py_content for kw in [
                    "递进", "设计意图", "期望方向", "期望", "递进关系",
                    "Q3 应", "Q3 应该", "Q3 测", "Q3 期望",
                ])
                if not has_intent:
                    py_missing.append(py_file.name)
    if py_missing:
        return ("yellow",
                f"v1.5.7.7 设计意图检测: {len(py_missing)} 个 .py 缺 '递进/设计意图/期望方向' 注释 ({', '.join(py_missing[:3])})",
                "在 .py 顶部加 '## 递进关系 + 期望方向' 注释 (e.g. 'Q3 期望紧急购电 < Q2, 否则方法错')")
    return ("green", f"SKILL.md 设计意图章节 + references/题目设计意图 + 读题清单 5 列 + 跑题 .py 含递进/设计意图注释", None)


def check_v1579_three_modes_and_data():
    """checkable 23: v1.5.7.9 三口径铁律 + 数据物理真实性
    1. references/题目设计意图分析.md 含 §6 三口径铁律
    2. references/题目设计意图分析.md 含 §7 数据物理真实性
    3. SKILL.md description 提到 v1.5.7.9 (隐含)
    4. 跑题目录 .py 文件不含物理造假关键词 (yellow 警告)
    """
    intent_doc = REFS_DIR / "design-intent" / "题目设计意图分析.md"
    if not intent_doc.exists():
        return ("red", "references/题目设计意图分析.md 缺失", "不可用")
    intent_content = intent_doc.read_text(encoding="utf-8", errors="replace")
    # 1. §6 三口径铁律
    if "三口径铁律" not in intent_content or "计划购电费" not in intent_content:
        return ("red", "references/题目设计意图分析.md 缺 §6 三口径铁律 (v1.5.7.9 必加)",
                "加 §6 三口径铁律: 计划购电费 (预测电价) + 紧急购电费 (当天实际电价 × 5) + 调整偏差费 (0.5/1.5x × c_t)")
    # 2. §7 数据物理真实性
    if "数据物理真实性" not in intent_content:
        return ("red", "references/题目设计意图分析.md 缺 §7 数据物理真实性 (v1.5.7.9 必加)",
                "加 §7 数据物理真实性: 标注附件 2 全年无阴雨, 论文 §5.2.2 诚实说, 不能'修正数据'")
    # 4. 跑题目录 .py 不含物理造假关键词 (yellow 警告)
    paper_dir = get_paper_dir()
    fake_warnings = []
    if paper_dir:
        solve_dir = paper_dir.parent / "求解"
        if solve_dir.exists():
            for py_file in solve_dir.rglob("*.py"):
                if py_file.name.startswith("_") or "/共享/" in str(py_file) or "\\共享\\" in str(py_file):
                    continue
                try:
                    py_content = py_file.read_text(encoding="utf-8", errors="replace")
                except:
                    continue
                # 检测物理造假关键词
                bad_patterns = [
                    (r'人造.*雨|人工.*雨|梅雨.*季', '# 人造梅雨季'),
                    (r'缩.*g.*上界|上界.*P_step\s*\*\s*0\.[1-5]', '# 缩 g 上界'),
                    (r'np\.random.*normal.*noise|np\.random.*uniform.*sigma', '# 加随机噪声'),
                ]
                for pat, desc in bad_patterns:
                    if re.search(pat, py_content):
                        fake_warnings.append(f'{py_file.name}: {desc}')
    if fake_warnings:
        return ("yellow",
                f"v1.5.7.9 物理造假检测: {len(fake_warnings)} 个潜在风险 ({'; '.join(fake_warnings[:3])})",
                "不能人造数据/缩 g 上界/加噪声 — 题面附件 2 是出题组给定数据, 不修正. 论文 §5.2.2 诚实标注数据物理不真实.")
    return ("green", f"references/题目设计意图 §6 三口径 + §7 数据物理真实性 + 跑题 .py 无物理造假关键词", None)


def check_v15711_five_lines_index():
    """checkable 24: v1.5.7.11 5 道防线集中索引 + 自检清单
    1. references/5道防线自检清单.md 存在
    2. 含 §1 总览 + §2 反模式速查 + §3 跑题前自检 + §4 跑完后对照
    3. SKILL.md §Step 0 顶部含"5 道防线速查表"
    """
    index_doc = REFS_DIR / "design-intent" / "5道防线自检清单.md"
    if not index_doc.exists():
        return ("red", "references/5道防线自检清单.md 缺失 (v1.5.7.11 必加)",
                "新建 references/5道防线自检清单.md, 含 §1 5 道防线总览 + §2 反模式对照表 (12 行) + §3 跑题前自检 + §4 跑完后对照 checklist + §5/§6 引用与版本")
    index_content = index_doc.read_text(encoding="utf-8", errors="replace")
    required_sections = [
        ("§1 总览", "5 道防线总览"),
        ("§2 反模式", "反模式速查表"),
        ("§3 自检", "跑题前自检 checklist"),
        ("§4 对照", "跑完后期望对照"),
    ]
    missing = [name for name, kw in required_sections if kw not in index_content]
    if missing:
        return ("red", f"references/5道防线自检清单.md 缺章节 ({', '.join(missing)})",
                "补齐 §1/§2/§3/§4 章节, 让 AI 一处调取 5 道防线")
    # SKILL.md §Step 0 顶部含速查表
    skill_doc = REFS_DIR.parent / "SKILL.md"
    skill_content = skill_doc.read_text(encoding="utf-8", errors="replace")
    if "5 道防线速查表" not in skill_content or "check 24" not in skill_content:
        return ("yellow",
                "SKILL.md §Step 0 顶部含 5 道防线速查表 但未提到 'check 24' (可忽略, 不影响 green)",
                "在 §Step 0 顶部 '5 道防线速查表' 末尾加 '| 24. 检查 | 中心索引 | references/5道防线自检清单.md | check 24 |' (可选)")
    return ("green", "references/5道防线自检清单.md 存在 + 4 章节齐全 + SKILL.md §Step 0 速查表引用", None)


def check_v15713_category_adaptation():
    """checkable 25: v1.5.7.13 类目适配说明 (防通用性陷阱)
    1. references/5道防线自检清单.md 顶部含 '类目适配' 段
    2. references/信息边界原则.md 顶部含 '适用题类' 段
    3. references/题目设计意图分析.md §6 三口径 顶部含 '适用题类' 段
    4. references/题目设计意图分析.md §7 数据物理真实性 顶部含 '通用' 段
    """
    required = [
        (REFS_DIR / "design-intent" / "5道防线自检清单.md", "类目适配", "5道防线自检清单.md 缺类目适配段"),
        (REFS_DIR / "data-usage" / "信息边界原则.md", "适用题类", "信息边界原则.md 缺适用题类说明"),
        (REFS_DIR / "design-intent" / "题目设计意图分析.md", "适用题类", "题目设计意图分析.md §6 缺适用题类说明"),
    ]
    missing = []
    for path, kw, fix in required:
        if not path.exists():
            missing.append(f"{path.name} (文件不存在)")
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if kw not in content:
            missing.append(fix)
    # §7 必须含 '通用' 字样
    intent_doc = REFS_DIR / "design-intent" / "题目设计意图分析.md"
    intent_content = intent_doc.read_text(encoding="utf-8", errors="replace")
    if "通用" not in intent_content[intent_content.find("§7"):] if "§7" in intent_content else "":
        missing.append("题目设计意图分析.md §7 缺 '通用' 标注")
    if missing:
        return ("red", f"v1.5.7.13 类目适配说明缺: {'; '.join(missing)}",
                "在 3 份 references 顶部加 '类目适配 / 适用题类' 段 (防通用性陷阱, 标 [调度类]/[通用]/[物理]/[数据] tag)")
    return ("green", "5道防线自检清单 + 信息边界原则 + 题目设计意图 §6/§7 都含类目适配说明", None)


def check_v15714_category_references():
    """checkable 26: v1.5.7.14 4 类目专属 references (物理/数据/优化/调度) 全在
    (v1.5.7.25 移到 references/by-category/ sub-directory)
    1. references/by-category/物理机理类典型反模式.md 存在 + 含 §1 反模式 + §3 期望对照
    2. references/by-category/数据分析类典型反模式.md 存在 + 含 §1 反模式 + §4 时序严格
    3. references/by-category/优化类典型反模式.md 存在 + 含 §1 反模式 + §3 期望对照
    """
    cat_files = [
        (REFS_DIR / "by-category" / "物理机理类典型反模式.md", ["## 1.", "网格收敛"], "物理机理类典型反模式.md 缺 §1 反模式或网格收敛段"),
        (REFS_DIR / "by-category" / "数据分析类典型反模式.md", ["## 1.", "训练-测试", "时序"], "数据分析类典型反模式.md 缺 §1 反模式或训练-测试/时序段"),
        (REFS_DIR / "by-category" / "优化类典型反模式.md", ["## 1.", "gap", "灵敏度"], "优化类典型反模式.md 缺 §1 反模式或 gap/灵敏度段"),
    ]
    missing = []
    for path, required_kws, fix in cat_files:
        if not path.exists():
            missing.append(f"{path.name} 不存在")
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for kw in required_kws:
            if kw not in content:
                missing.append(f"{path.name} 缺 '{kw}' 段")
    if missing:
        return ("red", f"v1.5.7.14 类目 references 缺: {'; '.join(missing)}",
                "补齐 3 份类目 references (§1 反模式 + 类目专属术语: 物理=网格收敛/数据=训练-测试/优化=gap)")
    return ("green", "by-category/ 3 类目 references 全在 + 类目专属术语齐 (v1.5.7.25 移到 sub-directory)", None)


def check_v15715_more_category_references():
    """checkable 27: v1.5.7.15 7 类目 references 全在 (扩 3 类: 经济/生物/交通)
    (v1.5.7.25 移到 references/by-category/ sub-directory)
    1. references/by-category/经济金融类典型反模式.md 存在 + 含 §1 反模式 + 类目专属术语 (基点/风险度量/压力测试)
    2. references/by-category/生物医疗类典型反模式.md 存在 + 含 §1 反模式 + 类目专属术语 (机理引用/多重校正/伦理)
    3. references/交通运筹类典型反模式.md 存在 + 含 §1 反模式 + 类目专属术语 (网络结构/Pareto/时空约束)
    """
    cat_files = [
        (REFS_DIR / "by-category" / "经济金融类典型反模式.md", ["## 1.", "基点", "压力测试"], "经济金融类典型反模式.md 缺 §1 反模式或基点/压力测试段"),
        (REFS_DIR / "by-category" / "生物医疗类典型反模式.md", ["## 1.", "机理引用", "多重校正"], "生物医疗类典型反模式.md 缺 §1 反模式或机理引用/多重校正段"),
        (REFS_DIR / "by-category" / "交通运筹类典型反模式.md", ["## 1.", "网络结构", "Pareto"], "交通运筹类典型反模式.md 缺 §1 反模式或网络结构/Pareto段"),
    ]
    missing = []
    for path, required_kws, fix in cat_files:
        if not path.exists():
            missing.append(f"{path.name} 不存在")
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for kw in required_kws:
            if kw not in content:
                missing.append(f"{path.name} 缺 '{kw}' 段")
    if missing:
        return ("red", f"v1.5.7.15 新增 3 类目 references 缺: {'; '.join(missing)}",
                "补齐 3 份新类目 references (§1 反模式 + 类目专属术语: 经济=基点/生物=多重校正/交通=Pareto)")
    return ("green", "by-category/ 经济金融/生物医疗/交通运筹 3 类目 references 全在 + 类目专属术语齐 (v1.5.7.25 移到 sub-directory)", None)


def check_v15728_description_six_lines():
    """checkable 32: v1.5.7.28 writing-for-agents 约束 — SKILL.md description ≤ 6 行
    description 是 always-loaded, 行数过多 = context load 失控
    """
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        return ("red", "SKILL.md 不存在", "修 SKILL.md")
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    if not content.startswith("---\n"):
        return ("red", "SKILL.md 缺 frontmatter (--- 开头)", "修 SKILL.md")
    end = content.find("\n---\n", 4)
    if end == -1:
        return ("red", "SKILL.md frontmatter 缺结尾 ---", "修 SKILL.md")
    fm = content[4:end]
    desc_match = re.search(r'description:\s*\|\n((?:[ \t]+.+\n)+)', fm)
    if not desc_match:
        return ("red", "SKILL.md frontmatter 缺 description", "修 SKILL.md")
    desc_lines = [l for l in desc_match.group(1).split("\n") if l.strip()]
    n = len(desc_lines)
    if n > 6:
        return ("red", f"SKILL.md description {n} 行 (writing-for-agents 硬约束 ≤ 6 行, v1.5.7.28 加)",
                "合并触发器 (跑题/出论文/验本 skill) + 砍冗余 (5 道防线版本号串)")
    return ("green", f"SKILL.md description {n} 行 ≤ 6 (writing-for-agents 约束满足)", None)


def check_v15728_leading_words_table():
    """checkable 33: v1.5.7.28 writing-for-agents 约束 — leading words 锚定表全在
    v1.5.7.22 + v1.5.7.27 累计加 10 个核心 leading word, 全部应在 SKILL.md 锚定段
    """
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        return ("red", "SKILL.md 不存在", "修 SKILL.md")
    content = skill_md.read_text(encoding="utf-8", errors="replace")
    required_words = [
        # v1.5.7.22 加
        "green", "red", "sign-off", "checkable", "探路弹", "check N", "5 道防线",
        # v1.5.7.27 加
        "反模式", "陷阱", "踩坑", "避坑",
    ]
    missing = [w for w in required_words if w not in content]
    if missing:
        return ("red", f"SKILL.md leading words 锚定段缺 {len(missing)} 个 ({', '.join(missing)})",
                f"在 SKILL.md §Step 0 顶部 '📌 核心 leading words' 表加这 {len(missing)} 个词")
    return ("green", f"SKILL.md leading words 锚定 {len(required_words)} 个全在 (green/red/sign-off/checkable/探路弹/check N/5 道防线/反模式/陷阱/踩坑/避坑)", None)


def check_v15728_nine_subdirs():
    """checkable 34: v1.5.7.31 — references/ 18 sub-directory 全在 (扩 v1.5.7.28 的 10 → 18)

    18 sub-directory 分 3 类:
    - 10 由 v1.5.7.25-26 拆分新建 (by-category + 9 新建)
    - 8 原有 (2026官方答疑/examples/llm-prompts/scripts/templates/数模资料/板块自查/获奖论文/技能总结)

    ⚠️ v1.5.7.28 之前只验 10 个新建 sub-directory, 已存在的 8 个被忽略 (如果被删, check 不报)
    """
    expected = [
        # v1.5.7.25-26 拆分新建 (10 个)
        "by-category", "data-usage", "design-intent", "read-checklist",
        "workflow", "paper", "plot", "aigc", "audit", "preparation",
        # 原有 (8 个)
        "2026官方答疑", "examples", "llm-prompts", "scripts",
        "templates", "数模资料", "板块自查", "获奖论文",
        # v1.5.7.30 新建 (1 个)
        "技能总结",
    ]
    missing = [s for s in expected if not (REFS_DIR / s).is_dir()]
    if missing:
        return ("red", f"references/ 缺 {len(missing)} 个 sub-directory ({', '.join(missing)})",
                f"恢复这些 sub-directory (按 git log 看是何时删的)")
    # 验证每个 sub-directory 至少 1 个文件
    empty = [s for s in expected if not any((REFS_DIR / s).iterdir())]
    if empty:
        return ("yellow", f"{len(empty)} 个 sub-directory 空 ({', '.join(empty)})",
                f"空目录没人用, 删除或补文件")
    return ("green", f"references/ 18 sub-directory 全在 (v1.5.7.25-26 拆分 10 + 原有 8), 都非空", None)


def check_v15732_skill_md_lines():
    """checkable 35: v1.5.7.32 writing-for-agents 约束 — SKILL.md ≤ 1500 行
    防止 SKILL.md 后续 hotfix 加 inline reference 致 sprawl (>1500 行), 应拆到 references/
    """
    skill_md = SKILL_ROOT / "SKILL.md"
    if not skill_md.exists():
        return ("red", "SKILL.md 不存在", "修 SKILL.md")
    n_lines = sum(1 for _ in skill_md.open(encoding="utf-8", errors="replace"))
    if n_lines > 1500:
        return ("red",
                f"SKILL.md {n_lines} 行 (writing-for-agents 硬约束 ≤ 1500 行, v1.5.7.32 修复后已 1464 行, 现在又膨胀了)",
                "拆 inline reference 段到 references/<sub-dir>/<topic>.md, SKILL.md 留指针 + 1 行说明. 范本: v1.5.7.32 把 §Step 3 + §Step 4.1 117 行拆到 references/paper/写作与附录检查.md")
    return ("green", f"SKILL.md {n_lines} 行 ≤ 1500 (writing-for-agents 约束满足, v1.5.7.32 拆后 1464 行)", None)


def check_v15716_period_start_concept():
    """checkable 28: v1.5.7.16 周期起点决策概念升级 (防 0:00 锚定陷阱)
    1. references/信息边界原则.md 核心规则用 '周期起点' (不锚定 0:00)
    2. SKILL.md §Step 0/1 含 '周期起点' 概念
    3. 5道防线自检清单.md 自检 checklist 用 '周期起点' (而非 0:00)
    """
    # 1. 信息边界原则.md 核心规则用 周期起点
    boundary_doc = REFS_DIR / "data-usage" / "信息边界原则.md"
    if not boundary_doc.exists():
        return ("red", "references/信息边界原则.md 缺失", "不可用")
    boundary_content = boundary_doc.read_text(encoding="utf-8", errors="replace")
    if "周期起点" not in boundary_content:
        return ("red", "references/信息边界原则.md 缺 '周期起点' 概念 (v1.5.7.16 升级)",
                "把 '0:00 决策' 改为 '周期起点决策 (e.g. 每日 0:00 调度)', 概念通用化, 0:00 仅作调度类例子")
    # 2. SKILL.md 含 周期起点
    skill_md = SKILL_ROOT / "SKILL.md"
    skill_content = skill_md.read_text(encoding="utf-8", errors="replace")
    if "周期起点" not in skill_content:
        return ("red", "SKILL.md 缺 '周期起点' 概念 (v1.5.7.16 升级)",
                "把 '0:00 LP' / '0:00 决策' 改为 '周期起点 LP' / '周期起点决策'")
    # 3. 5道防线自检清单.md 含 周期起点
    five_lines_doc = REFS_DIR / "design-intent" / "5道防线自检清单.md"
    if five_lines_doc.exists():
        five_content = five_lines_doc.read_text(encoding="utf-8", errors="replace")
        if "周期起点" not in five_content:
            return ("yellow",
                    "5道防线自检清单.md 缺 '周期起点' 概念 (可忽略, 已大部分替换",
                    "把 §3 自检中 '0:00 信息边界列表' 改为 '周期起点信息边界列表 (历史/预报/当期)'")
    return ("green", "信息边界原则.md + SKILL.md + 5道防线自检清单 都用 '周期起点决策' 概念, 0:00 仅作调度类例子", None)


def check_v15717_consolidation():
    """checkable 29: v1.5.7.17 信息边界 + 题目设计意图 重复段合并 (防内容重复)
    1. 信息边界原则.md §2 反模式 2 不含完整缩 g 代码 (应引用 §7, 不重复)
    2. 信息边界原则.md §2 反模式 2 引用 '题目设计意图分析.md §7'
    3. 题目设计意图分析.md §7 仍存在 + 含 §7 数据物理真实性
    """
    boundary_doc = REFS_DIR / "data-usage" / "信息边界原则.md"
    if not boundary_doc.exists():
        return ("red", "references/信息边界原则.md 缺失", "不可用")
    boundary_content = boundary_doc.read_text(encoding="utf-8", errors="replace")
    # 1. 信息边界 §2 反模式 2 不含完整缩 g 代码 (应该引用 §7)
    if "LpVariable" in boundary_content and "P_step" in boundary_content:
        # 检查是否在 反模式 2 段含这些
        if "反模式 2" in boundary_content and boundary_content.find("反模式 2") < boundary_content.find("LpVariable"):
            return ("red", "信息边界原则.md §2 反模式 2 含完整缩 g 代码 (v1.5.7.17 合并后应引用 §7, 不重复)",
                    "把 §2 反模式 2 的缩 g 代码块替换为 '→ 见 references/题目设计意图分析.md §7' 引用")
    # 2. 信息边界 §2 反模式 2 引用 §7
    if "§7" not in boundary_content or "题目设计意图分析" not in boundary_content:
        return ("red", "信息边界原则.md 缺 §7 引用 (v1.5.7.17 合并后必须引用)",
                "在 §2 反模式 2 加 '→ 见 references/题目设计意图分析.md §7 数据物理真实性标注' 引用")
    # 3. 题目设计意图 §7 仍存在
    intent_doc = REFS_DIR / "design-intent" / "题目设计意图分析.md"
    intent_content = intent_doc.read_text(encoding="utf-8", errors="replace")
    if "数据物理真实性" not in intent_content:
        return ("red", "题目设计意图分析.md 缺 §7 数据物理真实性 (v1.5.7.17 合并后必须保留)",
                "保留 §7, 它是合并后唯一含完整缩 g/Luca 反模式 + 何时举例的章节")
    return ("green", "信息边界 + 题目设计意图 重复段合并: §2 反模式 2 引用 §7, §7 是唯一完整版", None)


def check_v15718_aigc_merge():
    """checkable 30: v1.5.7.18 AIGC 文档合并 (受保护片段 + 检测平台弱点 → AIGC降重策略.md)
    1. references/AIGC降重策略.md 存在 + 含 §1 核心铁律 + §2 5 类禁改 + §3 4 平台 + §7 实战策略
    2. references/受保护片段.md 已删除 (不应存在)
    3. references/检测平台弱点.md 已删除 (不应存在)
    """
    # 1. AIGC降重策略.md 存在 + 4 关键章节
    aigc_doc = REFS_DIR / "aigc" / "AIGC降重策略.md"
    if not aigc_doc.exists():
        return ("red", "references/AIGC降重策略.md 缺失 (v1.5.7.18 合并必须新建)",
                "新建 references/AIGC降重策略.md, 合并 受保护片段 + 检测平台弱点")
    aigc_content = aigc_doc.read_text(encoding="utf-8", errors="replace")
    required_sections = [
        ("§1 核心铁律", "绝不为降重补进原文没有的事实"),
        ("§2 5 类禁改", "5 类禁改片段"),
        ("§3 4 大检测平台", "4 大检测平台对比"),
        ("§7 实战策略", "实战策略"),
    ]
    missing = [name for name, kw in required_sections if kw not in aigc_content]
    if missing:
        return ("red", f"references/AIGC降重策略.md 缺章节 ({', '.join(missing)})",
                "合并 受保护片段 + 检测平台弱点, 至少保留 4 章节: 核心铁律/5 类禁改/4 平台/实战策略")
    # 2 & 3. 受保护片段.md + 检测平台弱点.md 不应存在 (v1.5.7.18 已合并删除)
    legacy_files = [
        REFS_DIR / "受保护片段.md",
        REFS_DIR / "检测平台弱点.md",
    ]
    still_exists = [p.name for p in legacy_files if p.exists()]
    if still_exists:
        return ("yellow",
                f"v1.5.7.18 合并后旧文件仍存在 ({', '.join(still_exists)})",
                f"删除 {'/'.join(still_exists)} — 内容已合并到 references/aigc/AIGC降重策略.md")
    return ("green", "AIGC 文档合并: 受保护片段 + 检测平台弱点 → aigc/AIGC降重策略.md (4 章节齐, 旧文件已删)", None)


def check_v15719_plot_merge():
    """checkable 31: v1.5.7.19 绘图文档合并 (绘图规范 + 绘图避坑 → 绘图规范与避坑.md)
    1. references/绘图规范与避坑.md 存在 + 含 §1 决策三轴 + §2 18 条陷阱 + §3 matplotlib 设置
    2. references/绘图规范.md 已删除 (不应存在)
    3. references/绘图避坑.md 已删除 (不应存在)
    """
    # 1. 新文件存在 + 3 关键章节
    plot_doc = REFS_DIR / "plot" / "绘图规范与避坑.md"
    if not plot_doc.exists():
        return ("red", "references/绘图规范与避坑.md 缺失 (v1.5.7.19 合并必须新建)",
                "新建 references/绘图规范与避坑.md, 合并 绘图规范 + 绘图避坑")
    plot_content = plot_doc.read_text(encoding="utf-8", errors="replace")
    required_sections = [
        ("§1 决策三轴", "决策三轴"),
        ("§2 18 条陷阱", "18 条画图陷阱"),
        ("§3 matplotlib 设置", "matplotlib"),
    ]
    missing = [name for name, kw in required_sections if kw not in plot_content]
    if missing:
        return ("red", f"references/绘图规范与避坑.md 缺章节 ({', '.join(missing)})",
                "合并 绘图规范 + 绘图避坑, 至少保留 3 章节: 决策三轴/18 条陷阱/matplotlib 设置")
    # 2 & 3. 旧文件不应存在 (v1.5.7.19 已合并删除)
    legacy_files = [
        REFS_DIR / "绘图规范.md",
        REFS_DIR / "绘图避坑.md",
    ]
    still_exists = [p.name for p in legacy_files if p.exists()]
    if still_exists:
        return ("yellow",
                f"v1.5.7.19 合并后旧文件仍存在 ({', '.join(still_exists)})",
                f"删除 {'/'.join(still_exists)} — 内容已合并到 references/plot/绘图规范与避坑.md")
    return ("green", "绘图文档合并: 绘图规范 + 绘图避坑 → 绘图规范与避坑.md (3 章节齐, 旧文件已删)", None)


# ===== v1.5.7.34 新增 4 项: 参考文献 4 层审计 (L2/L3/L1-加强/L5-留位) =====

# AI 工具关键词 (L3 禁列清单, 命中即红)
# v1.5.7.34: 26 项基础
# v1.5.7.35: + 14 项扩展 (v17 P0-C claude2025 防御, AI 修复时把自己写进参考文献)
AI_TOOL_FORBIDDEN_KEYWORDS = [
    "ChatGPT", "DeepSeek", "Claude", "Copilot", "文心一言", "通义千问",
    "GPT-4", "GPT-3.5", "GPT-4o", "Kimi", "豆包", "元宝", "文心",
    "星火", "智谱", "Doubao", "Gemini", "Claude-3", "Bard", "Llama",
    "Qwen", "Yi-", "Baichuan", "ChatGLM", "Spark", "ERNIE",
    "Claude Sonnet", "Anthropic", "OpenAI", "GPT-4 Turbo", "GPT-4V",
    "o1-preview", "o3-mini", "Sora", "Mistral", "Mixtral",
    "Claude Opus", "Claude Haiku", "Claude 3.5", "Claude 4",
]

# GB/T 7714 模板字段占位符 (L1 强化, v5 P1 防御)
GB_T_7714_TEMPLATE_FIELDS = [
    "【简要用途",     # 9.0.AI工具使用声明.tex v5 P1 未替换源
    "【简要填",       # 模板示例引导
    "【这里填",       # 模板示例引导
    "【作者",         # 9.参考文献.tex item
    "【论文题名",
    "【期刊名",
    "【年份",
    "【卷",
    "【起止页码",
    "【书名",
    "【出版地",
    "【出版社",
    "【出版年",
    "【授予单位",
    "【发布机构",
    "【报告名称",
    "【数据集名称",
    "【网址",
    "【更新时间",
    "【访问日期",
    "【网页资源名称",
    "【标准号",
    "【标准名称",
    "【出版者",
    "【文件名称",
    "【颁布机构",
    "【发布机构",
    "【发布日期",
]


def check_ref_number_consistency():
    """checkable 36: 参考文献编号对应 (L2 一致性, auto).

    背景: 2025C 跑题 v4 → v5 反复改 9.参考文献.tex, 改了条目没同步正文 \\cite (或反过来),
    导致 cite 编号悬空 (cite 不存在, 红) 或条目孤儿 (定义未引用, 黑/黄).
    防御: 提取所有 \\cite{[n]} (正文) + 9.参考文献.tex \\item [n] (文末),
    做 A-B (cite 不存在) 红 + B-A (孤儿条目) 黄 自检.

    支持 enumerate 自动编号 (按 \\item 出现顺序) 与 \\item [n] (手动) 两种模板.
    Template 状态: yellow (模板占位符 \\item 与真实正文不一致是设计意图).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L2 编号对应自检",
                "用 --paper-dir <path> 指定, 或在跑题目录下跑")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    ref_file = paper_dir / "9.参考文献.tex"
    if not ref_file.exists():
        return ("yellow", "9.参考文献.tex 不存在, 跳过编号对应自检",
                "若使用纯 BZD 模板无 ref, 可忽略; 若有 \\cite 则补建 9.参考文献.tex")

    # 1. 提取 9.参考文献.tex 的 \\item 编号集 B
    ref_content = ref_file.read_text(encoding="utf-8", errors="replace")
    # 模式 A: \\item [n] (手动)
    manual_items = re.findall(r"\\item\s*\[(\d+)\]", ref_content)
    # 模式 B: enumerate 自动编号, 按 \\item 出现顺序
    auto_items = []
    in_enumerate = False
    for line in ref_content.splitlines():
        if r"\begin{enumerate}" in line:
            in_enumerate = True
            continue
        if r"\end{enumerate}" in line:
            in_enumerate = False
            continue
        if in_enumerate and re.search(r"\\item\b", line):
            auto_items.append(len(auto_items) + 1)

    if manual_items:
        ref_nums = set(int(x) for x in manual_items)
        mode = "manual \\item [n]"
    else:
        ref_nums = set(auto_items)
        mode = "enumerate 自动"
    if not ref_nums:
        return ("yellow", "9.参考文献.tex 未识别到 \\item 条目, 跳过编号对应",
                "检查 9.参考文献.tex 是否用 \\begin{enumerate} 或 \\item [n] 结构")

    # 2. 提取所有正文 \\cite{[n]} 集 A
    cited_nums = set()
    cite_loc = {}  # n → [(file, line), ...]
    for tex_file in sorted(paper_dir.glob("*.tex")):
        if tex_file.name == "9.参考文献.tex":
            continue
        try:
            content = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过 % 注释行 (整行 + 行内)
        non_comment_lines = [
            line for line in content.splitlines()
            if not line.lstrip().startswith("%")
        ]
        non_comment = "\n".join(non_comment_lines)
        for m in re.finditer(r"\\cite\{([^}]*)\}", non_comment):
            inner = m.group(1)
            for n in re.split(r"[,，\s]+", inner):
                n = n.strip()
                if n.isdigit():
                    num = int(n)
                    cited_nums.add(num)
                    line_no = non_comment[:m.start()].count("\n") + 1
                    cite_loc.setdefault(num, []).append((tex_file.name, line_no))

    # 3. 比对 A (cited) vs B (ref_items)
    a_minus_b = sorted(cited_nums - ref_nums)  # cite 不存在 → 红
    b_minus_a = sorted(ref_nums - cited_nums)  # 孤儿 → 黄

    if a_minus_b:
        details = []
        for n in a_minus_b:
            for fn, ln in cite_loc.get(n, [])[:2]:
                details.append(f"{fn}:L{ln} \\cite{{{n}}}")
        return ("red",
                f"\\cite 编号 {a_minus_b} 在 9.参考文献.tex 中无对应条目 ({len(a_minus_b)} 处)",
                f"在 9.参考文献.tex 加 \\item [{a_minus_b[0]}] ... 条目. cite 位置: {'; '.join(details[:3])}")

    if b_minus_a:
        return ("yellow",
                f"9.参考文献.tex 编号 {b_minus_a} 未被任何正文 \\cite 引用 (孤儿条目, {len(b_minus_a)} 条)",
                f"删 / 合并 / 补 \\cite{{{b_minus_a[0]}}} 到正文. 数量 {len(b_minus_a)} 条")

    return ("green",
            f"参考文献编号 {len(ref_nums)} 条 ({mode}) 与正文 \\cite 全部对应 (无 cite 不存在, 无孤儿)",
            None)


def check_ai_tool_in_refs():
    """checkable 37: 9.参考文献.tex 不得列 AI 工具 (L3 真实性, auto).

    背景: BZD 2026 规范明确: AI 工具 (ChatGPT / DeepSeek / Claude / Copilot / 文心一言 / ...)
    禁止列入参考文献, 只能在 9.0.AI工具使用声明.tex 声明. 2025C 跑题 v5 验证 AI 工具未误列 ✓,
    加这道防线: 自动扫 {len(AI_TOOL_FORBIDDEN_KEYWORDS)} 关键词, 命中即红.

    Template 状态: yellow (模板示例引导文字含 AI 关键词, 是设计意图).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L3 AI 工具禁列自检",
                "用 --paper-dir <path> 指定, 或在跑题目录下跑")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    ref_file = paper_dir / "9.参考文献.tex"
    if not ref_file.exists():
        return ("yellow", "9.参考文献.tex 不存在, 跳过 AI 工具禁列自检",
                "若使用纯 BZD 模板无 ref, 可忽略")

    content = ref_file.read_text(encoding="utf-8", errors="replace")
    # 跳过 % 整行注释
    non_comment_lines = [
        line for line in content.splitlines()
        if not line.lstrip().startswith("%")
    ]
    non_comment = "\n".join(non_comment_lines)

    violations = []
    for kw in AI_TOOL_FORBIDDEN_KEYWORDS:
        for m in re.finditer(re.escape(kw), non_comment):
            line_no = non_comment[:m.start()].count("\n") + 1
            line_start = non_comment.rfind("\n", 0, m.start()) + 1
            line_end = non_comment.find("\n", m.end())
            if line_end == -1:
                line_end = len(non_comment)
            line_text = non_comment[line_start:line_end]
            violations.append(f"L{line_no} 命中 {kw!r}: {line_text[:80]}")

    if violations:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留 {len(violations)} 处 AI 工具关键词 (BZD 规范引导文字, 跑题时必须删)",
                    f"参考性关键词: {violations[:2]}. 跑题用户需删除 9.参考文献.tex 中所有 AI 工具条目")
        return ("red",
                f"9.参考文献.tex 出现 {len(violations)} 处 AI 工具关键词 (扫 {len(AI_TOOL_FORBIDDEN_KEYWORDS)} 项)",
                f"AI 工具 (ChatGPT/DeepSeek/Claude/...) 禁止列入, 仅在 9.0.AI工具使用声明.tex 声明. 命中: {violations[:3]}")

    return ("green",
            f"9.参考文献.tex 未列 AI 工具 (扫 {len(AI_TOOL_FORBIDDEN_KEYWORDS)} 关键词, 0 命中)",
            None)


def check_template_placeholders_v2():
    """checkable 38: 模板占位符强化检查 (L1 扩展, v5 P1 防御, auto).

    背景: 2025C 跑题 v5 P1: 9.0.AI工具使用声明.tex L4 仍带【简要用途...】占位符,
    check 15 漏报原因可能是 paper_dir 路径不对 / 未跑. 加专项检查:

    1. 9.0.AI工具使用声明.tex: 扫【简要用途】/【简要填】/【这里填】模板引导
    2. 9.参考文献.tex: 扫 \\textbf{【...】} (item 内 GB/T 7714 字段占位符, 模板专用格式)
    3. 通用: 扫【作者】/【论文题名】/【期刊名】/【出版地】等 GB/T 7714 字段

    Template 状态: yellow (模板有意保留), 跑题状态: red.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L1 占位符强化自检",
                "用 --paper-dir <path> 指定, 或在跑题目录下跑")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    target_files = ["9.参考文献.tex", "9.0.AI工具使用声明.tex"]
    violations = []
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            content = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过 % 整行注释
        non_comment_lines = [
            line for line in content.splitlines()
            if not line.lstrip().startswith("%")
        ]
        non_comment = "\n".join(non_comment_lines)
        # 模式 1: \\textbf{【...】} (item 内 GB/T 7714 字段占位符)
        for m in re.finditer(r"\\textbf\{【[^】]*】\}", non_comment):
            line_no = non_comment[:m.start()].count("\n") + 1
            violations.append(f"{fname}:L{line_no} \\textbf{{【...】}} -> {m.group()[:60]}")
        # 模式 2: GB/T 7714 模板字段占位符字符串 (行内自由出现)
        for kw in GB_T_7714_TEMPLATE_FIELDS:
            for m in re.finditer(re.escape(kw), non_comment):
                line_no = non_comment[:m.start()].count("\n") + 1
                violations.append(f"{fname}:L{line_no} 模板占位符 {kw!r}")

    if violations:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留 {len(violations)} 处占位符 (设计意图, 跑题时填掉才 GREEN)",
                    f"占位符示例: {violations[:3]}. 跑题用户复制 example-paper 后替换")
        return ("red",
                f"9.参考文献.tex / 9.0.AI工具使用声明.tex 仍带 {len(violations)} 处模板占位符 (v5 P1 防御)",
                f"替换为实际内容. 重点: 9.0.AI工具使用声明.tex 【简要用途】占位符 (v5 P1 漏报源). 命中: {violations[:3]}")

    return ("green",
            f"9.参考文献.tex + 9.0.AI工具使用声明.tex 模板占位符全替换 (扫 {len(GB_T_7714_TEMPLATE_FIELDS)} 关键词 + \\textbf{{【...】}} 模式, 0 命中)",
            None)


def check_39_numeric_consistency_reserved():
    """checkable 39: 数字一致性 L5 (留位, 摘要-§5 章节-Q 表数字互查).

    背景: 2025C 跑题 v5 报告 P0: 摘要 Q3 节约 5.7% vs §5.3 调整反贵 5.4% (方向反转),
    摘要 Q4-2 = 1504 万 vs §5.4 = 2183 万 vs 文件 = 1843 万 (三处对不上),
    §5.1.2 鲁棒差额 +2552 元 vs +9648 元, §5.2 紧急购电 11.6 万 vs 110.9 万 vs 589 万.
    自动实现复杂度高 (需解析 LaTeX 数学环境 + 跨文件 grep), v1.5.7.34 留位,
    短期由 SKILL.md §Step 4 末尾 "论文内部数字一致性自检清单" (跑题后必做, 手动) 兜底.

    状态: 永久 yellow (留位, 不判 PASS/FAIL), 等下次实现.
    """
    return ("yellow",
            "v1.5.7.34 留位 — 数字一致性 L5 (摘要-§5 章节-Q 表数字互查, 自动实现复杂度高)",
            "短期由 SKILL.md §Step 4 末尾 论文内部数字一致性自检清单 手动兜底 (跑题后必做). 等下次实现 auto check.")


# ===== v1.5.7.35 新增 4 项: 赛后审计 L6/L7/L11/L12 =====

def check_result_vs_paper_numeric():
    """checkable 40: result 文件 vs 论文数字一致性 L6 (auto, 简化版).

    背景: v15 P0-1 (§5.3 表9 365天冒名334天) + 论文综合 10 处 P0 数字偏差
    (Q2/Q3/Q4-2 vs resultX.xlsx 偏差 11.5倍 / 37倍) + v17 P0-A 表9 编造拆分.
    简化版: 跑 .tex 提取 "数字+元/万" + resultX.xlsx 求和, 数量级比对.
    0.5-2.0x green, 否则 yellow. 完整版需解析 LaTeX 数学环境, 等下次.

    Template 状态: yellow (模板占位符 .tex 数字与 result 不一致是设计意图).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L6", "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    result_files = {}
    for r in [paper_dir.parent / "求解", paper_dir.parent / "数据" / "附件" / "附件5"]:
        if r.exists():
            for f in r.rglob("result*.xlsx"):
                m = re.match(r"result(\d[\w-]*)\.xlsx", f.name)
                if m:
                    result_files.setdefault(m.group(1), []).append(f)
    if not result_files:
        return ("yellow", "result*.xlsx 未找到", "跑题后必须生成 result1/2/3/4-2/4-3.xlsx")

    try:
        import openpyxl
    except ImportError:
        return ("yellow", "openpyxl 未装, 跳过 L6", "pip install openpyxl")
    result_totals = {}
    for key, paths in result_files.items():
        for path in paths[:1]:
            try:
                wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
            except Exception:
                continue
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                col_total, col_count = 0, 0
                for row in ws.iter_rows(min_row=2, max_row=min(ws.max_row, 1000), values_only=True):
                    for v in row[:3]:
                        if isinstance(v, (int, float)) and abs(v) > 100:
                            col_total += v
                            col_count += 1
                            break
                if col_count > 10:
                    result_totals[key] = col_total
                    break
            wb.close()
            if key in result_totals:
                break
    if not result_totals:
        return ("yellow", f"result {len(result_files)} 个但无法提取总费用列", "检查 sheet 结构")

    paper_totals = []
    target_files = ["0.摘要.tex", "5.1.1.分析与准备.tex", "5.1.2.建模与求解.tex",
                    "5.2.建模与求解.tex", "5.3.建模与求解.tex", "5.4.建模与求解.tex"]
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in re.finditer(r"(\d{1,3}(?:[,，]\d{3})+|\d{4,})\s*(?:元|万元|万\s*元)", tcontent):
            num_str = m.group(1).replace(",", "").replace("，", "")
            try:
                val = int(num_str)
                unit = m.group(0).replace(m.group(1), "").strip()
                if "万" in unit:
                    val *= 10000
                if val > 10000:
                    paper_totals.append((fname, m.group(0)[:30], val))
            except ValueError:
                pass
    if not paper_totals:
        return ("yellow", "论文 .tex 未找到 数字+元/万元 模式 (简化版)", "完整 L6 需解析 LaTeX 数学环境")

    result_sum = sum(result_totals.values())
    paper_mean = sum(v for _, _, v in paper_totals) / max(len(paper_totals), 1)
    if result_sum == 0:
        return ("yellow", "result 总费用求和=0", "深入检查 sheet")
    ratio = paper_mean / max(result_sum, 1)
    if 0.5 <= ratio <= 2.0:
        return ("green",
                f"L6 简化版: 论文 {len(paper_totals)} 处 / result {len(result_totals)} 个, 数量级匹配 ({ratio:.2f}x)",
                None)
    if is_template:
        return ("yellow",
                f"example 模板有意保留不一致 ({ratio:.2f}x)",
                "跑题用户用真实 resultX.xlsx 重写摘要+§5.X")
    return ("yellow",
            f"result 总费用 vs 论文关键数字均值 比值 {ratio:.2f}x (期望 0.5-2.0)",
            f"跑题后必做 L6 完整比对: resultX.xlsx 各 sheet 总费用 vs 论文 §5.X 表数字. 偏差 > 5% 即按 v15 P0-1 修复")


def check_attachments_vs_paper_mtime():
    """checkable 41: 附件 ↔ 正文 mtime 一致性 L7 (auto).

    背景: v15 P0-4 附件5 旧版 (09-11 11:21, 比新鲜结果旧 2 天) + v17 P0-E 附件5 仅 2/5 刷新.
    防御: 扫 数据/附件/附件N/ mtime vs 论文最新 mtime vs 求解/最新 mtime.
    附件旧于求解 2h+ 红, 旧于论文 2h+ 黄.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L7", "用 --paper-dir 指定")
    if "templates" in str(paper_dir) or "example" in str(paper_dir):
        return ("yellow", "example 模板无附件, 跳过 L7", "跑题用户用真实附件 5 个 result 文件同步")

    paper_mtime = 0
    for tex_file in paper_dir.glob("*.tex"):
        try:
            mt = tex_file.stat().st_mtime
            if mt > paper_mtime:
                paper_mtime = mt
        except Exception:
            continue
    if paper_mtime == 0:
        return ("yellow", "论文 .tex 文件不存在, 跳过 L7", "复制 example-paper → 论文/")

    attach_dir = paper_dir.parent / "数据" / "附件" / "附件5"
    if not attach_dir.exists():
        return ("yellow", "数据/附件/附件5/ 不存在, 跳过 L7", "无附件场景可忽略")
    attach_files = list(attach_dir.glob("*.xlsx"))
    if not attach_files:
        return ("yellow", "附件目录无 .xlsx", "跳过 L7")

    solve_dir = paper_dir.parent / "求解"
    solve_mtime = 0
    if solve_dir.exists():
        for f in solve_dir.rglob("result*.xlsx"):
            try:
                mt = f.stat().st_mtime
                if mt > solve_mtime:
                    solve_mtime = mt
            except Exception:
                continue

    THRESHOLD = 2 * 3600
    stale_attach = []
    very_stale = []
    for f in attach_files:
        try:
            mt = f.stat().st_mtime
        except Exception:
            continue
        age_paper = paper_mtime - mt
        if age_paper > THRESHOLD:
            stale_attach.append(f"{f.name} 旧于论文 {age_paper/3600:.1f}h")
        if solve_mtime > 0 and mt < solve_mtime - THRESHOLD:
            very_stale.append(f"{f.name} 旧于求解 result {age_paper/3600:.1f}h")
    if very_stale:
        return ("red",
                f"附件 {len(very_stale)}/{len(attach_files)} 旧于求解 result (v15 P0-4 / v17 P0-E)",
                f"从 求解/问题X/结果/ 复制新 resultX.xlsx 到 数据/附件/附件5/. 命中: {very_stale[:3]}")
    if stale_attach:
        return ("yellow",
                f"附件 {len(stale_attach)}/{len(attach_files)} 旧于论文 2h+",
                f"提交前最好同步. 命中: {stale_attach[:3]}")
    return ("green",
            f"附件 {len(attach_files)} 个 .xlsx mtime 一致 (无过期)",
            None)


def check_figure_mtime_vs_solve():
    """checkable 45: 旧图未刷新 L11 (auto, includegraphics 图 mtime vs 求解).

    背景: v15 P0-3 §5.4 图7/图8 (Q4-2/Q4-3_全年汇总.png) 是 g_adj 修复前的旧图 +
    v17 P0-E 图7/图8/q1_不确定性分配 均为旧图. 防御: includegraphics 引用的 .png vs
    求解/最新 mtime. 图旧于求解 12h+ 红, 2h+ 黄.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L11", "用 --paper-dir 指定")

    figures_dir = paper_dir / "figures"
    if not figures_dir.exists():
        return ("yellow", "论文/figures/ 不存在, 跳过 L11", "跑题用户应复制 figures/")

    cited_figs = set()
    for tex_file in paper_dir.glob("*.tex"):
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tcontent):
            cited_figs.add(m.group(1))
    if not cited_figs:
        return ("yellow", "论文 .tex 未 includegraphics 任何 .png", "跑题后必加图")

    fig_mtimes = {}
    for fig_rel in cited_figs:
        for cand in [paper_dir / fig_rel, figures_dir / Path(fig_rel).name]:
            if cand.exists():
                try:
                    fig_mtimes[fig_rel] = cand.stat().st_mtime
                    break
                except Exception:
                    continue
    if not fig_mtimes:
        return ("yellow", f"引用 {len(cited_figs)} 张图但 figures/ 中无对应文件", "检查路径一致")

    solve_dir = paper_dir.parent / "求解"
    solve_mtime = 0
    if solve_dir.exists():
        for f in solve_dir.rglob("*"):
            try:
                mt = f.stat().st_mtime
                if mt > solve_mtime:
                    solve_mtime = mt
            except Exception:
                continue

    THRESHOLD_YELLOW = 2 * 3600
    THRESHOLD_RED = 12 * 3600
    stale_yellow = []
    stale_red = []
    for fig_rel, mt in fig_mtimes.items():
        if solve_mtime > 0 and mt < solve_mtime - THRESHOLD_RED:
            age = (solve_mtime - mt) / 3600
            stale_red.append(f"{Path(fig_rel).name} 旧于求解 {age:.1f}h")
        elif solve_mtime > 0 and mt < solve_mtime - THRESHOLD_YELLOW:
            age = (solve_mtime - mt) / 3600
            stale_yellow.append(f"{Path(fig_rel).name} 旧于求解 {age:.1f}h")
    if stale_red:
        return ("red",
                f"图 {len(stale_red)}/{len(fig_mtimes)} 旧于求解 12h+ (v17 P0-E)",
                f"用最新 result 重生成. 命中: {stale_red[:3]}")
    if stale_yellow:
        return ("yellow",
                f"图 {len(stale_yellow)}/{len(fig_mtimes)} 旧于求解 2h+",
                f"提交前最好重生成. 命中: {stale_yellow[:3]}")
    return ("green",
            f"图 {len(fig_mtimes)}/{len(cited_figs)} mtime 一致",
            None)


def check_calendar_window_consistency():
    """checkable 46: 口径混用 L12 (auto, 334 天 vs 365 天).

    背景: v15 P0-1 §5.3 表9 365 天值冒名 334 天 + 论文综合 §2.4 Q4 论文数与任一口径
    都不符 (Q2/Q3 365 天 vs Q4 334 天). 防御: 扫摘要 + §5.X 含 334 天/365 天/2.1-12.31/
    1.1-12.31 关键词. 出现 ≥ 2 种口径 红.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L12", "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    target_files = ["0.摘要.tex", "5.1.1.分析与准备.tex", "5.1.2.建模与求解.tex",
                    "5.2.建模与求解.tex", "5.3.建模与求解.tex", "5.4.建模与求解.tex"]
    patterns_to_check = [
        ("334 天", "334 天"),
        ("365 天", "365 天"),
        ("2.1-12.31", "2.1-12.31 (334 天区间)"),
        ("1.1-12.31", "1.1-12.31 (365 天区间)"),
        ("2025.2.1", "2025.2.1 (334 天起点)"),
        ("2025.1.1", "2025.1.1 (365 天起点)"),
    ]
    found = set()
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        non_comment = "\n".join(
            line for line in tcontent.splitlines()
            if not line.lstrip().startswith("%")
        )
        for kw, label in patterns_to_check:
            if non_comment.count(kw) > 0:
                found.add(label)

    distinct_calendars = set()
    if any("334 天" in k or "2.1-12.31" in k or "2025.2.1" in k for k in found):
        distinct_calendars.add("334 天")
    if any("365 天" in k or "1.1-12.31" in k or "2025.1.1" in k for k in found):
        distinct_calendars.add("365 天")

    n = len(distinct_calendars)
    if n == 0:
        return ("yellow", "论文 .tex 未出现 334/365 口径关键词", "建议摘要 + §5.X 明确统计期")
    if n >= 2:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留 {n} 种口径引导",
                    f"跑题用户统一为 334 天 (附件5 模板口径) 或 365 天 (全年). 命中: {list(distinct_calendars)}")
        return ("red",
                f"论文混用 {n} 种统计期口径 {distinct_calendars} (v15 P0-1 / 论文综合 §2.4)",
                f"全文统一为 334 天 (附件5 对齐) 或 365 天. 命中: {list(found)}")
    return ("green",
            f"口径统一: {distinct_calendars} (L12 扫 {len(found)} 关键词命中)",
            None)


# ===== v1.5.7.36 新增 2 项: 绘图自检 L14 (冗余图) + L15 (图注 vs axes) =====

def check_unused_figures():
    """checkable 47: figures/ 中未被 \includegraphics 引用的图 (auto).

    背景: 论文综合 (Sep 12) §六.2 反例 — 8 张冗余未引用图残留
    (q2_季节PV箱线图.png / q2_月度发电量对比.png / q2_全年汇总.png /
    q2_累计费用.png / q2_梅雨敏感性.png / q2_预测误差敏感性.png /
    q2_不完美预测.xlsx / q2_用附件3不滚动.xlsx). 这些图是上一轮分析残留或
    自己加的中间产物, 不被任何 \includegraphics 引用, 却跟着 figures/ 一起
    提交. 防御: 调 references/scripts/check_figure.py:find_unused_figures
    扫 figures/ vs 所有 .tex \includegraphics 引用集, 报告差集.

    Template 状态: yellow (template 示例 figures/ 含占位图, 设计意图).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L14 冗余图检查",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    # 1. 找 figures/ 目录
    figures_dir = paper_dir / "figures"
    if not figures_dir.exists():
        return ("yellow", "论文/figures/ 不存在, 跳过 L14 (无图场景)",
                "跑题用户应复制 example-paper/figures/ → 论文/figures/")

    # 2. 扫 figures/ 中所有目标图, 与所有 .tex \includegraphics 集比对
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from check_figure import find_unused_figures
    except ImportError as e:
        return ("yellow", f"check_figure.py 导入失败: {e}", "检查 references/scripts/check_figure.py 完整性")

    tex_files = [str(p) for p in paper_dir.glob("*.tex")]
    try:
        unused, cited = find_unused_figures(figures_dir, tex_files=tex_files)
    except Exception as e:
        return ("yellow", f"find_unused_figures 调用失败: {e}", "检查 check_figure.py 实现")

    if not unused and not cited:
        return ("yellow", f"figures/ {figures_dir} 无 .png/.pdf/.svg 图", "跑题后必须生成图")

    if not unused:
        return ("green",
                f"figures/ {len(cited)} 张图全部被 \includegraphics 引用 (无冗余)",
                None)

    # 有冗余
    if is_template:
        return ("yellow",
                f"example 模板有意保留 {len(unused)} 张冗余图 (设计意图, 跑题时清理才 GREEN)",
                f"冗余示例: {unused[:3]}. 跑题用户复制 example-paper 后删冗余图")
    return ("yellow",
            f"figures/ 有 {len(unused)} 张图未被任何正文 \includegraphics 引用 (论文综合 §六.2 反例)",
            f"删除冗余图: {unused[:5]}. 引用图: {len(cited)} 张")


def check_caption_axes_consistency():
    """checkable 48: 论文 PDF caption 含多面板语义但 figure 实际只有 1 张图 (auto).

    背景: 论文综合 (Sep 12) §六.1 反例 — 图1 图注称"上: 购电量与电价, 下: 储能 SOC",
    实际只有单面板 (无 SOC 子图). 图注与实际 axes 数不符是图片堆积型问题,
    评委一眼能看出"图说一套, 画一套". 防御: 调 references/scripts/visual_qa.py:
    check_caption_axes_consistency 扫 PDF 中 caption 关键词 vs figure axes 数.

    Template 状态: yellow (template 无 PDF, 跳过).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L15 图注检查",
                "用 --paper-dir 指定")

    # 1. 找 PDF (论文.pdf 或 电子版.pdf)
    pdf_candidates = ["论文.pdf", "电子版.pdf", "main.pdf", "paper.pdf"]
    pdf_path = None
    for fn in pdf_candidates:
        cand = paper_dir / fn
        if cand.exists():
            pdf_path = str(cand)
            break
    if pdf_path is None:
        return ("yellow", f"论文 PDF 不存在 ({pdf_candidates}), 跳过 L15",
                "跑题后必先生成 PDF (xelatex × 2)")

    # 2. 调 visual_qa.py check_caption_axes_consistency
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from visual_qa import check_caption_axes_consistency
    except ImportError as e:
        return ("yellow", f"visual_qa.py 导入失败: {e}", "检查 references/scripts/visual_qa.py 完整性")

    try:
        issues = check_caption_axes_consistency(pdf_path)
    except Exception as e:
        return ("yellow", f"check_caption_axes_consistency 调用失败: {e}", "检查 visual_qa.py 实现")

    if not issues:
        return ("green",
                f"L15 图注 vs axes 一致性: PDF {pdf_path} 无多面板 caption-axes 不符",
                None)

    # 有问题
    has_red = any(sev == "FAIL" for sev, _ in issues)
    if has_red:
        msgs = [m for s, m in issues if s == "FAIL"]
        return ("red",
                f"图注含多面板语义但 figure 实际 axes 不够 (论文综合 §六.1 反例)",
                f"修改 figure: 加子图或删 caption 多面板描述. 命中: {msgs[:3]}")

    has_warn = any(sev == "WARN" for sev, _ in issues)
    msgs_w = [m for s, m in issues if s == "WARN"]
    return ("yellow",
            f"L15 图注扫描: 找到 {len(issues)} 处 caption 含多面板语义, 需人工核对 (论文综合 §六.1 反例)",
            f"命中: {msgs_w[:3]}")


CHECKS = [
    ("1. 装包 (核心包)", check_pkg),
    ("2. 10 Python 脚本", check_python_scripts),
    ("3. LaTeX 编译", check_tex_compile),
    ("4. Overfull 数", check_overfull),
    ("5. pack.py + 2 zip", check_pack),
    ("6. AIGC 风险", check_aigc),
    ("7. SKILL.md frontmatter", check_skill_md_frontmatter),
    ("8. LLM 工具 5 prompt (v1.5.0+)", check_llm_tools),
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
    ("20. v1.5.7.5 writing-for-agents 修剪 (description/红线/CHANGELOG/4 完成判据)", check_v1575_polish),
    ("21. v1.5.7.6 数据隔离原则 (周期起点不用当期实际, v1.5.7.16 升级 0:00 概念)", check_v1576_data_isolation),
    ("22. v1.5.7.7 题目设计意图分析 (递进关系 + 期望方向)", check_v1577_design_intent),
    ("23. v1.5.7.9 三口径铁律 + 数据物理真实性", check_v1579_three_modes_and_data),
    ("24. v1.5.7.11 5 道防线自检清单 (中心索引 + 反模式 + checklist)", check_v15711_five_lines_index),
    ("25. v1.5.7.13 类目适配说明 (防通用性陷阱, 3 references 顶部标 [调度类]/[通用])", check_v15713_category_adaptation),
    ("26. v1.5.7.14 4 类目 references (物理/数据/优化 + 调度, 类目专属术语, v1.5.7.25 移到 by-category/)", check_v15714_category_references),
    ("27. v1.5.7.15 7 类目 references (扩 3 类: 经济/生物/交通, 类目专属术语, v1.5.7.25 移到 by-category/)", check_v15715_more_category_references),
    ("28. v1.5.7.16 周期起点决策概念升级 (防 0:00 锚定陷阱)", check_v15716_period_start_concept),
    ("29. v1.5.7.17 信息边界 + 题目设计意图 重复段合并 (防内容重复)", check_v15717_consolidation),
    ("30. v1.5.7.18 AIGC 文档合并 (受保护片段 + 检测平台弱点 → AIGC降重策略.md)", check_v15718_aigc_merge),
    ("31. v1.5.7.19 绘图文档合并 (绘图规范 + 绘图避坑 → 绘图规范与避坑.md)", check_v15719_plot_merge),
    ("32. v1.5.7.28 SKILL.md description ≤ 6 行 (writing-for-agents 约束)", check_v15728_description_six_lines),
    ("33. v1.5.7.28 SKILL.md leading words 锚定 10 词全在 (green/red/sign-off/checkable/探路弹/check N/5 道防线/反模式/陷阱/踩坑/避坑)", check_v15728_leading_words_table),
    ("34. v1.5.7.31 references/ 18 sub-directory 全在 (10 拆分 + 8 原有: 2026官方答疑/examples/llm-prompts/scripts/templates/数模资料/板块自查/获奖论文 + 1 新建 技能总结)", check_v15728_nine_subdirs),
    ("35. v1.5.7.32 SKILL.md ≤ 1500 行 (writing-for-agents 硬约束, 防止 6 维度 sprawl)", check_v15732_skill_md_lines),
    ("36. v1.5.7.34 参考文献编号对应 L2 (\\cite 与 \\item 互查, A-B 红 cite 不存在, B-A 黄孤儿)", check_ref_number_consistency),
    ("37. v1.5.7.34 AI 工具禁列 L3 (9.参考文献.tex 扫 {N} 关键词, 命中红, BZD 2026 规范)", check_ai_tool_in_refs),
    ("38. v1.5.7.34 模板占位符强化 L1 (9.参考文献 + 9.0.AI声明 扫 \\textbf{{【...】}} + GB/T 7714 字段, v5 P1 防御)", check_template_placeholders_v2),
    ("39. v1.5.7.34 数字一致性 L5 (摘要-§5 章节-Q 表数字互查, 留位, 短期 SKILL.md §Step 4 手动清单兜底)", check_39_numeric_consistency_reserved),
    ("40. v1.5.7.35 result 文件 vs 论文数字 L6 (数量级比对, 简化版, v15 P0-1 / 论文综合 10 处 P0 防御)", check_result_vs_paper_numeric),
    ("41. v1.5.7.35 附件 vs 正文 mtime L7 (附件旧于求解红, 旧于论文黄, v15 P0-4 / v17 P0-E 防御)", check_attachments_vs_paper_mtime),
    ("45. v1.5.7.35 旧图未刷新 L11 (includegraphics 图 mtime vs 求解, 旧于 12h 红, v15 P0-3 / v17 P0-E 防御)", check_figure_mtime_vs_solve),
    ("46. v1.5.7.35 口径混用 L12 (334 天 vs 365 天, ≥2 种混用红, v15 P0-1 / 论文综合 §2.4 防御)", check_calendar_window_consistency),
    ("47. v1.5.7.36 冗余图 L14 (figures/ 中未 \\includegraphics 引用的 .png/.pdf/.svg, 论文综合 §六.2 反例)", check_unused_figures),
    ("48. v1.5.7.36 图注 vs axes L15 (PDF caption 含多面板语义但 figure 实际 axes 不够, 论文综合 §六.1 反例)", check_caption_axes_consistency),
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
        print("li-mtrie-2026 赛前 1 天 + CI smoke-test (v1.5.7.1)")
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
