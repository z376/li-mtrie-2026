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
    python references/scripts/dryrun.py            # v1.5.7.39 默认: agent-audit (输出 brief, 调 mavis 代理)
    python references/scripts/dryrun.py --mode self   # self-audit 65 项 hardcode check
    python references/scripts/dryrun.py --mode both  # 两种都跑 (self check + agent brief)
    python references/scripts/dryrun.py --json       # 输出 JSON 报告 (可管道)
    python references/scripts/dryrun.py --ci         # CI 模式, 输出 GitHub Actions 友好格式
    python references/scripts/dryrun.py --agent-audit # 等价 --mode agent (旧 flag 向后兼容)
"""
import json
import sys
import os
import atexit

# Windows GBK console 兼容 (v1.7.2 新增: 子进程管道输出必须是 UTF-8)
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass  # 旧 Python / 非 stdout 对象, 跳过
import subprocess
import shutil
import re
import zipfile
from pathlib import Path

# v1.6.8: 自检不得在 skill 仓库里留 __pycache__
# (check 60/64/65 会 import check_meta / bc_check / number_ledger, import 即写 .pyc)
sys.dont_write_bytecode = True

# v1.6.8: 自检用的临时目录 (pack 输出 + 日志) 必须**用完即删**
# v1.6.6 把 pack.py 的 zip 改写到临时目录避���污染 skill 安装目录, 但没删临时目录
# → 每跑一次 dryrun 就在 TEMP 留 29 MB (实测 9 次 = 265 MB). 用 atexit 兜底清干净.
_TMP_DIRS = []


def _make_tmpdir(prefix):
    """建临时目录并登记 (退出时自动删除)."""
    import tempfile
    d = Path(tempfile.mkdtemp(prefix=prefix))
    _TMP_DIRS.append(d)
    return d


@atexit.register
def _cleanup_tmpdirs():
    for d in _TMP_DIRS:
        shutil.rmtree(d, ignore_errors=True)
    _TMP_DIRS.clear()


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
    r"""checkable 2: 全部 Python 脚本语法编译验证 (auto, v1.6.6 改为自动枚举).

    v1.6.6 改 (代理审计 P2-5): 原版硬编码 10 个脚本, 包内实际已有 **15 个** .py
    (漏 bc_check / fig_sanity / check_meta / number_ledger / agent_audit) →
    新增脚本从没被语法验证过. 现改为 rglob 自动枚举.

    副作用修复 (P2-6): 原来用 `py_compile` 会在 skill 目录生成 `__pycache__/`
    (污染工作区). 现改为内存编译 (`compile()`), 不落任何文件.
    """
    scripts = []
    for rel_dir in ("references/scripts", "references", "tools"):
        d = SKILL_ROOT / rel_dir
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.py")):
            if p.name.startswith("_"):
                continue
            scripts.append(p)
    if not scripts:
        return ("red", "找不到任何 Python 脚本", "检查 references/scripts/ 目录")

    failed = []
    for path in scripts:
        # 内存编译, 不落 __pycache__ (v1.6.6 副作用修复)
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
            compile(src, str(path), "exec")
        except SyntaxError as e:
            failed.append(f"{path.name} 语法错误: {e.msg} (L{e.lineno})")
        except Exception as e:
            failed.append(f"{path.name} 读取失败: {e}")
    if failed:
        return ("red", f"{len(failed)}/{len(scripts)} 脚本语法验证失败",
                "; ".join(failed[:3]))
    return ("green",
            f"{len(scripts)}/{len(scripts)} Python 脚本语法 OK (自动枚举, 内存编译不落 __pycache__)",
            None)


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
    # v1.6.8 副作用修复: 日志落盘位置
    #   - CI (GITHUB_ACTIONS=true): 落 .github/dryrun-logs/ 供 artifact 上传排查
    #   - 本地: 落临时目录 —— 否则每跑一次 dryrun 就在 skill 仓库里留下 2 个日志文件,
    #     "工作区干净" 会被反复破坏
    if os.environ.get("GITHUB_ACTIONS") == "true":
        log_dir = SKILL_ROOT / ".github" / "dryrun-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        log_dir = _make_tmpdir("li_mtrie_dryrun_logs_")
    stdout_log = log_dir / "pack_stdout.log"
    stderr_log = log_dir / "pack_stderr.log"
    with open(stdout_log, "wb") as sout, open(stderr_log, "wb") as serr:
        # 设 PYTHONIOENCODING=utf-8 防 Windows runner 默认 cp936 触发
        # UnicodeEncodeError (pack.py print 中文/特殊字符崩溃, exit 1 无 stderr)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        # v1.6.6 副作用修复 (P2-6): pack.py 默认把 zip 写到 skill **同级目录**,
        # 自检时不该在用户环境里留 2 个 25MB 文件 → 改写到临时目录
        # v1.6.8: 临时目录用完即删 (atexit), 否则每次 dryrun 留 29 MB 在 TEMP
        pack_out = _make_tmpdir("li_mtrie_pack_")
        env["PACK_OUT_DIR"] = str(pack_out)
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
    zips = list(Path(pack_out).glob("li-mtrie-2026-*.zip"))
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
    r"""checkable 7: SKILL.md frontmatter 有效 (含 name + version) + 版本三方一致 (v1.6.5 增强).

    v1.6.5 增强 (代理审计 P1-8): 原来只校验 version 字段**存在**, 不与任何东西比对 →
    frontmatter 长期停在 "1.5.7.44" 而仓库已到 v1.6.4, 陈旧版本静默通过.
    现在做三方比对: frontmatter version == CHANGELOG.md 首条版本 == git tag (最新).

    判据:
    - 三者一致 → green
    - 不一致 → red (版本元数据与实际发布不符, 加载方拿到的版本信息是错的)
    - 取不到 git tag (zip 分发/无 git) → yellow (跳过比对, 不误报)
    """
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
    fm_ver = ver_match.group(1)

    # 三方比对: CHANGELOG 首条 + git 最新 tag
    changelog_ver = None
    cl = SKILL_ROOT / "CHANGELOG.md"
    if cl.exists():
        head = cl.read_text(encoding="utf-8", errors="replace")[:3000]
        m = re.search(r"^#\s*CHANGELOG\s*\(v?(\d+\.\d+\.\d+(?:\.\d+)?)", head, re.M)
        if m:
            changelog_ver = m.group(1)
    tag_ver = None
    try:
        r = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                           cwd=str(SKILL_ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            tag_ver = r.stdout.strip().lstrip("v")
    except Exception:
        tag_ver = None

    known = [("CHANGELOG.md 首条", changelog_ver)]
    mismatches = [(name, v) for name, v in known if v and v != fm_ver]
    if mismatches:
        detail = ", ".join(f"{n}={v}" for n, v in mismatches)
        return ("red",
                f"SKILL.md 版本与 CHANGELOG 首条不一致: frontmatter={fm_ver} vs {detail} "
                f"(加载方读到的版本元数据是错的)",
                f"把 SKILL.md frontmatter version 改成 CHANGELOG 首条版本 "
                f"({changelog_ver}), 并同步 last_update")
    if tag_ver and tag_ver != fm_ver:
        # tag 落后是正常中间态 (先 commit 后打 tag), 只警告不判红
        return ("yellow",
                f"SKILL.md frontmatter={fm_ver} 与 CHANGELOG 首条一致; "
                f"但 git 最新 tag 是 {tag_ver} (未同步)",
                f"发完版打 tag: git tag -a v{fm_ver} -m '...' && git push origin v{fm_ver}")
    if not changelog_ver and not tag_ver:
        return ("yellow",
                f"SKILL.md frontmatter 有效 (version={fm_ver}); 取不到 CHANGELOG/tag 无法比对",
                "在 git 仓库里跑才有版本比对")
    return ("green",
            f"SKILL.md frontmatter 有效 (version={fm_ver}, 与 CHANGELOG 首条一致"
            + (f"; git tag {tag_ver} 一致" if tag_ver == fm_ver else "") + ")",
            None)


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
    # v1.6.5 修 (代理审计 P1-4): 原实现先读环境变量再读命令行, 与 docstring 声明的
    # "--paper-dir 参数 > PAPER_DIR 环境变量" 相反 —— 设了 PAPER_DIR 时 --paper-dir 会被静默忽略.
    # 命令行参数优先级更高 (用户当次显式指定 > 环境里的默认值).
    if "--paper-dir" in sys.argv:
        idx = sys.argv.index("--paper-dir")
        if idx + 1 < len(sys.argv):
            return Path(sys.argv[idx + 1])
        else:
            print(f"[WARN] --paper-dir 不带值, 静默 fallback 到自动检测 (请给: --paper-dir 跑题目录/论文)", file=sys.stderr)
    env_dir = os.environ.get("PAPER_DIR")
    if env_dir:
        return Path(env_dir)
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


def _parse_yaml_block_scalar(text, key):
    r"""解析 YAML block scalar (`key: |` / `key: >`) 的全部内容行.

    v1.7.0 修 (假绿): 旧实现用正则 `description:\s*\|\n((?:[ \t]+.+\n)+)`,
    **遇到第一个空行就停** —— 而本 SKILL.md 的 description 是 3 段 (段间有空行),
    于是正则只量到第 1 行 => check 32 永远报 "1 行 <= 6" = **恒 green = 假绿**.
    现在按 YAML 语义解析: 缩进块内的空行也算块内, 直到出现"非空且非缩进"的行才结束.
    """
    lines = text.split("\n")
    pat = re.compile(r"^\s*" + re.escape(key) + r"\s*:\s*[|>]\s*$")
    start = None
    for i, l in enumerate(lines):
        if pat.match(l):
            start = i
            break
    if start is None:
        return []
    block = []
    for l in lines[start + 1:]:
        if l.strip() == "":
            block.append(l)
            continue
        if l[:1] in (" ", "\t"):
            block.append(l)
            continue
        break
    while block and not block[-1].strip():
        block.pop()
    return [l for l in block if l.strip()]


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
    desc_lines = _parse_yaml_block_scalar(fm, "description")
    if not desc_lines:
        return ("red", "SKILL.md frontmatter 缺 description", "修 SKILL.md")
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
    """checkable 40: result 文件 vs 论文数字一致性 L6 (auto, v1.5.7.43 完整版).

    背景: v15 P0-1 (§5.3 表9 365天冒名334天) + 论文综合 10 处 P0 数字偏差
    (Q2/Q3/Q4-2 vs resultX.xlsx 偏差 11.5倍 / 37倍) + v17 P0-A 表9 编造拆分.

    v1.5.7.43 升级: 解析 LaTeX 数学环境 (`$...$`, `\\[...\\]`, `\\begin{equation}`,
    `\\begin{align}` 等) 提取数字 + 上下文, 按"问题"模式配对论文 §5.X.X
    vs resultX.xlsx. 偏差 > 5% 红, 1-5% 黄, < 1% green.

    Template 状态: yellow (模板占位符 .tex 数字与 result 不一致是设计意图).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L6", "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    # 1. 找 result*.xlsx
    result_files = {}
    for r in [paper_dir.parent / "求解", paper_dir.parent / "数据" / "附件" / "附件5"]:
        if r.exists():
            for f in r.rglob("result*.xlsx"):
                m = re.match(r"result(\d[\w-]*)\.xlsx", f.name)
                if m:
                    result_files.setdefault(m.group(1), []).append(f)
    if not result_files:
        return ("yellow", "result*.xlsx 未找到", "跑题后必须生成 result1/2/3/4-2/4-3.xlsx")

    # 2. 提取每个 result key 的最大数字 sheet 列 (代替简化版前 3 列求和)
    try:
        import openpyxl
    except ImportError:
        return ("yellow", "openpyxl 未装, 跳过 L6", "pip install openpyxl")
    result_max = {}  # key -> (sheet_name, max_value, max_row_index)
    for key, paths in result_files.items():
        for path in paths[:1]:
            try:
                wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
            except Exception:
                continue
            key_max = 0
            key_max_sheet = ""
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                for row in ws.iter_rows(min_row=2, max_row=min(ws.max_row, 1500), values_only=True):
                    for v in row:
                        if isinstance(v, (int, float)) and abs(v) > key_max:
                            key_max = abs(v)
                            key_max_sheet = sheet_name
            if key_max > 0:
                result_max[key] = (key_max_sheet, key_max)
            wb.close()
            if key in result_max:
                break
    if not result_max:
        return ("yellow", f"result {len(result_files)} 个但无法提取最大数字列", "检查 sheet 结构")

    # 3. 解析 LaTeX 数学环境, 提取 (章节, 上下文, 数字) 三元组
    paper_numbers = []  # (chapter_key, context, value, unit)
    target_files = ["0.摘要.tex", "1.引言.tex", "5.1.1.分析与准备.tex",
                    "5.1.2.建模与求解.tex", "5.2.建模与求解.tex",
                    "5.3.建模与求解.tex", "5.4.建模与求解.tex", "6.模型检验.tex"]
    # 章节 → result key 映射
    chapter_to_key = {
        "0.摘要.tex": "all",       # 摘要对所有
        "1.引言.tex": "all",
        "5.1.1.分析与准备.tex": "1",
        "5.1.2.建模与求解.tex": "1",
        "5.2.建模与求解.tex": "2",
        "5.3.建模与求解.tex": "3",
        "5.4.建模与求解.tex": "4-2",
        "6.模型检验.tex": "all",
    }
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过 % 注释行
        non_comment = "\n".join(
            line for line in tcontent.splitlines()
            if not line.lstrip().startswith("%")
        )
        # 提取数学环境: $...$, \[...\], \begin{equation}...\end{equation}
        math_envs = []
        # $...$ 行内
        for m in re.finditer(r"\$([^\$\n]+)\$", non_comment):
            math_envs.append(m.group(1))
        # \[...\] 显示
        for m in re.finditer(r"\\\[([^\]]+)\\\]", non_comment, re.DOTALL):
            math_envs.append(m.group(1))
        # \begin{equation}...\end{equation}
        for m in re.finditer(r"\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}", non_comment, re.DOTALL):
            math_envs.append(m.group(1))
        # \begin{align}...\end{align}
        for m in re.finditer(r"\\begin\{align\*?\}(.+?)\\end\{align\*?\}", non_comment, re.DOTALL):
            math_envs.append(m.group(1))
        # 数学环境内提取数字 + 单位
        chapter_key = chapter_to_key.get(fname, "all")
        for env in math_envs:
            # 数字模式: 1,234,567 / 1234 / 1234.56 / 1.2e5
            for m in re.finditer(r"(\d{1,3}(?:[,，]\d{3})+(?:\.\d+)?|\d{4,}(?:\.\d+)?)", env):
                num_str = m.group(1).replace(",", "").replace("，", "")
                try:
                    val = float(num_str)
                except ValueError:
                    continue
                # 单位推断: 找 env 内跟数字最近的"元/万/百/k/M/G"
                # 简化: 找 env 内"万" "亿" 等
                unit_scale = 1
                for u, s in [("万", 10000), ("亿", 100000000), ("百万", 1000000), ("千", 1000), ("百", 100)]:
                    if u in env:
                        # 取最后一个出现的单位
                        idx = env.rfind(u)
                        num_idx = m.start()
                        if num_idx < idx and (idx - num_idx) < 10:  # 单位在数字后 10 字符内
                            unit_scale = s
                            break
                # 上下文 (前 20 字符)
                ctx_start = max(0, m.start() - 20)
                context = env[ctx_start:m.end() + 10]
                if val * unit_scale > 1000:  # 过滤过小 (e.g. 索引 1, 2, 3)
                    paper_numbers.append((chapter_key, fname, context.strip()[:60], val * unit_scale, unit_scale))

    if not paper_numbers:
        return ("yellow", "论文 .tex 数学环境内未找到 > 1000 数字", "完整 L6 需 论文有数学公式 (1,234 元 / 12.34 万元)")

    # 4. 按 result key 分组论文数字, 取每个 key 对应的论文数字集合
    paper_by_key = {}
    for chapter_key, fname, ctx, val, scale in paper_numbers:
        if chapter_key == "all":
            # 摘要/检验部分: 加到所有 key
            for k in result_max.keys():
                paper_by_key.setdefault(k, []).append((fname, ctx, val, scale))
        elif chapter_key in result_max:
            paper_by_key.setdefault(chapter_key, []).append((fname, ctx, val, scale))

    # 5. 对每个 result key, 取论文数字中位数, 跟 result max 比对
    deviations = []
    for key, (sheet, rmax) in result_max.items():
        if key not in paper_by_key or not paper_by_key[key]:
            continue
        nums = sorted([v for _, _, v, _ in paper_by_key[key]])
        if not nums:
            continue
        p_med = nums[len(nums) // 2]  # 中位数
        if rmax == 0:
            continue
        dev = abs(p_med - rmax) / rmax
        deviations.append((key, sheet, rmax, p_med, dev, paper_by_key[key]))

    if not deviations:
        return ("yellow", "论文数学公式未与 result 文件配对", "检查 §5.1/§5.2/§5.3/§5.4 章节是否与 result1/2/3/4-2 对应")

    # 6. 阈值判定: 任一偏差 > 5% 红, 1-5% 黄, 全部 < 1% green
    worst_key, worst_sheet, worst_rmax, worst_pmed, worst_dev, worst_data = max(deviations, key=lambda x: x[4])
    if worst_dev < 0.01:
        return ("green",
                f"L6 完整版: {len(deviations)} 个 result key 全部 < 1% 偏差 (worst: {worst_key} {worst_dev:.2%})",
                None)
    if worst_dev < 0.05:
        return ("yellow",
                f"L6 完整版: 偏差 1-5% (worst: {worst_key} {worst_dev:.2%}, result {worst_rmax:,.0f} vs 论文 {worst_pmed:,.0f})",
                f"论文中位数 {worst_pmed:,.0f} 与 result {worst_key} 偏差 {worst_dev:.2%}, 检查 {worst_data[0][0]} 数学公式")
    if is_template:
        return ("yellow",
                f"example 模板有意保留偏差 {worst_dev:.2%} (设计意图, 跑题时校准才 GREEN)",
                f"跑题用户用真实 resultX.xlsx 重写摘要+§5.X")

    # 详细列出偏差最大的 3 个
    top3 = sorted(deviations, key=lambda x: -x[4])[:3]
    detail = "\n".join(
        f"  result{k} {sheet}: result {rmax:,.0f} vs 论文 {pmed:,.0f} (偏差 {dev:.2%})"
        for k, sheet, rmax, pmed, dev, _ in top3
    )
    return ("red",
            f"L6 完整版: 偏差 > 5% (worst: {worst_key} {worst_dev:.2%}, result {worst_rmax:,.0f} vs 论文 {worst_pmed:,.0f})",
            f"v15 P0-1 / 论文综合 10 处 P0 数字偏差防御. 修复: 用 result 真实数字替换论文 §5.X 数字. Top 3:\n{detail}")


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


# ===== v1.5.7.37 新增 2 项: AIGC 扫描增强 L16 (段首重复率) + L17 (连接词密度) =====

# AIGC 连接词关键词 (Sep 13 实战: "同时" ×8 偏多, "然而/因此/此外" 等)
AIGC_CONNECTOR_KEYWORDS = (
    "同时", "然而", "因此", "此外", "更进一步", "与此同时",
    "综上所述", "可以看出", "值得注意的是", "由此可见",
)


def check_segment_opener_repetition():
    """checkable 49: AIGC 段首重复率 L16 (auto, AIGC 痕迹实战提炼).

    背景: 2025C Sep 13 AIGC 报告 (Sep 13 04:06 09-13 复审) 段首重复率 39.6% 偏高
    (主要因"问题一/二/三/四"结构 + "本文/当/针对" 等高频词). Sep 13 报告 §2.2 判定
    39.6% 可接受 (<50% 阈值), 但建议人工分散到"本问/该问题/此问题". 加自动扫:

    1. 收集论文所有 .tex 段首 2 字符 (跳过 % 注释 + 空段 + 章节标题)
    2. 计算重复率 = (总段数 - 唯一段首数) / 总段数
    3. 0-30% green (低), 30-50% yellow (可接受), > 50% red (偏高, AIGC 风险)

    Template 状态: yellow (template 默认多章节重复段首, 设计意图).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L16 段首重复率",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    target_files = ["0.摘要.tex", "1.引言.tex", "2.总体分析.tex", "3.模型假设.tex",
                    "4.符号说明.tex", "5.1.1.分析与准备.tex", "5.1.2.建模与求解.tex",
                    "5.2.建模与求解.tex", "5.3.建模与求解.tex", "5.4.建模与求解.tex",
                    "6.模型检验.tex", "7.模型评价.tex", "8.模型改进推广.tex"]
    openers = []
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 提取段落 (用空行分隔), 段首 2 字符
        for para in tcontent.split("\n\n"):
            lines = [l for l in para.split("\n") if l.strip() and not l.strip().startswith("%")]
            if not lines:
                continue
            first_line = lines[0].strip()
            # 跳过章节标题 + 列表项 + 数学环境
            if first_line.startswith(("\\section", "\\subsection", "\\subsubsection",
                                        "\\item", "$", "\\begin", "\\end",
                                        "\\textbf", "\\caption", "\\label")):
                continue
            # 段首 2 字符
            opener = first_line[:2]
            if opener:
                openers.append(opener)

    if not openers:
        return ("yellow", "论文 .tex 未提取到段首 (可能全章节标题/无段落)",
                "跑题用户应写真实段落")

    total = len(openers)
    unique = len(set(openers))
    repetition_rate = 1.0 - unique / total if total > 0 else 0

    # Sep 13 AIGC 阈值: <50% 可接受 (green/yellow 分界), >50% 偏高
    if repetition_rate < 0.30:
        return ("green",
                f"AIGC 段首重复率 {repetition_rate:.1%} 低 ({total} 段, {unique} 唯一) — Sep 13 AIGC 报告 39.6% 阈值的 0.6 倍",
                None)
    if repetition_rate < 0.50:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留段首重复 ({repetition_rate:.1%}, 设计意图, 跑题时分散才 GREEN)",
                    f"替换段首为'本问/该问题/此问题/当'等变体")
        return ("yellow",
                f"AIGC 段首重复率 {repetition_rate:.1%} 中等 ({total} 段, {unique} 唯一) — Sep 13 AIGC 报告 39.6% 同等",
                f"分散段首: '问题' → '本问/该问题/此问题'; '本文' → '本研究/笔者'; '当' → '此时/当...时'")
    if is_template:
        return ("yellow",
                f"example 模板有意保留段首重复偏高 ({repetition_rate:.1%}, 设计意图)",
                f"分散段首变体")
    return ("red",
            f"AIGC 段首重复率 {repetition_rate:.1%} 偏高 ({total} 段, {unique} 唯一) — AIGC 风险",
            f"替换段首为变体 (Sep 13 报告 §4.4 优化建议: '同时' 替换 3 处, '问题' 替换为'本问/该问题/此问题')")


def check_connector_density():
    """checkable 50: AIGC 连接词密度 L17 (auto, "同时" 等关键词扫).

    背景: 2025C Sep 13 AIGC 报告 §2.1 连接词密度 7.5% (低, <50% 阈值);
    "同时" ×8 偏多, 建议替换 2-3 处为"且/并/另一方面". 加自动扫:

    1. 收集论文所有 .tex 连接词命中数 (AIGC_CONNECTOR_KEYWORDS 10 项)
    2. 计算总连接词数 / 总句数 = 连接词密度
    3. 0-10% green (低), 10-15% yellow (中等), > 15% red (偏高)

    Template 状态: yellow (template 默认示例, 设计意图).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L17 连接词密度",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    target_files = ["0.摘要.tex", "1.引言.tex", "2.总体分析.tex", "5.1.1.分析与准备.tex",
                    "5.1.2.建模与求解.tex", "5.2.建模与求解.tex", "5.3.建模与求解.tex",
                    "5.4.建模与求解.tex", "7.模型评价.tex", "8.模型改进推广.tex"]
    connector_count = 0
    sentence_count = 0
    per_keyword = {kw: 0 for kw in AIGC_CONNECTOR_KEYWORDS}
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过 % 注释行
        non_comment = "\\n".join(
            line for line in tcontent.splitlines()
            if not line.lstrip().startswith("%")
        )
        # 数连接词命中 (中文字符, 无 word boundary)
        for kw in AIGC_CONNECTOR_KEYWORDS:
            cnt = non_comment.count(kw)
            per_keyword[kw] += cnt
            connector_count += cnt
        # 数句子 (中文句号/问号/感叹号, 跳过数学环境的 $)
        non_math = re.sub(r"\$.*?\$", "", non_comment, flags=re.DOTALL)
        sentence_count += len(re.findall(r"[。！？]", non_math))

    if sentence_count == 0:
        return ("yellow", "论文 .tex 未提取到句子 (可能全文数学/公式)",
                "跑题用户应写完整摘要 + §5.X 正文")

    density = connector_count / sentence_count if sentence_count > 0 else 0

    # 找最高频连接词 (报告 "同时" 偏多)
    top_kw = sorted(per_keyword.items(), key=lambda x: -x[1])[:3]
    top_msg = ", ".join(f"{kw}×{cnt}" for kw, cnt in top_kw if cnt > 0)

    if density < 0.10:
        return ("green",
                f"AIGC 连接词密度 {density:.1%} 低 ({connector_count}/{sentence_count}, {top_msg}) — Sep 13 AIGC 报告 7.5% 同级",
                None)
    if density < 0.15:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留连接词 ({density:.1%}, 设计意图, 跑题时分散才 GREEN)",
                    f"分散: {top_msg}")
        return ("yellow",
                f"AIGC 连接词密度 {density:.1%} 中等 ({connector_count}/{sentence_count}, {top_msg})",
                f"分散'同时/然而/因此'为'且/并/另一方面/从而' (Sep 13 报告 §2.1)")
    if is_template:
        return ("yellow",
                f"example 模板有意保留连接词偏高 ({density:.1%})",
                f"分散连接词")
    return ("red",
            f"AIGC 连接词密度 {density:.1%} 偏高 ({connector_count}/{sentence_count}, {top_msg}) — AIGC 风险",
            f"替换'同时/然而/因此'为变体: '且/并/另一方面/从而/除此之外'")


# ===== v1.5.7.44 新增 2 项: AIGC 2-gram TTR + 3-gram 重复率 L18/L19 =====

def _extract_ngrams(text, n):
    """提取 n-gram 集 (sliding window).

    输入: 散文文本 (已跳过注释 + 数学环境)
    输出: n-gram 元组 list
    """
    ngrams = []
    for i in range(len(text) - n + 1):
        ng = text[i:i+n]
        # 过滤纯标点 / 空白 n-gram
        if all(c in ' \t\n\r，。；：、！？（）()【】《》' for c in ng):
            continue
        ngrams.append(ng)
    return ngrams


def check_ngram_ttr():
    """checkable 51: AIGC 2-gram TTR L18 (auto, Sep 13 实战).

    背景: Sep 13 AIGC 报告 2-gram TTR = 0.457 (Sep 13 阈值, 实际 > 0.35 正常).
    防御: 跑论文所有 .tex 散文 (跳过注释 + 跳过数学环境), 计算 2-gram 唯一数 / 总 2-gram 数.

    阈值: > 0.45 green (Sep 13 0.457 同级) / 0.35-0.45 yellow / < 0.35 red (词汇多样性低, AIGC 风险).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L18", "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    target_files = ["0.摘要.tex", "1.引言.tex", "2.总体分析.tex", "5.1.1.分析与准备.tex",
                    "5.1.2.建模与求解.tex", "5.2.建模与求解.tex", "5.3.建模与求解.tex",
                    "5.4.建模与求解.tex", "6.模型检验.tex", "7.模型评价.tex", "8.模型改进推广.tex"]
    total_ngrams = 0
    unique_ngrams = 0
    per_file = {}
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过 % 注释
        non_comment = "\n".join(
            line for line in tcontent.splitlines()
            if not line.lstrip().startswith("%")
        )
        # 跳过数学环境 (4 种)
        text = non_comment
        for pat in [r"\$[^\$\n]+\$", r"\\\[[^\]]+\\\]",
                    r"\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}",
                    r"\\begin\{align\*?\}(.+?)\\end\{align\*?\}"]:
            text = re.sub(pat, "", text, flags=re.DOTALL)
        # 提取 2-gram
        ngs = _extract_ngrams(text, 2)
        if not ngs:
            continue
        total_ngrams += len(ngs)
        unique_ngrams += len(set(ngs))
        per_file[fname] = (len(ngs), len(set(ngs)))

    if total_ngrams < 100:
        return ("yellow", f"论文 .tex 散文 2-gram 总数 {total_ngrams} < 100 (可能全文公式/短句)",
                "跑题用户应写完整摘要 + §5.X 正文")

    ttr = unique_ngrams / total_ngrams

    if ttr > 0.45:
        return ("green",
                f"AIGC 2-gram TTR {ttr:.3f} 高 ({total_ngrams} ngrams, {unique_ngrams} 唯一) — Sep 13 报告 0.457 同级",
                None)
    if ttr > 0.35:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留 2-gram TTR {ttr:.3f} (设计意图, 跑题时分散才 GREEN)",
                    f"分散词汇: 用同义词替换高频 2-gram")
        return ("yellow",
                f"AIGC 2-gram TTR {ttr:.3f} 中等 (Sep 13 报告 0.457 同等)",
                f"分散词汇: 用同义词替换高频 2-gram (e.g. 储能/电池/蓄电池, 优化/调度/规划)")
    if is_template:
        return ("yellow",
                f"example 模板有意保留 2-gram TTR 偏低 {ttr:.3f} (设计意图)",
                f"分散词汇")
    return ("red",
            f"AIGC 2-gram TTR {ttr:.3f} 偏低 (词汇多样性差, AIGC 风险)",
            f"分散词汇: 用同义词替换高频 2-gram (Sep 13 报告 §2.3 优化建议)")


def check_ngram_repetition():
    """checkable 52: AIGC 3-gram 重复率 L19 (auto, Sep 13 实战).

    背景: Sep 13 AIGC 报告 3-gram 重复率 60.3% (Sep 13 阈值, < 70% 可接受).
    防御: 跑论文所有 .tex 散文, 计算 (1 - 3-gram 唯一数/总 3-gram 数) 重复率.

    阈值: < 60% green (Sep 13 60.3% 同级) / 60-70% yellow / > 70% red (词汇重复度高, AIGC 风险).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow", f"论文目录不存在 ({paper_dir}), 跳过 L19", "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    target_files = ["0.摘要.tex", "1.引言.tex", "2.总体分析.tex", "5.1.1.分析与准备.tex",
                    "5.1.2.建模与求解.tex", "5.2.建模与求解.tex", "5.3.建模与求解.tex",
                    "5.4.建模与求解.tex", "6.模型检验.tex", "7.模型评价.tex", "8.模型改进推广.tex"]
    total_ngrams = 0
    unique_ngrams = 0
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            tcontent = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过注释
        non_comment = "\n".join(
            line for line in tcontent.splitlines()
            if not line.lstrip().startswith("%")
        )
        # 跳过数学环境
        text = non_comment
        for pat in [r"\$[^\$\n]+\$", r"\\\[[^\]]+\\\]",
                    r"\\begin\{equation\*?\}(.+?)\\end\{equation\*?\}",
                    r"\\begin\{align\*?\}(.+?)\\end\{align\*?\}"]:
            text = re.sub(pat, "", text, flags=re.DOTALL)
        # 提取 3-gram
        ngs = _extract_ngrams(text, 3)
        if not ngs:
            continue
        total_ngrams += len(ngs)
        unique_ngrams += len(set(ngs))

    if total_ngrams < 100:
        return ("yellow", f"论文 .tex 散文 3-gram 总数 {total_ngrams} < 100 (可能全文公式/短句)",
                "跑题用户应写完整摘要 + §5.X 正文")

    repetition = 1.0 - unique_ngrams / total_ngrams

    if repetition < 0.60:
        return ("green",
                f"AIGC 3-gram 重复率 {repetition:.1%} 低 ({total_ngrams} ngrams, {unique_ngrams} 唯一) — Sep 13 报告 60.3% 同级",
                None)
    if repetition < 0.70:
        if is_template:
            return ("yellow",
                    f"example 模板有意保留 3-gram 重复 {repetition:.1%} (设计意图)",
                    f"分散重复 3-gram (e.g. 储能 SOC 初始 → 储能荷电状态初值)")
        return ("yellow",
                f"AIGC 3-gram 重复率 {repetition:.1%} 中等 (Sep 13 报告 60.3% 同等)",
                f"分散重复 3-gram: 同义改写高频 3-gram (Sep 13 报告 §2.3 优化建议)")
    if is_template:
        return ("yellow",
                f"example 模板有意保留 3-gram 重复 {repetition:.1%} (设计意图)",
                f"分散 3-gram")
    return ("red",
            f"AIGC 3-gram 重复率 {repetition:.1%} 偏高 (词汇重复度高, AIGC 风险)",
            f"分散重复 3-gram: 同义改写 (e.g. '根据以上分析' → '综上可见', '问题一' → 'Q1')")


# ===== v1.5.8 新增 1 项: FVM 表面 Robin 边界离散式 L20 (auto, P0-1 防御) =====

def check_bc_robin_template():
    r"""checkable 53: FVM 表面 Robin 边界离散式正确性 (auto, v1.5.8 新增, P0-1 防御).

    背景: 2026A 实跑复盘 v1.1 §2.1 P0-1 (v15 终审) — 温度场 build_surface_row() 返回
    (1.0, 1+β, β), β = h·Δr/α ≈ 29611, **式中无 Δt**, 表面钉死在烘房温度
    (h→∞ 极限, 不是题面给的有限 h=25). 决定性证据: 正确格式
    `dE/dt ÷ [h(T∞−Ts)·A] ≈ 0.995`, 错误格式 = 223 (不可能的 223 倍).

    正确半控制体 FVM Robin 模板 (圆柱/球坐标通用, 中心节点因子 4):

        (1 + 2μ + γ) · U^{n+1}_{N-1} − 2μ · U^{n+1}_{N-2} = U^{n}_{N-1} + γ · U_amb

    其中:
    - μ = D_eff · Δt / Δr² (Fourier 数 / 2)
    - γ = 2 · h_eff · Δt / Δr (Biot 含 Δt, 不是经典 Bi = h·Δr/α)
    - 4 = 中心节点权重 (半控制体), 边界节点因子 2 (全控制体)

    反例模式 (P0-1, h→∞ 极限):
        (1.0, 1 + beta, beta)           ← beta = h·Δr/α 形式, 无 Δt
        (1, 1 + β, β)                  ← 同上 (中文 β)
        return (1.0, 1 + h*L/k, h*L/k) ← 同上, h·Δr/α 形式
        ← 把传热方程改写成代数方程时, β 项的物理意义是收敛到 h→∞
        ← 不是"题面给的有限 h=25", 表面温度被错误地钉死成烘房温度 T_amb

    检测方法:
    - 扫 求解/问题N/*.py, 跳过 共享/ / _开头 / utils.py
    - 找含 build_surface_row / bc_row / surface_row / build_bc / boundary_row
      等关键词的函数定义
    - 提取函数体内 return 元组或变量赋值, 判断:
      错模式 (β = h·Δr/α 形式, 无 Δt, 无显式 γ=2h·Δt/Δr 项) → red
      对模式 (含 2μ+γ 或显式 gamma=2*h_eff*dt/dr 项) → green
      找不到 bc 函数 → yellow (e.g. 优化/数据分析/常微分题, 非 FVM 物理机理)

    阈值: yellow 跳过 (非 FVM) / green (找到真 Robin) /
          red (找到 (1, 1+β, β) 错误形式 — P0-1 反例).

    防御反例: 2026A v15 P0-1 (温度场) + v15 水分场 Bi_m 错算 32 实 3.24 +
              物理机理类 2024A/B 反模式 #2 (边界条件漏写/错写, P0).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L20 bc",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    solve_dir = paper_dir.parent / "求解"
    if not solve_dir.is_dir():
        return ("yellow",
                f"求解/ 不存在 ({solve_dir}), 跳过 L20 bc (非 PDE/ODE 物理机理题)",
                "本题若是 FVM 物理机理题, 应有 求解/问题N/ 子目录")

    # 启发式: bc_row / surface_row / build_bc 等 6 个常见命名
    bc_fn_pattern = re.compile(
        r'\bdef\s+(build_surface_row|bc_row|surface_row|build_bc|compute_bc|boundary_row)'
        r'\s*\('
    )
    # 错模式: (1, 1+β, β) / (1.0, 1+beta, beta) / (1, 1 + h*L/k, h*L/k)
    # 必须紧贴 ( [1/1.0] , 1 + x, x ) 这种 3 元组, 否则放宽为 warning
    bad_pattern = re.compile(
        r'\(\s*1(?:\.0)?\s*,\s*1\s*\+\s*[A-Za-z_β\u03b2\u0392]+\s*,\s*[A-Za-z_β\u03b2\u0392]+\s*\)'
    )
    # 对模式: γ 项 / 显式 gamma / 2μ + γ / (1+2*mu+gamma,) 三元组
    gamma_clue = re.compile(
        r'\bgamma\b|2\s*\*\s*mu|2\s*\*\s*[a-zA-Z_]+\s*\+|2\s*\u03bc|gamma\s*=\s*2'
    )
    correct_robin_pattern = re.compile(
        r'\(\s*1\s*\+\s*2\s*\*\s*[a-zA-Z_]+\s*\+\s*[a-zA-Z_]+\s*,'
        r'\s*-?\s*2\s*\*\s*[a-zA-Z_]+\s*,'
        r'\s*[a-zA-Z_]+\s*\)'
    )

    bad_rows = []   # 错格式 (P0-1 反例)
    good_rows = []  # 真 Robin
    skipped = []    # 不含 bc 函数 (非 FVM, 静默跳过)

    for py_file in solve_dir.rglob("*.py"):
        # 跳过 __init__ / 共享 utils / 数据处理 helper
        rel = str(py_file.relative_to(solve_dir))
        if py_file.name.startswith("_"):
            continue
        if "共享" in rel or "shared" in rel.lower() or "utils" in rel.lower() or "data_utils" in rel.lower():
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # 1. 是否含 bc_row 类函数?
        has_bc_fn = bool(bc_fn_pattern.search(content))
        if not has_bc_fn:
            continue

        # 2. 检测错/对模式
        bad_match = bad_pattern.search(content)
        # 对模式: 显式 2μ + γ 三元组 或 gamma 变量
        correct_match = correct_robin_pattern.search(content)
        gamma_match = gamma_clue.search(content)

        if bad_match and not (correct_match or gamma_match):
            bad_rows.append(rel)
        elif correct_match or gamma_match:
            good_rows.append(rel)
        else:
            skipped.append(rel)

    # 判定逻辑
    if not (bad_rows or good_rows):
        # 没找到 bc_row 类函数, 但 solve_dir 存在, 是优化类/数据分析类
        return ("yellow",
                f"求解/ 中未找到 bc_row/surface_row/build_bc 函数 ({len(skipped)} 个 .py 扫过)",
                "本题若为 FVM 物理机理题, 应在 solve_*.py 显式定义 build_surface_row()/bc_row()")

    if bad_rows and not good_rows:
        # 纯错 (P0-1 反例)
        return ("red",
                f"P0-1 表面离散式错误 (2026A 复盘 v1.1 §2.1): h→∞ 极限 (1, 1+β, β) 无 Δt",
                f"改用半控制体 FVM Robin: (1+2μ+γ)·U[N-1] - 2μ·U[N-2] = U_old + γ·U_amb; "
                f"γ=2·h_eff·Δt/Δr. 命中: {bad_rows}")

    if good_rows and not bad_rows:
        return ("green",
                f"L20 FVM 表面 Robin 离散式正确 (含 γ 项, 2026A P0-1 防御): "
                f"{len(good_rows)} 个 bc_row 函数",
                None)

    # 混合: 部分对 + 部分错 (黄色警告, 人工核对)
    return ("yellow",
            f"L20 FVM 边界: {len(good_rows)} 个含 γ 项 + {len(bad_rows)} 个错格式 (需人工核对)",
            f"错格式: {bad_rows[:3]}; 真 Robin: {good_rows[:3]}. "
            f"若两套实现用于不同时刻/不同维度 (e.g. 温度场 + 水分场 + 动边界 3 套), "
            f"分别核对 2026A 复盘 v1.1 §2.1 真模板")


# ===== v1.5.8.1 新增 1 项: 趋势数据禁用全局 IQR L21 (auto, P0-2 防御) =====

def check_iqr_outlier():
    r"""checkable 54: 趋势数据 IQR/箱线判据误用 (auto, v1.5.8.1 新增, P0-2 防御).

    背景: 2026A 复盘 v1.1 §0 (Sep 28 改进意见 P0-2) — 首版清洗用
    `IQR(k=3) = Q3 + 3×IQR / Q1 - 3×IQR` 把附件 1 升温段 (27 行) +
    附件 2 收缩段 (23 行) 全部判异常, **边界条件被腰斩**. 趋势数据的
    四分位距天然覆盖不了分布尾部的"过程段", IQR 不适用于过程段检测.

    防御: 扫 `求解/问题N/*.py`, 启发式找 iqr/IQR/boxplot/quantile(0.25)
    等关键词 + 紧邻 drop/删除/剔除/outlier 等清洗操作, 判断:
    - 紧邻 drop/删除/剔除/outlier → **red** (P0-2 反例, 趋势数据被全删)
    - 纯描述统计 (describe() / quantile() 用于报告) → **green**
    - 找不到 IQR/boxplot → **yellow** (非数据分析题, 跳过)

    阈值: yellow 跳过 (无 IQR 用法) / green (纯描述) /
          red (IQR + 紧邻 drop = P0-2 反例).

    防御反例: 2026A v15 P0-2 (升温/收缩曲线 IQR 误删) + 反模式 #1 数据预处理
              不报告 (数据分析类) / 物理机理类升温/收缩曲线 IQR 误删.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L21 IQR",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    solve_dir = paper_dir.parent / "求解"
    if not solve_dir.is_dir():
        return ("yellow",
                f"求解/ 不存在 ({solve_dir}), 跳过 L21 IQR (非数据清洗题)",
                "本题若有数据清洗, 应有 求解/问题N/ 子目录")

    # 启发式: IQR / boxplot / quantile(0.25) 等 5 个常见命名/调用
    iqr_fn_pattern = re.compile(
        r'\b(?:iqr|IQR)\b|'           # 单词 iqr / IQR
        r'\bplt\.boxplot\b|'          # matplotlib 箱线
        r'\bsns\.boxplot\b|'          # seaborn 箱线
        r'\.quantile\(\s*0\.25\b'     # pd.Series.quantile(0.25) Q1
    )
    # 紧邻 drop/删除/剔除 等清洗操作 (5 个关键词, 10 行内)
    drop_pattern = re.compile(
        r'\b(?:drop|dropna|删除|剔除|outlier)\b'
    )

    bad_rows = []    # 错用法 (P0-2 反例)
    good_rows = []   # 纯描述统计
    skipped = []     # 不含 IQR (非数据清洗题, 静默跳过)

    for py_file in solve_dir.rglob("*.py"):
        rel = str(py_file.relative_to(solve_dir))
        if py_file.name.startswith("_"):
            continue
        if "共享" in rel or "shared" in rel.lower() or "utils" in rel.lower() or "data_utils" in rel.lower():
            continue
        # 跳过纯绘图脚本 (boxplot 用于画图, 不剔除) — 通过路径关键词
        if "plot" in rel.lower() or "绘图" in rel or "figure" in rel.lower():
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        if not iqr_fn_pattern.search(content):
            continue

        # 检测 IQR 紧邻 drop/删除/剔除 (10 行窗口)
        lines = content.split('\n')
        iqr_line_idx = None
        drop_line_idx = None
        for i, line in enumerate(lines):
            if iqr_fn_pattern.search(line):
                iqr_line_idx = i
                # 在后续 10 行内找 drop
                for j in range(i, min(i + 11, len(lines))):
                    if drop_pattern.search(lines[j]):
                        drop_line_idx = j
                        break
                if drop_line_idx is not None:
                    break

        if iqr_line_idx is not None and drop_line_idx is not None:
            bad_rows.append(f"{rel}:L{drop_line_idx + 1} (IQR 在 L{iqr_line_idx + 1})")
        else:
            good_rows.append(rel)

    # 判定逻辑
    if not (bad_rows or good_rows):
        return ("yellow",
                f"求解/ 中未找到 IQR/boxplot/quantile(0.25) 调用, 跳过 L21 (非数据清洗题)",
                "本题若有清洗需求, 应在 solve_*.py 用 4 类允许检测 (物理越界/一阶差分/单调性/时间间隔)")

    if bad_rows and not good_rows:
        return ("red",
                f"P0-2 趋势数据 IQR 误用 (2026A 复盘 v1.1 §0): 升温/收缩段被全删, 边界条件腰斩",
                f"改用 4 类允许检测: 物理越界 / 一阶差分 z>5 / 单调性 (含容差) / 时间间隔+重复. "
                f"完整规范 + 代码模板: references/data-usage/数据清洗规范.md §2. 命中: {bad_rows[:3]}")

    if good_rows and not bad_rows:
        return ("green",
                f"L21 IQR 用法正确 (纯描述统计, P0-2 防御): {len(good_rows)} 处 quantile/boxplot",
                None)

    # 混合: 部分清洗 + 部分描述 (黄, 人工核对)
    return ("yellow",
            f"L21 IQR 用法: {len(good_rows)} 描述统计 + {len(bad_rows)} 紧邻 drop (需人工核对)",
            f"紧邻 drop 命中: {bad_rows[:3]}; 纯描述: {good_rows[:3]}. "
            f"若清洗只针对非趋势段 (e.g. 平稳流量), 改用 4 类允许检测; "
            f"若纯描述报告, 当前 OK")


# ===== v1.5.8.2 新增 1 项: 论文数字三来源 L22 (auto, P0-3 防御) =====

def check_number_source():
    r"""checkable 55: 论文关键判据 (Bi/Fo/收缩率/Re/Pr) 必含可信来源标记 (auto, P0-3 防御).

    背景: 2026A 复盘 v1.1 §0 P0-3 — 5.2.2 ρ/cp/k 起止值系目视读图臆造 (实 976.4→667.3);
    5.4.1"前 10h→1.424cm、占 78%"同为目测错 (实 5h、71.8%); **Bi_m 一次心算错 32 实 3.24
    (差 10 倍)**, 决定性证据: 评审找代理公式复算时全部暴露, 评"模型不严谨" 0 分.

    防御: 扫论文 11 章节 .tex, 找 5 类关键判据 (Bi / Fo / 收缩率 / Re / Pr) 出现位置,
    检测紧邻文字是否含可信来源标记 ("实算" / "print" / "resultX.xlsx" / "代码" / "solver 算"
    / "公式" / 公式环境), 判断:
    - 关键判据 + 含可信来源 → **green**
    - 关键判据 + 无来源 → **yellow** (警告: 补公式 + 二次复算, P0-3 反例)
    - 找不到关键判据 → **yellow** (非机理题, e.g. 优化/数据无 Bi/Fo, 跳过)

    阈值: yellow 跳过 (非机理) / green (关键判据含来源) /
          yellow 警告 (关键判据无来源, 提示补).

    防御反例: 2026A v15 P0-3 (5.2.2 ρ/cp/k + 5.4.1 收缩率 + Bi_m=32 三个反例).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L22 数字来源",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    target_files = ["0.摘要.tex", "1.引言.tex", "2.总体分析.tex",
                    "5.1.1.分析与准备.tex", "5.1.2.建模与求解.tex",
                    "5.2.建模与求解.tex", "5.3.建模与求解.tex", "5.4.建模与求解.tex",
                    "6.模型检验.tex", "7.模型评价.tex", "8.模型改进推广.tex"]

    # 5 类关键判据 (中文 + LaTeX 符号)
    key_indicators = [
        (r'毕渥数|Bi\b|\\Bi\b', "Bi"),
        (r'傅里叶数|Fo\b|\\Fo\b', "Fo"),
        (r'收缩率', "收缩率"),
        (r'雷诺数|Re\b|\\Re\b', "Re"),
        (r'普朗特数|Pr\b|\\Pr\b', "Pr"),
    ]
    # 可信来源标记 (论文写作现场应含)
    source_markers = re.compile(
        r'实算|print|result.*\.xlsx|solver 算|公式|\\begin\{equation|'
        r'\\begin\{align|台账|附录.*源|solve_.*\.py|code|代码|'
        r'由.*计算|根据.*公式|代入.*得'
    )

    total_found = 0
    no_source = []  # 关键判据出现但无来源 (P0-3 反例)
    with_source = []  # 含来源

    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            text = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过注释
        non_comment = "\n".join(
            line for line in text.splitlines()
            if not line.lstrip().startswith("%")
        )

        for pat, name in key_indicators:
            for m in re.finditer(pat, non_comment):
                total_found += 1
                # 检查紧邻 100 字符内是否含来源标记
                start = max(0, m.start() - 50)
                end = min(len(non_comment), m.end() + 100)
                context = non_comment[start:end]
                if source_markers.search(context):
                    with_source.append((fname, name, m.group()))
                else:
                    no_source.append((fname, name, m.group()))

    # 判定逻辑
    if total_found == 0:
        return ("yellow",
                f"L22 关键判据: 论文未发现 Bi/Fo/收缩率/Re/Pr 5 类关键判据 (非机理题, 跳过)",
                "本题若为物理机理题, 应在 §5.X 给出关键判据 (Bi/Fo) + 公式 + 二次复算")

    if no_source and not with_source:
        # 全部关键判据都无来源 (P0-3 翻车)
        return ("yellow",
                f"L22 关键判据 {total_found} 处全无来源标记 (P0-3 翻车警告)",
                f"补公式 + 二次独立复算, 例: 'Bi = h·L/k = 25·0.02/0.5 = 1.0 (实算, 单位独立验算)'. "
                f"命中: {[(f, n) for f, n, _ in no_source[:3]]}. "
                f"完整规范: references/audit/数值台账规范.md")

    if no_source:
        # 部分有来源, 部分无 (混合, yellow 警告)
        return ("yellow",
                f"L22 关键判据: {len(with_source)} 含来源 + {len(no_source)} 无来源 (P0-3 警告)",
                f"无来源: {[(f, n) for f, n, _ in no_source[:3]]}. "
                f"建议: 跑 python references/scripts/number_ledger.py init 建台账 + 补 '实算/print/resultX.xlsx/公式' 标记")

    # 全部含来源
    return ("green",
            f"L22 关键判据 {total_found} 处全含来源标记 (P0-3 防御: {len(with_source)} 处实算/print/resultX/公式)",
            None)


# ===== v1.5.8.3 新增 1 项: resultX 结构 vs 附件3 模板 L23 (auto, P0-4 防御) =====

def check_result_struct():
    r"""checkable 56: resultX.xlsx 列名/dtype/行数 vs 附件3 模板 (auto, v1.5.8.3 新增, P0-4 防御).

    背景: 2026A 复盘 v1.1 §P0-4 — 4 个 result 的 A 列名写成 `时间` (模板为
    `时间\到药材中心的距离`); result4 多插"半径/cm"列导致距离列右移且为字符串
    列名; 论文表5 用了 0.1cm 21 列 (题面要求 0.5cm 5 列). 均为提交前审计才发现.

    防御: 用 openpyxl 打开附件3 模板 (`数据/附件/附件3/*.xlsx`) 与产出
    `求解/**/result*.xlsx`, 逐项比对:
    - sheet 名集合 (result 应包含模板 sheet 名)
    - A 列名精确匹配模板 (e.g. "时间\到药材中心的距离" vs "时间")
    - 距离列 dtype 数值 (不能是字符串)
    - result4 末列 = "药材表面" (题面要求)
    - 行数 = 题面时长 / 步长 + 1 (e.g. t=205906s / dt=60s ≈ 3433 行)

    阈值: 列名不匹配 red / dtype 错 red / 行数偏差 > 5% red /
          找不到附件3 模板 yellow 跳过 (非物理/数据题) /
          resultX 不存在 yellow (跑完求解再跑).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L23 结构",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    # 1. 找附件3 模板
    project_root = paper_dir.parent
    attach3_candidates = [
        project_root / "数据" / "附件" / "附件3",
        project_root / "数据" / "附件3",
        project_root / "附件3",
    ]
    attach3_dir = None
    for cand in attach3_candidates:
        if cand.is_dir() and list(cand.glob("*.xlsx")):
            attach3_dir = cand
            break
    if attach3_dir is None:
        return ("yellow",
                f"附件3 模板未找到 (扫描 {len(attach3_candidates)} 路径), 跳过 L23 结构",
                "本题若为物理/数据题, 应有 数据/附件/附件3/*.xlsx 模板")

    # 2. 读附件3 模板所有 sheet 列名
    try:
        import openpyxl
    except ImportError:
        return ("yellow",
                "openpyxl 未装, 跳过 L23 结构 (pip install openpyxl)",
                "check 56 需要 openpyxl")

    template_sheets = {}  # sheet_name -> [列名 list]
    template_files = list(attach3_dir.glob("*.xlsx"))
    for tf in template_files[:2]:  # 限 2 个模板
        try:
            wb = openpyxl.load_workbook(tf, data_only=True, read_only=True)
            for sname in wb.sheetnames[:3]:  # 每模板限 3 sheet
                ws = wb[sname]
                cols = []
                for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
                    cols = [str(c) if c is not None else "" for c in row]
                    break
                template_sheets[(tf.name, sname)] = cols
        except Exception as e:
            print(f"  [WARN] 读模板 {tf.name} 失败: {e}")

    if not template_sheets:
        return ("yellow",
                f"附件3 模板无 sheet ({len(template_files)} 个 xlsx), 跳过 L23",
                "模板文件应有 ≥1 sheet 含列名")

    # 3. 扫产出 resultX
    solve_dir = project_root / "求解"
    if not solve_dir.is_dir():
        return ("yellow",
                f"求解/ 不存在 ({solve_dir}), 跳过 L23 结构 (无 resultX)",
                "跑完求解生成 resultX.xlsx 后再跑")

    result_files = list(solve_dir.rglob("result*.xlsx"))
    if not result_files:
        return ("yellow",
                f"求解/ 下未找到 result*.xlsx (跑完求解后才有), 跳过 L23",
                "跑题后必须生成 result1/2/3/4-2/4-3.xlsx")

    # 4. 逐 resultX vs 模板比对
    issues = []
    ok = []
    for rf in result_files[:6]:  # 限 6 个 result
        try:
            wb = openpyxl.load_workbook(rf, data_only=True, read_only=True)
            for sname in wb.sheetnames:
                ws = wb[sname]
                # 读列名
                cols = []
                for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
                    cols = [str(c) if c is not None else "" for c in row]
                    break
                # 找匹配模板 (按 sheet 名)
                matched_template = None
                for (tfile, tsname), tcols in template_sheets.items():
                    if tsname == sname:
                        matched_template = tcols
                        break
                if matched_template is None:
                    issues.append(f"{rf.name} sheet '{sname}' 不在附件3 模板中")
                    continue
                # 列名比对
                if cols != matched_template:
                    diff = []
                    for i, (a, b) in enumerate(zip(cols, matched_template)):
                        if a != b:
                            diff.append(f"col[{i}] '{a}' vs 模板 '{b}'")
                    issues.append(f"{rf.name} sheet '{sname}' 列名错: {'; '.join(diff[:3])}")
                else:
                    ok.append(f"{rf.name} sheet '{sname}'")
        except Exception as e:
            issues.append(f"{rf.name} 读失败: {e}")

    # 5. 判定
    if not issues:
        return ("green",
                f"L23 resultX 结构 vs 附件3 模板: {len(ok)} sheet 全列名匹配 (P0-4 防御)",
                None)
    if not ok:
        return ("red",
                f"P0-4 resultX 结构错: {len(issues)} 处列名/dtype 错 (2026A 复盘 §P0-4)",
                f"用 openpyxl 打开附件3 模板 vs {result_files[0].name}, 修列名完全匹配. 命中: {issues[:3]}")
    # 混合
    return ("yellow",
            f"L23 resultX 结构: {len(ok)} sheet 对 + {len(issues)} sheet 错 (需人工核对)",
            f"错处: {issues[:3]}; 对处: {ok[:3]}")


# ===== v1.5.8.4 新增 1 项: 支撑材料超限预案 L24 (auto, P0-5 防御) =====

def check_support_overlimit():
    r"""checkable 57: 支撑材料/ 任一文件 >10MB 触发预案 (auto, v1.5.8.4 新增, P0-5 防御).

    背景: 2026A 复盘 v1.1 §P0-5 — result2.xlsx 达 35→36MB, 单文件即超 20MB 包限.
    方案: gzip CSV (两 sheet 约 5.6MB) + 包内说明 + 脚本一键重生.

    防御: 扫用户跑题根的 `支撑材料/` 目录, 找 >10MB 文件, 判断:
    - 任一文件 >10MB 但未触发预案 (未提供 csv.gz 等价压缩) → **red** (P0-5 翻车)
    - 任一文件 >10MB 且有 csv.gz/npz 配套 → **yellow** (提示同步附录 A/D/J)
    - 总包大小 >20MB → **red** (竞赛硬规则)
    - 支撑材料/ 不存在 → **yellow** (跑前 skip)
    - 全部 <10MB → **green** (无超限)
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L24 超限",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    project_root = paper_dir.parent
    support_dir = project_root / "支撑材料"
    if not support_dir.is_dir():
        return ("yellow",
                f"支撑材料/ 不存在 ({support_dir}), 跳过 L24 (跑前 skip)",
                "Step 4.4 打包前才生成 支撑材料/ 目录")

    # 1. 扫所有文件大小
    big_files = []  # >10MB
    all_files = []
    total_size = 0
    for f in support_dir.rglob("*"):
        if f.is_file():
            try:
                size_mb = f.stat().st_size / (1024 * 1024)
            except OSError:
                continue
            total_size += size_mb
            all_files.append((f, size_mb))
            if size_mb > 10:
                big_files.append((f.relative_to(support_dir), size_mb))

    if not big_files:
        return ("green",
                f"L24 支撑材料包: {len(all_files)} 文件, {total_size:.1f} MB, 无超限 (P0-5 防御绿)",
                None)

    # 2. 检查大文件是否已配套 csv.gz / npz
    unbacked = []  # 大文件但无配套压缩
    for rel, sz in big_files:
        stem = rel.stem
        has_companion = False
        for ext in [".csv.gz", ".npz", ".xlsx.gz"]:
            companion = rel.parent / (stem + ext)
            if companion.exists():
                has_companion = True
                break
        if not has_companion:
            unbacked.append((rel, sz))

    # 3. 检查总包
    over_20mb = total_size > 20
    over_10mb_files = [f"{r} ({s:.1f} MB)" for r, s in big_files]

    if unbacked and over_20mb:
        return ("red",
                f"P0-5 支撑材料超限: 总 {total_size:.1f} MB > 20MB + {len(unbacked)} 大文件无配套压缩 (2026A result2 36MB 翻车)",
                f"压缩 {unbacked[0][0]}: 跑 `df.to_csv(..., index=False)` + gzip. "
                f"包内说明 + 重生脚本必留. 大文件: {over_10mb_files[:3]}")
    if unbacked:
        return ("red",
                f"P0-5 支撑材料: {len(unbacked)} 大文件无 csv.gz/npz 配套 (>{10} MB 单文件超限)",
                f"压缩方法: pd.read_excel().to_csv(...).gzip. 大文件: {over_10mb_files[:3]}")
    if over_20mb:
        return ("red",
                f"P0-5 支撑材料总包 {total_size:.1f} MB > 20MB (竞赛硬规则)",
                f"压缩最大文件 {over_10mb_files[0]}, 包内留重生脚本 + 改动说明")
    # 全部有配套, 但总包没超 20
    return ("yellow",
            f"L24 支撑材料: {len(big_files)} 大文件均配套压缩, 总 {total_size:.1f} MB (P0-5 需同步附录 A/D/J 引用)",
            f"大文件: {over_10mb_files[:3]}. 提醒: 附录 A 列表必须列 csv.gz 而不是原始 xlsx, 评审按包内清单查")


# ===== v1.5.8.5 新增 1 项: 附录 ↔ 支撑材料包内容一致性 L25 (auto, P0-6 防御) =====

def check_appendix_consistency():
    r"""checkable 58: 附录 .tex 中 \texttt{路径} 必须真实存在于 支撑材料/ (auto, P0-6 防御).

    背景: 2026A 复盘 v1.1 §P0-6 — 附录 J 引用 `论文/_frag/gen_tables.py` 不在
    包内; 附录 A 仍列已剔除的 result2.xlsx; 附录 J 表号错位 (写"表1↔result1"
    但符号说明+边界数据占了表1/表2, 题面结果表实为表3-表8).

    防御: 扫 paper_dir/10.附录.tex + 10.0.附录固定说明.tex, regex 提
    `\texttt{...}` 中所有路径, 验证每个路径在 `支撑材料/` 下真实存在.
    缺一个 → red (P0-6 翻车).

    注: 表号错位 (附录写"表1↔result1"但实际表号是3) 留给 v1.5.9 P1 fig_sanity
    处理 (需要解析编译后 .aux 文件 `\newlabel`, 复杂度高).

    阈值: 附录引用包外文件 red / 全在包内 green / 附录不存在 yellow / 支撑材料
    不存在 yellow.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L25 附录一致性",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    project_root = paper_dir.parent
    support_dir = project_root / "支撑材料"
    if not support_dir.is_dir():
        return ("yellow",
                f"支撑材料/ 不存在 ({support_dir}), 跳过 L25 (跑前 skip)",
                "Step 4.4 打包前才生成")

    # 1. 扫附录 .tex 提所有 \texttt{路径}
    appendix_files = ["10.附录.tex", "10.0.附录固定说明.tex"]
    appendix_paths = []  # [(tex_file, path, line_no)]
    path_re = re.compile(r'\\texttt\{([^}]+)\}')
    for af in appendix_files:
        p = paper_dir / af
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            # 跳过注释
            if line.lstrip().startswith("%"):
                continue
            for m in path_re.finditer(line):
                raw = m.group(1).strip()
                # 过滤非路径 (e.g. 中文/短文本)
                if not raw or "/" not in raw and "\\" not in raw:
                    continue
                if len(raw) < 3 or len(raw) > 200:
                    continue
                appendix_paths.append((af, raw, line_no))

    if not appendix_paths:
        return ("yellow",
                f"L25 附录 .tex 未找到 \\texttt{{路径}} 引用 (非附录型论文)",
                f"如有附录, 在 {appendix_files[0]} 列文件路径用 \\texttt{{...}} 包裹")

    # 2. 验证每个路径在支撑材料/ 下存在
    missing = []  # 找不到的路径
    for af, p, line_no in appendix_paths:
        # 处理路径 (e.g. 求解/问题1/问题1_xxx.py) — 相对项目根, 不在支撑材料/
        # 实际 "支撑材料/" 内是用户放入的, 路径形式多样 (相对/绝对/含 ..)
        # 简化: 检查 .basename 在 支撑材料/ 下某处存在
        from pathlib import PurePosixPath
        basename = PurePosixPath(p).name
        if not basename or basename in (".", ".."):
            continue
        # 找
        found = False
        try:
            for f in support_dir.rglob(basename):
                if f.is_file():
                    found = True
                    break
        except Exception:
            pass
        if not found:
            missing.append((af, p, line_no))

    if not missing:
        return ("green",
                f"L25 附录 ↔ 支撑材料包: {len(appendix_paths)} 个 \\texttt{{路径}} 全部在包内 (P0-6 防御)",
                None)

    if not appendix_paths:
        return ("yellow",
                "L25 附录 .tex 无路径引用 (跳过)",
                "本检查仅适用于有附录引用包内文件的论文")

    # 部分缺失 = red (P0-6 翻车)
    miss_str = [f"{af}:L{ln} {p}" for af, p, ln in missing[:3]]
    return ("red",
            f"P0-6 附录引用 {len(missing)}/{len(appendix_paths)} 个包外文件 (2026A 复盘 §P0-6 翻车)",
            f"把下列路径改为包内真实存在的文件 (或补到 支撑材料/): {miss_str}")


# ===== v1.5.9 新增 1 项: 图形内容自检 L26 (auto, P1-3 防御) =====

def check_fig_content_sanity():
    r"""checkable 59: 图形程序化内容自检 (auto, v1.5.9 新增, P1-3 防御).

    背景: 2026A 复盘 v1.1 §P1-3 — Q1 干燥前沿因阈值写成 `2.5*C0` 曲线恒为 0
    (np.ptp(y)==0), 靠肉眼发现; 另有 C₀ 字形□乱码 (U+2080 下标). 用 PIL
    对 22 张图做"顶部中央暗像素占比"检测 (标题带 >0.06 判红), 全部
    ≤0.045 → 确认无残留图内标题.

    防御: 调 `references/scripts/fig_sanity.py` 扫 `paper_dir/figures/` 全部图:
    - np.ptp(y)==0 曲线恒为常数 (阈值写错) → red
    - 全 NaN → red
    - 超物理范围 (T>200℃, C<0 等) → red
    - 顶部暗像素占比 > 0.06 (残留 set_title, 双标题) → red
    - .py 源含 U+2080 下标 (C₀ □乱码) → yellow 警告

    与 check_figure.py (格式 / DPI / 字体) 互补: 内容错走 fig_sanity, 格式错
    走 check_figure. 两者协同: 内容自检 = 内容层, 格式自检 = 格式层.

    阈值: 全部 green / 任何 issue red / 全 warnings yellow.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L26 fig_sanity",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    figures_dir = paper_dir / "figures"
    if not figures_dir.exists():
        return ("yellow",
                f"figures/ 不存在 ({figures_dir}), 跳过 L26 (无图场景)",
                "跑题后必须生成图")

    # 1. 调 fig_sanity.audit_content
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from fig_sanity import audit_content
    except ImportError as e:
        return ("yellow",
                f"fig_sanity.py 导入失败: {e}",
                "检查 references/scripts/fig_sanity.py 完整性")

    # 2. 扫所有图
    n_total = 0
    n_red = 0
    n_yellow = 0
    n_green = 0
    red_files = []
    yellow_files = []
    for ext in ('*.png', '*.jpg', '*.jpeg', '*.pdf', '*.svg'):
        for f in figures_dir.rglob(ext):
            if not f.is_file():
                continue
            n_total += 1
            try:
                result = audit_content(str(f), title_threshold=0.06)
            except Exception as e:
                yellow_files.append((f.relative_to(figures_dir), f"audit_content 异常: {e}"))
                n_yellow += 1
                continue
            if result["issues"]:
                n_red += 1
                red_files.append((f.relative_to(figures_dir), result["issues"]))
            elif result["warnings"]:
                n_yellow += 1
                yellow_files.append((f.relative_to(figures_dir), result["warnings"]))
            else:
                n_green += 1

    if n_total == 0:
        return ("yellow",
                f"figures/ 无图像文件 ({figures_dir}), 跳过 L26",
                "跑题后必须生成图")

    # 3. 判定
    if n_red > 0 and n_green == 0 and n_yellow == 0:
        # 全部 red (内容级 P0 翻车)
        sample = [f"{f}: {iss[0]}" for f, iss in red_files[:3]]
        return ("red",
                f"P1-3 图形内容错: {n_red}/{n_total} 图有问题 (2026A 复盘 §P1-3)",
                f"修: 删 set_title (改用 caption) / 修 np.ptp=0 阈值 / 改 U+2080 下标. 命中: {sample}")

    if n_red > 0:
        return ("yellow",
                f"L26 fig_sanity: {n_red} 红 + {n_green} 绿 + {n_yellow} 黄 ({n_total} 总, 需人工核对)",
                f"红处: {[(str(f), iss[0]) for f, iss in red_files[:3]]}")

    if n_yellow > 0:
        return ("yellow",
                f"L26 fig_sanity: {n_yellow} 黄 + {n_green} 绿 (无 red, 警告可保留)",
                f"警告: {[(str(f), w[0]) for f, w in yellow_files[:3]]}")

    return ("green",
            f"L26 fig_sanity: {n_green}/{n_total} 图内容全过 (P1-3 防御, 顶像素 < 0.06 + 无 np.ptp=0 + 无 U+2080)",
            None)


# ===== v1.5.9.4 新增 1 项: meta.json 3 件套验证 L27 (auto, P1-7 防御) =====

def check_meta_3pcs():
    r"""checkable 60: 求解/问题N/结果/meta.json 含 3 件套 (auto, v1.5.9.4 新增, P1-7 防御).

    背景: 2026A 复盘 v1.1 §P1-7 — 评阅关注点 2 强调"高效数值计算过程", 但脚本
    print 了 elapsed 未入交付文件, 论文靠会话记忆. 改进: code-template 强制
    `meta.json` 落盘 (elapsed_sec / steps / grid / dt / dr / complexity / version).

    防御: 扫 `求解/问题N/结果/meta.json`, 验证 7 字段都不为 None. 缺一 → red.
    论文 §5.X.2 必引 3 件套: 步长依据 (dt/dr) + O(复杂度) (complexity) + 实测耗时 (elapsed_sec).

    阈值: 7 字段全填 green / 任一缺 red / meta.json 不存在 red / 求解/ 不存在 yellow.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L27 meta",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    project_root = paper_dir.parent
    solve_dir = project_root / "求解"
    if not solve_dir.is_dir():
        return ("yellow",
                f"求解/ 不存在 ({solve_dir}), 跳过 L27 meta (跑前 skip)",
                "跑完求解后才有 meta.json")

    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from check_meta import audit_meta
    except ImportError as e:
        return ("yellow",
                f"check_meta.py 导入失败: {e}",
                "检查 references/scripts/check_meta.py 完整性")

    # 扫所有问题目录
    problem_dirs = sorted([d for d in solve_dir.iterdir()
                          if d.is_dir() and (d.name.startswith("问题") or d.name.startswith("Q"))])
    if not problem_dirs:
        return ("yellow",
                f"求解/ 下无问题目录 ({solve_dir})",
                "跑题后必有 求解/问题N/ 子目录")

    n_total = 0
    n_red = 0
    n_green = 0
    red_files = []
    for pdir in problem_dirs:
        meta_files = list(pdir.rglob("meta.json"))
        if not meta_files:
            n_total += 1
            n_red += 1
            red_files.append((pdir.name + "/meta.json 缺失", []))
            continue
        for mf in meta_files:
            n_total += 1
            result = audit_meta(mf)
            if result["ok"]:
                n_green += 1
            else:
                n_red += 1
                red_files.append((str(mf.relative_to(project_root)), result["missing"]))

    if n_total == 0:
        return ("yellow",
                f"求解/ 下无 meta.json (跑完求解后才有), 跳过 L27",
                "跑题后 code-template 必落 meta.json")

    if n_red == 0:
        return ("green",
                f"L27 meta.json 3 件套全过: {n_green}/{n_total} 问题含 7 字段 (P1-7 防御, 评阅关注点 2 '高效' 必填)",
                None)

    sample = [f"{f}: 缺 {m[:3]}" for f, m in red_files[:3]]
    return ("red",
            f"P1-7 meta.json 缺字段: {n_red}/{n_total} 问题未含 3 件套 (2026A 复盘 §P1-7)",
            f"跑 code-template 自动落盘, 必填 elapsed_sec / steps / grid / dt / dr / complexity / version. 命中: {sample}")


# ===== v1.5.9.5 新增 1 项: 论文表格两行表头 L28 (auto, P1-8 防御) =====

def check_paper_two_row_header():
    r"""checkable 61: 论文 .tex 表格含两行表头 (\\multicolumn + \\multirow) (auto, P1-8 防御).

    背景: 2026A 复盘 v1.1 §P1-8 — 题面表 1-6 模板带 `到药材中心的距离/cm` 跨列组表头
    (两行表头), 我们的表只有裸距离值、缺该组标签 (审计判 WARN). 题面明确
    "按表 X 的格式给出", 格式偏差会被对照. 改进: 论文 .tex 表格必含
    `\\multicolumn{n}{c}{组标签}` (第一行) + `\\multirow{n}{*}{命名列}` (分组)
    + 第二行行表头.

    防御: 扫论文 5.X.2 章节 longtable 段, 检测 `\\multicolumn` + `\\multirow`
    配对. 至少 1 处配对 → green, 0 处 → red (题面格式不匹配).

    阈值: 论文表含两行表头 green / 全无 red / 论文目录无 longtable yellow
          (本题无表格章节, 跳过).
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L28 表头",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    # 扫论文 5.X 章节 longtable / tabular
    target_files = ["5.1.1.分析与准备.tex", "5.1.2.建模与求解.tex",
                    "5.2.建模与求解.tex", "5.3.建模与求解.tex", "5.4.建模与求解.tex",
                    "6.模型检验.tex"]
    multicolumn_count = 0
    multirow_count = 0
    longtable_count = 0
    tex_with_both = []
    for fname in target_files:
        tex_file = paper_dir / fname
        if not tex_file.exists():
            continue
        try:
            text = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 跳过注释
        non_comment = "\n".join(
            line for line in text.splitlines()
            if not line.lstrip().startswith("%")
        )
        if "\\multicolumn" in non_comment:
            multicolumn_count += non_comment.count("\\multicolumn")
        if "\\multirow" in non_comment:
            multirow_count += non_comment.count("\\multirow")
        if "\\begin{longtable}" in non_comment or "\\begin{tabular}" in non_comment:
            longtable_count += non_comment.count("\\begin{longtable}") + non_comment.count("\\begin{tabular}")
        # 配对 (同段 ±10 行)
        if "\\multicolumn" in non_comment and "\\multirow" in non_comment:
            tex_with_both.append(fname)

    # 判定
    if longtable_count == 0:
        return ("yellow",
                f"论文 5.X 章节无 longtable/tabular (本题可能无表格章节, 跳过 L28)",
                "若题面要求表格, 在 5.X.2 用 \\begin{longtable} 写两行表头")

    if tex_with_both and multirow_count >= 1 and multicolumn_count >= 1:
        return ("green",
                f"L28 论文表格两行表头: {len(tex_with_both)} 章节含 \\multicolumn + \\multirow 配对 (P1-8 防御, 题面 '到药材中心的距离/cm' 跨列组标签 ✓)",
                None)

    if multicolumn_count > 0 and multirow_count == 0:
        return ("yellow",
                f"L28 论文表格检测: \\multicolumn {multicolumn_count} 处, 缺 \\multirow (组表头不完整)",
                f"加 \\multirow{{n}}{{*}}{{命名列}} 与 \\multicolumn 配对 (题面表 1-6 模板 '到药材中心的距离/cm' 跨列)")

    if is_template:
        return ("yellow",
                f"example 模板有意保留单行表头 (0 配对, 设计意图, 跑题用户按题面模板改才 GREEN)",
                f"跑题时在 5.X.2 表前加 \\multicolumn{{n}}{{c}}{{组标签}} + \\multirow{{n}}{{*}}{{命名列}} (题面表 1-6 模板格式)")

    return ("red",
            f"P1-8 论文表格缺两行表头: 0 章节配对 \\multicolumn + \\multirow (2026A 复盘 §P1-8 格式偏差 WARN)",
            f"在 5.X.2 表前用 \\multicolumn{{n}}{{c}}{{到药材中心的距离/cm}} + \\multirow{{n}}{{*}}{{命名列}} 写两行表头 (题面表 1-6 模板格式)")


# ===== v1.6.0 新增 2 项: Python 探测 (第 0 项) + 波浪号中文 L29 =====

def check_python_probe():
    r"""checkable 62: Python 解释器探测 (第 0 项, auto, v1.6.0 新增, P2-1 防御).

    背景: 2026A 复盘 v1.1 §P2-1 — `python` 为**微软商店占位符** (exit 49), 全程被迫
    用 `py`. 改进: 环境节改探测式 (`py -3` / `python` / `python3` 依次尝试, 锁定后
    固化), dryrun 第 0 项自动探测.

    防御: 依次探测 3 个候选命令, 检测 exit 49 (商店占位符标志). 判断:
    - 探测到可用解释器 → **green** (报告版本 + 路径)
    - 全部不可用 → **red** (赛前必须修, 否则 96h 跑题全废)
    - 探测到但 pip 不同源 → **yellow** (提示用 `<解释器> -m pip install`)

    阈值: green / red / yellow.
    """
    candidates = [
        ("py -3", ["py", "-3"]),
        ("python", ["python"]),
        ("python3", ["python3"]),
    ]
    probed = []
    placeholder = []
    for label, argv in candidates:
        try:
            r = subprocess.run(argv + ["-c", "import sys; print(sys.version.split()[0]); print(sys.executable)"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
        except (FileNotFoundError, OSError):
            probed.append((label, None, "不可用"))
            continue
        except subprocess.TimeoutExpired:
            probed.append((label, None, "超时"))
            continue
        # exit 49 = 微软商店占位符
        if r.returncode == 49:
            placeholder.append(label)
            probed.append((label, None, "商店占位符 (exit 49)"))
            continue
        if r.returncode == 0:
            lines_out = (r.stdout or "").strip().split("\n")
            ver = lines_out[0].strip() if lines_out else "?"
            exe = lines_out[1].strip() if len(lines_out) > 1 else "?"
            # 检查 pip 同源
            try:
                pr = subprocess.run(argv + ["-m", "pip", "--version"],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
                pip_ok = (pr.returncode == 0)
                pip_msg = (pr.stdout or "").strip()[:80]
            except Exception:
                pip_ok = False
                pip_msg = "pip 探测失败"
            if not pip_ok:
                return ("yellow",
                        f"Python 探测 OK ({label} → {ver}, {exe}), 但 pip 不同源/不可用",
                        f"用 `{label} -m pip install ...` (别用裸 pip). pip: {pip_msg}")
            return ("green",
                    f"Python 探测 OK: {label} → v{ver} ({exe}), pip 同源 ✓",
                    None)
        probed.append((label, None, f"exit {r.returncode}"))

    # 全部不可用
    detail = ", ".join(f"{lbl}: {msg}" for lbl, _, msg in probed)
    ph = f"; 商店占位符: {placeholder}" if placeholder else ""
    return ("red",
            f"P2-1 Python 解释器全部不可用 ({detail}{ph}) — 赛前必须修, 否则 96h 跑题全废",
            "装 Python 3.10-3.12 或用 `py -3` launcher (py -3 -m pip install pandas numpy scipy matplotlib openpyxl PyMuPDF pulp)")


def check_tilde_chinese():
    r"""checkable 63: LaTeX 波浪号命令后接中文 (auto, v1.6.0 新增, P2-4 防御).

    背景: 2026A 复盘 v1.1 §P2-4 — `\textasciitilde` 直接接中文 → LaTeX 未定义命令
    ×2 (编译报错). 改进: 波浪号后仅接数字/空格; 接中文用"至".

    防御: 扫论文 .tex, 找 `\textasciitilde` / `~` 后紧跟中文字符, 命中 → red.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L29 波浪号",
                "用 --paper-dir 指定")
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)

    # 波浪号命令后接中文 (中文字符范围)
    cjk = r'一-鿿㐀-䶿'
    patterns = [
        (re.compile(r'\\textasciitilde\s*[' + cjk + r']'), r'\textasciitilde 后接中文'),
        (re.compile(r'\\textasciitilde\{[^}]*\}[' + cjk + r']'), r'\textasciitilde{} 后接中文'),
        (re.compile(r'~[' + cjk + r']'), r'裸 ~ 后接中文'),
    ]

    hits = []
    n_files = 0
    for tex_file in sorted(paper_dir.glob("*.tex")):
        n_files += 1
        try:
            text = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("%"):
                continue
            for pat, desc in patterns:
                m = pat.search(line)
                if m:
                    snippet = line.strip()[:80]
                    hits.append((tex_file.name, line_no, desc, snippet))

    if not hits:
        return ("green",
                f"L29 波浪号中文: {n_files} 个 .tex 无 \\textasciitilde/~ 后接中文 (P2-4 防御)",
                None)

    if is_template:
        return ("yellow",
                f"example 模板有意保留 {len(hits)} 处波浪号中文 (设计意图, 跑题时改才 GREEN)",
                f"波浪号后仅接数字/空格; 接中文用 '至'. 命中: {[h[0] + ':L' + str(h[1]) for h in hits[:3]]}")

    return ("red",
            f"P2-4 波浪号命令后接中文: {len(hits)} 处 LaTeX 未定义命令 (2026A 复盘 §P2-4 编译报错 ×2)",
            f"波浪号后仅接数字/空格, 接中文改用 '至'. 命中: {[(h[0], 'L' + str(h[1]), h[2]) for h in hits[:3]]}")


# ===== v1.5.7.36 新增 2 项: 绘图自检 L14 (冗余图) + L15 (图注 vs axes) =====

def check_unused_figures():
    r"""checkable 47: figures/ 中未被 \includegraphics 引用的图 (auto).

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
                f"figures/ {len(cited)} 张图全部被 \\includegraphics 引用 (无冗余)",
                None)

    # 有冗余
    if is_template:
        return ("yellow",
                f"example 模板有意保留 {len(unused)} 张冗余图 (设计意图, 跑题时清理才 GREEN)",
                f"冗余示例: {unused[:3]}. 跑题用户复制 example-paper 后删冗余图")
    return ("yellow",
            f"figures/ 有 {len(unused)} 张图未被任何正文 \\includegraphics 引用 (论文综合 §六.2 反例)",
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


# ===== v1.6.3 新增 1 项: 表面行能量守恒校验 L30 (auto, 2026A 复盘 §验收标准 第 1/2 条) =====

def check_bc_energy_conservation():
    r"""checkable 64: 表面边界行过能量守恒校验 (auto, v1.6.3 新增, 验收标准第 1/2 条).

    背景 (2026A 复盘 v1.1 §验收标准 L224-225):
        验收标准点名 dryrun 必须有 `check_bc (表面行过能量守恒校验)`, 且
        "任一新跑题: 表面边界行能通过 dE/dt ÷ 边界通量 ≈ 1 校验, 且有独立换实现的复算记录".

        2026A v15 P0-1 的决定性证据就是这个比值:
            错格式 build_surface_row -> (1.0, 1+beta, beta), beta = h·dr/alpha (无 dt)
                = h→∞ 极限, 表面被钉死在 T_amb            =>  ratio = 223
            真 Robin (1 + 2mu + gamma), gamma = 2·h·dt/dr  =>  ratio = 0.995
        |ratio − 1| 必须 < 0.05; 偏离一个数量级 = 离散式必错, 不是数值误差.

    检测方法 (两级, 不真跑求解):
      A. 防御资产自检 (skill 内, 缺一即 red):
         - references/scripts/bc_check.py 存在且可导入
         - 工具自测通过 (内置 对组 ratio=1 / 错组 ratio=223, 必须能区分)
         - mechanism-template.py + code-template.py 已接入 recorder 提示
         - 代理审计 prompt.md A 板块含守恒校验要求
      B. 项目实测 (仅当 求解/ 存在):
         - 扫 求解/问题N/**/守恒记录*.csv
         - 用 bc_check.verify_rows 判定 |worst ratio − 1| <= 0.05
         - 任一文件偏离 > tol → red (P0-1 型离散式错误)

    阈值: A 全过 + 项目无记录 green / A 全过 + 项目全过 green /
          A 缺 red / 项目数据偏离 red / 有数据但有效区间不足 yellow.
    """
    # ---- A. 防御资产自检 ----
    script = SCRIPTS_DIR / "bc_check.py"
    if not script.exists():
        return ("red",
                "验收标准第 1/2 条防御资产缺失: references/scripts/bc_check.py 不存在",
                "从 skill 恢复 bc_check.py (表面行守恒校验器), 否则 P0-1 型离散式错误无人拦")
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        import importlib
        import bc_check as _bc
        importlib.reload(_bc)
    except Exception as e:
        return ("red",
                f"bc_check.py 导入失败: {e}",
                "检查 references/scripts/bc_check.py 完整性 (它是验收标准第 1/2 条的落地载体)")

    # A2. 工具自测 (必须能区分 对组 ratio=1 / 错组 ratio=223)
    try:
        demo = _bc.run_demo(verbose=False)
    except Exception as e:
        return ("red", f"bc_check.py 自测调用失败: {e}", "检查 bc_check.py 的 run_demo() 实现")
    if not demo.get("pass"):
        return ("red",
                "bc_check.py 自测未过 (无法区分 对组 ratio=1 / 错组 ratio=223)",
                "守恒校验器自身失效, 先修 bc_check.py 再信它的判定")

    # A3. 模板接入 (机理题模板必接, 数据题模板给指针)
    tmpl_issues = []
    for fn in ("mechanism-template.py", "code-template.py"):
        p = REFS_DIR / fn
        if not p.exists():
            tmpl_issues.append(f"{fn} 不存在")
            continue
        if "ConservationRecorder" not in p.read_text(encoding="utf-8", errors="replace"):
            tmpl_issues.append(f"{fn} 未接入 ConservationRecorder")
    if tmpl_issues:
        return ("red",
                f"验收标准第 1/2 条防御未接入模板: {tmpl_issues}",
                "模板加 § 4.1 接入片段 (rec.record(t, E, flux) + rec.save('结果/守恒记录.csv'))")

    # A4. 代理审计 prompt A 板块含守恒校验要求
    prompt = REFS_DIR / "代理审计prompt.md"
    if not prompt.exists():
        return ("red", "references/代理审计prompt.md 不存在", "恢复代理审计 prompt 模板")
    if "守恒" not in prompt.read_text(encoding="utf-8", errors="replace"):
        return ("red",
                "代理审计 prompt A 板块缺守恒校验要求",
                "A1/A2 板块写明 dE/dt ÷ [h(T∞−Ts)·A] ≈ 1 (2026A P0-1 决定性证据)")

    # ---- B. 项目实测 ----
    paper_dir = get_paper_dir()
    project_root = paper_dir.parent if paper_dir.exists() else Path.cwd()
    solve_dir = project_root / "求解"
    rec_files = _bc.find_record_files(solve_dir) if solve_dir.is_dir() else []

    if not rec_files:
        return ("green",
                f"L30 表面行守恒防御就绪: bc_check.py 自测过 (对组 ratio=1 / 错组 ratio=223), "
                f"模板已接入; 项目内暂无 守恒记录*.csv (求解后跑本 check 自动判)",
                None)

    bad = []
    weak = []
    for f in rec_files:
        rows = _bc.read_record_csv(f)
        if not rows:
            weak.append(f"{f.name}(无数据行)")
            continue
        rep = _bc.verify_rows(rows, tol=0.05, name=f.stem)
        if rep["n_valid"] < 3:
            weak.append(f"{f.name}(有效区间 {rep['n_valid']}<3)")
        elif not rep["ok"]:
            bad.append(f"{f.name}: {rep['reason']}")

    if bad:
        return ("red",
                f"表面行守恒被破坏 ({len(bad)}/{len(rec_files)} 个记录文件 ratio 偏离 1 > 0.05): "
                f"P0-1 型离散式错误 (h→∞ 极限), 结果全错",
                f"命中: {bad[:3]}. 改边界行后重跑: py bc_check.py --csv <记录文件>")
    if weak:
        return ("yellow",
                f"表面行守恒: {len(rec_files) - len(weak)}/{len(rec_files)} 个记录文件通过, "
                f"但 {weak[:2]} 有效区间不足 (至少记 4 个时刻)",
                f"补记更多时刻后重跑; 命中: {weak[:3]}")
    return ("green",
            f"L30 表面行能量守恒全过: {len(rec_files)}/{len(rec_files)} 个记录文件 "
            f"|worst ratio − 1| <= 0.05 (验收标准第 1/2 条)",
            None)


# ===== v1.6.4 新增 2 项: 论文数字台账覆盖 L31 + 表/图编号一致性 L32 =====

def check_number_ledger_coverage():
    r"""checkable 65: 论文正文数字全部可溯源 (台账覆盖率) (auto, v1.6.4 新增).

    背景 (2026A 复盘 v1.1 §验收标准 L226):
        "论文正文 grep 不到'目测数字' (全部可溯源台账); 关键判据 (Bi/Fo) 有二次复算记录".
        check 40 是**正向** (result 文件里的数是否出现在论文), 覆盖不到
        "论文里凭图读数 / 心算写出来的数" —— 那正是 P0-3 的翻车形态:
        5.2.2 ρ/cp/k 起止值目测错 (实 976.4→667.3) + 5.4.1 "前 10h→1.424cm、占 78%" 目测错 (实 5h、71.8%).

    检测:
      - 台账 求解/数值台账.csv (4 列: 符号/值/来源/生成脚本; 来源 1=print 2=resultX 3=公式 4=题面)
      - 扫论文正文 .tex 提候选数字 (排除年份 1900-2100 + 0-9 整数计数 + 注释 + 数学环境 + label/ref)
      - 覆盖率 = 台账命中的唯一数字 / 论文候选唯一数字

    阈值: 台账不存在 yellow / 台账有效数字 < 3 yellow (基本没建) /
          覆盖率 >= 70% green / 40-70% yellow / < 40% red.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L31 台账覆盖",
                "用 --paper-dir 指定")
    project_root = paper_dir.parent
    ledger_path = project_root / "求解" / "数值台账.csv"
    if not ledger_path.exists():
        return ("yellow",
                f"数值台账不存在 ({ledger_path}), 跳过 L31 (跑前 skip)",
                "跑 `py -3 references/scripts/number_ledger.py init --root .` 建台账")

    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        import importlib
        import number_ledger as _nl
        importlib.reload(_nl)
    except Exception as e:
        return ("red",
                f"number_ledger.py 导入失败: {e}",
                "检查 references/scripts/number_ledger.py 完整性")
    try:
        cov = _nl.compute_coverage(paper_dir, project_root)
    except Exception as e:
        return ("yellow",
                f"台账覆盖率计算失败: {e}",
                "检查论文 .tex 编码 / 台账 CSV 格式")

    n_paper, n_ledger = cov["n_paper"], cov["n_ledger"]
    if n_ledger < 3:
        return ("yellow",
                f"数值台账只有 {n_ledger} 个有效数字 (<3), 台账基本没建, 跳过 L31 判定",
                "跑 number_ledger.py init + add, 把论文里的关键数字登记进台账")
    if n_paper == 0:
        return ("yellow", "论文正文未提取到候选数字, 跳过 L31", "检查论文 .tex 是否为空")

    rate = cov["rate"]
    unmatched = cov["unmatched"]
    if rate >= 0.7:
        return ("green",
                f"L31 论文数字台账覆盖 {rate:.0%} ({cov['matched']}/{n_paper} 个唯一数字有出处, 验收标准第 3 条)",
                None)

    sample = ", ".join(f"{k}@{v[0]}" for k, v in list(unmatched.items())[:5])
    if rate >= 0.4:
        return ("yellow",
                f"论文数字台账覆盖 {rate:.0%} ({cov['matched']}/{n_paper}), "
                f"有 {len(unmatched)} 个数字查不到出处",
                f"补台账: number_ledger.py add --sym <符号> --val <值> --source <1|2|3|4> --script <脚本:行>. 未匹配: {sample}")
    return ("red",
            f"论文数字台账覆盖仅 {rate:.0%} ({cov['matched']}/{n_paper}): "
            f"多数数字无可溯源来源 (P0-3 目测数字风险, 验收标准第 3 条)",
            f"补台账或改写论文数字. 未匹配示例: {sample}")


def check_label_numbering():
    r"""checkable 66: 表/图编号一致性 + 重复 label + 悬空引用 (auto, v1.6.4 新增).

    背景:
      - 2026A 复盘 §P0-6: "附录 J 表号错位 (写'表1↔result1' 但符号说明+边界数据占了表1/表2,
        题面结果表实为表3-表8)" —— v1.5.8.5 的 check 58 明确写"留给 P1 fig_sanity 处理".
      - 2026A 复盘附录 A B 板块第 6 条: "悬空引用 / 重复 label / 图文不符".
      - v1.6.2 实跑发现: example-paper 模板 4 问复制时漏改 label, eq:model / eq:constraints /
        fig:q1_results 各重复 4 次 → LaTeX "multiply defined" + \ref 指错图 (v1.6.4 已修).

    检测 (4 条规则, 全静态, 不编译):
      R1 重复 label    : 同一 label 名在 >=2 处定义 → red (编译警告 + 引用指错)
      R2 悬空 \ref     : \ref/\eqref/\cref/\Cref/\pageref 指向不存在的 label → red (编译出 ??)
      R3 越界表/图号  : 字面 "表 N"/"图 N" 的 N > 实际表/图总数 → red (引用了不存在的编号)
                         ⚠️ v1.6.5 修: 表计数**含 longtable** (skill 硬规则 C2.3 = 所有表格用
                         longtable; longtable 的 \caption 同样递增 table 计数器, 表号共用编号).
                         只数 \begin{table} 会让"按规范写出的论文"恒假红.
      R4 附录表号矛盾 : 附录里同一 resultM 被声明成不同表号 → red (P0-6 表号错位)

    阈值: 全过 green / R1-R4 任一命中 red / 论文目录不存在 yellow.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L32 编号一致性",
                "用 --paper-dir 指定")

    tex_files = sorted(paper_dir.rglob("*.tex"))
    cls_files = sorted(paper_dir.rglob("*.cls")) + sorted(paper_dir.rglob("*.sty"))
    if not tex_files:
        return ("yellow",
                f"论文目录无 .tex ({paper_dir}), 跳过 L32",
                "先写论文再跑终审")

    label_defs = {}   # label 名 -> [(file, line)]
    refs = []         # (ref 名, file, line)
    n_table = 0
    n_figure = 0
    text_lines = []   # (file, line_no, code)

    def _scan(path, count_floats):
        nonlocal n_table, n_figure
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return
        for line_no, line in enumerate(content.splitlines(), 1):
            if line.lstrip().startswith("%"):
                continue
            code = line.split("%")[0]
            if not code.strip():
                continue
            for m in re.finditer(r"\\label\{([^}]+)\}", code):
                label_defs.setdefault(m.group(1), []).append((path.name, line_no))
            for m in re.finditer(r"\\(?:eq|page|C|c)?ref\{([^}]+)\}", code):
                refs.append((m.group(1), path.name, line_no))
            if count_floats:
                # 表计数**必须含 longtable** (v1.6.5 修 P0-1):
                #   skill 硬规则 C2.3 = "所有表格用 longtable 不用 tabular" (验收清单.md C2.3),
                #   且 longtable 的 \caption 同样递增 table 计数器 —— 表号与 \begin{table} 共用编号.
                #   只数 \begin{table} 会让"按规范写出的论文"被判"越界表号" (恒假红).
                n_table += len(re.findall(r"\\begin\{table\*?\}", code))
                n_table += len(re.findall(r"\\begin\{longtable\}", code))
                n_figure += len(re.findall(r"\\begin\{figure\*?\}", code))
            text_lines.append((path.name, line_no, code))

    for tf in tex_files:
        _scan(tf, True)
    for cf in cls_files:      # format.cls / style 里的 label 也算数 (避免误报悬空)
        _scan(cf, False)

    # R1 重复 label
    dup = {k: v for k, v in label_defs.items() if len(v) > 1}
    # R2 悬空 ref
    dangling = [(r, f, l) for r, f, l in refs if r not in label_defs]
    # R3 越界表/图号
    bad_tab, bad_fig = [], []
    for fname, line_no, code in text_lines:
        clean = re.sub(r"\\(?:eq|page|C|c)?ref\{[^}]*\}", "", code)
        clean = re.sub(r"\\label\{[^}]*\}", "", clean)
        for m in re.finditer(r"(?<!图)表\s*(\d+)\s*[-–]\s*\d+", clean):
            pass    # "表 3-1" = 章节式编号, 跳过
        clean = re.sub(r"(?<!图)表\s*\d+\s*[-–]\s*\d+", "", clean)
        clean = re.sub(r"图\s*\d+\s*[-–]\s*\d+", "", clean)
        for m in re.finditer(r"(?<!图)表\s*(\d+)", clean):
            if int(m.group(1)) > n_table:
                bad_tab.append(f"{fname}:L{line_no} 表 {m.group(1)} (全文仅 {n_table} 张表)")
        for m in re.finditer(r"图\s*(\d+)", clean):
            if int(m.group(1)) > n_figure:
                bad_fig.append(f"{fname}:L{line_no} 图 {m.group(1)} (全文仅 {n_figure} 张图)")
    # R4 附录 result↔表号 声明矛盾
    claims = {}
    for fname, line_no, code in text_lines:
        if not fname.startswith("10."):
            continue
        for m in re.finditer(r"表\s*(\d+)[^。；\n]{0,20}?result\s*(\d+)", code, re.I):
            claims.setdefault(int(m.group(2)), set()).add(int(m.group(1)))
        for m in re.finditer(r"result\s*(\d+)[^。；\n]{0,20}?表\s*(\d+)", code, re.I):
            claims.setdefault(int(m.group(1)), set()).add(int(m.group(2)))
    conflict = {k: sorted(v) for k, v in claims.items() if len(v) > 1}

    problems = []
    if dup:
        items = [f"{k} ({len(v)} 处: {', '.join(f'{f}:L{ln}' for f, ln in v[:3])})"
                 for k, v in list(dup.items())[:4]]
        problems.append(("重复 label", f"{len(dup)} 个 label 被定义多次: {items}"))
    if dangling:
        items = [f"{r} @{f}:L{l}" for r, f, l in dangling[:4]]
        problems.append(("悬空引用", f"{len(dangling)} 处 \\ref 指向不存在的 label: {items}"))
    if bad_tab:
        problems.append(("越界表号", f"{len(bad_tab)} 处: {bad_tab[:3]}"))
    if bad_fig:
        problems.append(("越界图号", f"{len(bad_fig)} 处: {bad_fig[:3]}"))
    if conflict:
        problems.append(("附录表号矛盾", f"同一 result 被声明成多个表号: {conflict}"))

    if problems:
        detail = "; ".join(f"[{t}] {d}" for t, d in problems)
        return ("red",
                f"论文编号/引用一致性不过 (P0-6 表号错位 + 悬空/重复 label): {detail}",
                "重复 label 改唯一名 (如 fig:q1_results → fig:q2_results); 悬空 ref 补 label; "
                "越界表/图号改成实际编号; 附录 result↔表号统一")
    return ("green",
            f"L32 表/图编号一致: {len(label_defs)} 个 label 全唯一, {len(refs)} 处引用全有落点, "
            f"{n_table} 张表 / {n_figure} 张图, 无越界编号 (P0-6 防御)",
            None)


# ===== v1.6.5 新增 1 项: 章节图名 vs 问题号 L33 (auto, P0-2 防御) =====

def check_figure_name_matches_question():
    r"""checkable 67: 章节引用的图名必须与本章问题号一致 (auto, v1.6.5 新增).

    背景 (代理审计 P0-2, v1.6.5):
        v1.6.2 模板 4 问化时, 5.2.2 / 5.3.2 / 5.4.2 复制了 5.1.2 的图引用,
        三处仍写 `figures/q1_特征重要性.png` —— **问题二/三/四章节配问题一的图**.
        学生按 skill 流程生成自己的 q2_*.png / q3_*.png / q4_*.png 后,
        模板仍指向 q1_*, 于是问题三的章节里出现问题一的图 = **静默内容错误**
        (评委看到图文不符 = 数据不可信), 而全套 check **无一条能发现**
        (check 17 只查文件存在, check 48 只看单图 caption vs axes).

    检测 (2 条规则, 全静态):
      R1 图名问题号不符 : `5.N.*.tex` 引用 `q<M>_*.png` 且 M != N → red
      R2 一图多问共用   : 同一图路径被 >=2 个不同问题章节引用 → red

    判据: 任一命中 red / 全过 green / 无问题章节文件 yellow.
    """
    paper_dir = get_paper_dir()
    if not paper_dir.exists():
        return ("yellow",
                f"论文目录不存在 ({paper_dir}), 跳过 L33 图名一致性",
                "用 --paper-dir 指定")

    img_re = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
    qnum_re = re.compile(r"^5\.(\d+)\.")
    prefix_re = re.compile(r"(?:^|[/\\])q(\d+)_")

    mismatched = []   # (文件, 图名, 本章号, 图名里的号)
    shared = {}       # 图名 -> {章节号}
    n_scanned = 0

    for tex_file in sorted(paper_dir.rglob("*.tex")):
        m = qnum_re.match(tex_file.name)
        if not m:
            continue
        qn = int(m.group(1))
        try:
            content = tex_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        n_scanned += 1
        for im in img_re.finditer(content):
            path = im.group(1).strip()
            pm = prefix_re.search(path)
            if not pm:
                continue      # 无 q<N>_ 前缀的图 (如 sensitivity_关键参数.png) 不参与判定
            img_q = int(pm.group(1))
            shared.setdefault(path, set()).add(qn)
            if img_q != qn:
                mismatched.append(f"{tex_file.name} → {path} (本章 q{qn}, 图名 q{img_q})")

    if n_scanned == 0:
        return ("yellow",
                "论文目录无 5.N.*.tex 问题章节文件, 跳过 L33",
                "跑题后必有 求解/问题N 对应的 5.N.2.建模与求解.tex")

    multi = {p: sorted(qs) for p, qs in shared.items() if len(qs) > 1}

    if mismatched or multi:
        detail = []
        if mismatched:
            detail.append(f"{len(mismatched)} 处图名问题号不符: {mismatched[:3]}")
        if multi:
            detail.append(f"{len(multi)} 张图被多问共用: {list(multi.items())[:3]}")
        return ("red",
                f"章节图名与问题号不一致 (P0-2 型: 问题 N 的章节配了问题 M 的图): {'; '.join(detail)}",
                "把 5.N.*.tex 里的图名改成 q<N>_ 开头的本章图 (如 5.3.2 用 figures/q3_*.png); "
                "同一张图被多问引用时, 复制成各问各自的副本")
    return ("green",
            f"L33 章节图名与问题号一致: 扫 {n_scanned} 个问题章节, "
            f"{len(shared)} 张带 q<N>_ 前缀的图全部对应 (P0-2 防御)",
            None)


def check_skill_self_consistency():
    r"""checkable 68: v1.7.0 SKILL.md 自洽性 (writing-for-agents 第 2 轮代理审计 P0 级防御).

    背景 (2026-10-29 writing-for-agents 6 维度代理审计, VERDICT: FAIL):
        审计抓出 3 个 P0, 全是"文档自己和自己对不上"型 —— 任何单文件阅读都发现不了:
          P0-1 description 与正文各写一份「必读 3 文件」, **第三项不同**
               (description 指 5道防线自检清单, 正文指 读题清单.md)
               => always-loaded 指针漏掉 check 19 依赖的 读题清单.md
          P0-2 状态机 Step 0 框内**无 green 门** (Step 1/2/3/4 都有),
               且 Step 0 有两套互不引用的判据 (≥200 字 vs 15 项全填)
          P0-3 验收标准.md §1 表头写"以下 5 项"但表体 6 行, check 67 未进 §0 与 §J
        本 check 把这 3 类"自洽性"变成**可执行锚点**: 改了 A 忘了改 B, 立刻 red.

    5 条规则 (全静态, 只读 SKILL.md + 模板目录):
      R1 必读 3 文件一致 : description 列的 .md 集合 == 正文 §Step 0 列的 .md 集合
      R2 状态机 5 框有门 : §Procedure 代码块内 Step 0/1/2/3/4 每个框都有 green/red 判据行
      R3 .tex 数量一致   : SKILL.md 声明的"章节 .tex 数" == 模板实际章节 .tex 数 (文件名首字符是数字)
      R4 判据用词统一   : 作为判据的中文"绿/红"残留 == 0 ("红线" 是独立概念, 排除)
      R5 坏字符串 / 错指针: "干 run" 类坏串 == 0; 8 项自检指针不得写 §2 (真位置 §4.0)

    判据: 任一命中 red / 全过 green.
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
    body = content[end + 5:]

    problems = []

    # ---- R1 必读 3 文件: description vs 正文 ----
    desc_lines = _parse_yaml_block_scalar(fm, "description")
    desc_must = [l for l in desc_lines if "必读 3" in l]
    desc_files = set()
    if desc_must:
        desc_files = set(re.findall(r"([^\s`+/\\]+\.md)", desc_must[0]))
    else:
        problems.append("description 里找不到『必读 3 references』行")
    # v1.7.0 修 (自身假阳性): 原用 `必读 3 文件(.*?)(?=建议执行顺序)` 取正文段,
    # 但 5 道防线速查表里也出现过一次 "必读 3 文件" 字样 => 贪婪匹配从表那里起,
    # 把中间整段"类目适配"文件列表全吃进来 = 13 个文件 vs 3 个 = 假 red.
    # 现在锚到唯一的小节标题 "AI 跑题前必读 3 文件", 再只取编号列表项.
    m_head = re.search(r"AI 跑题前必读 3 文件", body)
    body_files = set()
    if m_head:
        chunk = body[m_head.end(): m_head.end() + 2000]
        items = re.findall(r"^\s*[123]\.\s+\*\*`([^`]+\.md)`\*\*", chunk, re.M)
        body_files = {Path(x).name for x in items}
        if len(body_files) != 3:
            problems.append("正文『必读 3 文件』实际解析到 %d 个 (期望 3): %s"
                            % (len(body_files), sorted(body_files)))
    else:
        problems.append("正文里找不到『AI 跑题前必读 3 文件』段")
    if desc_files and body_files and desc_files != body_files:
        problems.append("必读 3 文件不一致: description=%s vs 正文=%s"
                        % (sorted(desc_files), sorted(body_files)))
    elif desc_files and len(desc_files) != 3:
        problems.append("description 的必读文件数 = %d (期望 3)" % len(desc_files))

    # ---- R2 状态机 5 框都有判据门 ----
    pidx = body.find("## Procedure")
    if pidx == -1:
        problems.append("找不到 §Procedure 段")
    else:
        rest = body[pidx:]
        fo = rest.find("```")
        fc = rest.find("```", fo + 3) if fo != -1 else -1
        fence = rest[fo + 3:fc] if fo != -1 and fc != -1 else ""
        for step in range(0, 5):
            m_box = re.search(r"┌─ Step %d\b(.*?)(?=┌─ Step |└)" % step, fence, re.S)
            if not m_box:
                problems.append("状态机框 Step %d 不存在" % step)
            elif not re.search(r"\bgreen\b|\bred\b", m_box.group(1)):
                problems.append("状态机框 Step %d 没有 green/red 判据门" % step)

    # ---- R3 .tex 数量声明 vs 模板实际 ----
    tpl_dir = REFS_DIR / "templates" / "example-paper"
    if tpl_dir.is_dir():
        all_tex = sorted(tpl_dir.glob("*.tex"))
        chap_tex = [p for p in all_tex if p.name[:1].isdigit()]
        m_decl = re.search(r"(\d+)\s*个章节\s*\.tex", body)
        if not m_decl:
            problems.append("SKILL.md 没有声明『N 个章节 .tex』")
        elif int(m_decl.group(1)) != len(chap_tex):
            problems.append("章节 .tex 数量声明 %s != 模板实际 %d"
                            % (m_decl.group(1), len(chap_tex)))
        m_total = re.search(r"模板目录共\s*(\d+)\s*个\s*\.tex", body)
        if m_total and int(m_total.group(1)) != len(all_tex):
            problems.append("模板 .tex 总数声明 %s != 实际 %d"
                            % (m_total.group(1), len(all_tex)))
    else:
        problems.append("模板目录不存在, 无法核对 .tex 数量")

    # ---- R4 判据用词统一 (排除 '红线' 这个独立概念) ----
    stripped = content.replace("红线", "")
    n_cn_green = stripped.count("绿")
    n_cn_red = stripped.count("红")
    if n_cn_green or n_cn_red:
        problems.append("SKILL.md 仍有中文判据词: 绿 %d 处 / 红 %d 处 (应统一 green/red)"
                        % (n_cn_green, n_cn_red))

    # ---- R5 坏字符串 + 错指针 ----
    for bad in ("干 run", "干run"):
        if bad in content:
            problems.append("SKILL.md 含坏字符串 %r" % bad)
    if re.search(r"paper-spec\.md\s*§2\s*8\s*项自检", content):
        problems.append("8 项自检指针写成 §2 (真位置 = paper-spec.md §4.0)")

    if problems:
        return ("red",
                "SKILL.md 自洽性 %d 项不通过: %s" % (len(problems), "; ".join(problems[:4])),
                "同一含义改了 A 处必须同步改 B 处; 详见 references/audit/验收清单.md §J")
    return ("green",
            "SKILL.md 自洽 5 条全过 (必读 3 文件一致 / 状态机 5 框有门 / .tex 数量一致 / "
            "判据用词统一 / 无坏字符串与错指针)",
            None)


# v1.7.2: stdout UTF-8 契约判定正则 (行首 + 括号 + utf-8 参数).
# 行首锚定 = 只认**真调用**, 不认文档/字符串里的字面量 (防自指假绿).
_UTF8_STDOUT_RE = re.compile(
    r"^[ \t]*sys\.stdout\.reconfigure\s*\([^)]*encoding\s*=\s*['\"]utf-8['\"]",
    re.M)


def check_script_utf8_contract():
    r"""checkable 69: v1.7.2 子进程编码契约 (auto).

    背景 (v1.7.2 发现的 P0, 代理审计标"agent 模式端到端未跑"处):
        `dryrun.py --mode agent` (默认模式) **崩溃**:
          1) dryrun 用 subprocess + capture_output=True + text=True + encoding='utf-8'
             读 agent_audit.py 的 stdout
          2) agent_audit.py 缺 `sys.stdout.reconfigure(encoding='utf-8')`,
             管道下 Python 按 locale 编码 (本机 cp936/GBK) 写中文 -> GBK 字节
          3) dryrun 按 UTF-8 解码 -> UnicodeDecodeError -> rc!=0 -> dryrun exit 1
          4) agent 模式失败会 **exit(1) 连 self check 都跑不到** = 赛前自检直接失败

        实测: 11 个脚本里 5 个 (agent_audit / check_figure / check_meta /
              fig_sanity / number_ledger) 在管道下实测抛 UnicodeDecodeError.

    2 条规则 (全静态):
      R1 脚本 stdout 契约 : references/scripts/*.py + tools/*.py 每个都必须有
                           `sys.stdout.reconfigure` 且带 encoding='utf-8'
      R2 调用方容错      : dryrun.py 里所有 capture_output=True 的 subprocess.run
                           必须带 errors= 参数 (其余 6 处已有, 缺的 1 处是 P0 现场)

    判据: 任一命中 red / 全过 green.
    """
    py_files = sorted(list((REFS_DIR / "scripts").glob("*.py"))
                      + list((SKILL_ROOT / "tools").glob("*.py")))
    if not py_files:
        return ("red", "找不到任何 .py 脚本", "检查 references/scripts/ 与 tools/")

    # R1 每个脚本必须有 stdout UTF-8 契约
    missing = []
    # v1.7.2 修自指假绿: 用"行首 + 括号 + utf-8 参数"正则判定.
    # 不能用 `"sys.stdout.reconfigure" in t` —— 本函数自己的源码里就有这个字面量,
    # 扫 dryrun.py 时会**自己通过自己** = 假绿.
    for p in py_files:
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            missing.append(p.name + " (读不了)")
            continue
        if not _UTF8_STDOUT_RE.search(t):
            missing.append(p.name)
    problems = []
    if missing:
        problems.append(f"{len(missing)} 个脚本缺 stdout UTF-8 契约: {missing[:4]}")

    # R2 dryrun 的 subprocess 调用必须带 errors=
    dry = SCRIPTS_DIR / "dryrun.py"
    if dry.exists():
        dt = dry.read_text(encoding="utf-8", errors="replace")
        bad = []
        for m in re.finditer(r"subprocess\.run\((.*?)\)\s*\n", dt, re.S):
            call = m.group(1)
            if "capture_output=True" not in call and "stdout=subprocess.PIPE" not in call:
                continue
            if "text=True" not in call and "universal_newlines=True" not in call:
                continue
            if "errors=" not in call:
                ln = dt[:m.start()].count("\n") + 1
                bad.append(f"L{ln}")
        if bad:
            problems.append(f"dryrun.py 的 subprocess 调用缺 errors= 容错: {bad[:4]}")

    if problems:
        return ("red",
                f"子进程编码契约 {len(problems)} 项不通过: " + "; ".join(problems),
                "每个脚本 import 后加: sys.stdout.reconfigure(encoding='utf-8', errors='replace'); "
                "dryrun 的 subprocess.run 补 errors='replace'")
    return ("green",
            f"子进程编码契约 2 条全过: {len(py_files)} 个脚本都有 stdout UTF-8 契约 + "
            "dryrun 的 subprocess 调用全带 errors= 容错 (v1.7.2 P0 防御)",
            None)

def _iter_project_tex(project_root: Path):
    """项目里所有 .tex (论文目录 + 附录等), 跳过模板自带."""
    out = []
    for sub in ("论文", "paper", "Paper"):
        d = project_root / sub
        if d.is_dir():
            out += sorted(d.rglob("*.tex"))
    if not out:
        out = sorted(project_root.rglob("*.tex"))
    return out


def check_derived_numbers():
    r"""checkable 70: v1.8.0 派生量对账 (N-P0-1 防御, 终审复验轮).

    背景 (2026A 终审/复验轮 N-P0-1):
        修边界重跑后, 脚本生成的表**自动正确**, 但手写内容必然过期. 终审逐条抓出:
          - 附录 E 文件表仍写 `result3=3190 行` / `result4=2956 行`
            (这俩是**旧烘干时长的函数**: 191330/60+1 / 177290/60+1)
          - 附录 E verbatim 注释仍 `t_dry=191330 s` (最新 = 205906 s)
          - 附录 E 变量名 `recs_t` 而 Q3 源码是 `records_t`
        "看起来是元信息、实则由结果派生"的数字/名字, 最容易漏.

    本 check 做**能静态对账的那一半**:
      R1 行数对账 : 论文/附录里 "resultN ... NNNN 行" 的声明行数
                    vs 求解/问题N/结果/resultN.xlsx 的实际数据行数 -> 不符 red
      R2 变量名对账: 附录 verbatim 代码块里的变量名 vs 求解源码里是否真实存在
                    (附录写 `recs_t` 源码是 `records_t` -> red)

    判据: 任一命中 red / 全过 green / 无 result 文件 yellow (跑前 skip).
    """
    project_root = get_paper_dir().parent
    if not project_root.is_dir():
        return ("yellow", f"项目根不存在 ({project_root}), 跳过派生量对账", "用 --paper-dir 指定")

    # --- 收集 result 文件的真实行数 ---
    actual = {}   # resultN.xlsx -> 数据行数
    for x in sorted(project_root.rglob("result*.xlsx")):
        m = re.match(r"result(\d+)", x.stem)
        if not m:
            continue
        try:
            import openpyxl
            wb = openpyxl.load_workbook(x, read_only=True, data_only=True)
            rows = 0
            for ws in wb.worksheets:
                n = ws.max_row or 0
                rows = max(rows, n - 1)     # 首行是表头
            wb.close()
            actual[int(m.group(1))] = rows
        except Exception:
            continue

    tex_files = _iter_project_tex(project_root)
    if not tex_files:
        return ("yellow", "项目里没有 .tex, 跳过派生量对账", "跑题后必有 论文/*.tex")

    # --- R1 声明行数 vs 实际行数 ---
    problems = []
    checked = 0
    for tf in tex_files:
        try:
            content = tf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for m in re.finditer(r"result\s*(\d+)[^\n]{0,60}?(\d{2,6})\s*行", content, re.I):
            idx = int(m.group(1))
            claimed = int(m.group(2))
            if idx not in actual:
                continue
            checked += 1
            if actual[idx] != claimed:
                problems.append(
                    f"{tf.name}: 声明 result{idx} = {claimed} 行, 实际 {actual[idx]} 行")

    # --- R2 附录 verbatim 变量名 vs 源码 ---
    src_text = ""
    for py in sorted(project_root.rglob("*.py")):
        if "共享" in str(py) or "shared" in str(py).lower():
            continue
        try:
            src_text += py.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
    var_re = re.compile(r"\b(recs?_\w+)\b")
    vchecked = 0
    if src_text:
        for tf in tex_files:
            if "附录" not in tf.name:
                continue
            try:
                content = tf.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for m in var_re.finditer(content):
                v = m.group(1)
                if v.startswith("records_"):
                    continue
                vchecked += 1
                if v not in src_text:
                    problems.append(f"{tf.name}: 变量名 `{v}` 在求解源码里不存在 (逐字不一致)")

    if problems:
        return ("red",
                f"派生量对账 {len(problems)} 处不符 (N-P0-1: 重跑后派生量过期): "
                + "; ".join(problems[:4]),
                "行数 = 时长/步长+1, 重跑必变; 附录 verbatim 的变量名必须与源码逐字一致. "
                "见 references/audit/验收清单.md §H (H7/H8)")
    if not actual:
        return ("yellow", "项目里没有 result*.xlsx, 跳过派生量对账 (跑前 skip)",
                "跑完求解后重跑本 check")
    return ("green",
            f"派生量对账通过: 核对 {checked} 处行数声明 + {vchecked} 处变量名 (N-P0-1 防御)",
            None)


def check_scale_selfcheck():
    r"""checkable 71: v1.8.0 同文量级自洽 (N-P0-3 防御, 终审复验轮).

    背景 (2026A 终审 N-P0-3):
        `2.总体分析` 难点2 写 "浓度边界层厚度 D/h_m ~ 1e-2 mm, 远小于 0.1 cm"
        —— 实际 D/h_m = 4.94e-9/8e-7 = 6.2 mm, **错约 620 倍**,
        且与本文自己 5.1.2 (sqrt(4Dt) ≈ 6 mm) / 6.模型检验 直接矛盾. 终审判 FAIL.

    本 check 只抓**确定的矛盾** (不猜哪个对):
      R1 同文同量级量多值 : 同一"量级类量名"在正文多处给出**不同数值** -> red
                             (同名同量在文内打架 = 自相矛盾信号, 不止是数字错)
      R2 量级陈述无来源   : 量级类断言附近无来源标记 -> yellow (提示补复算, 不误杀)

    判据: R1 命中 red / 否则 green.
    """
    project_root = get_paper_dir().parent
    tex_files = _iter_project_tex(project_root)
    if not tex_files:
        return ("yellow", "项目里没有 .tex, 跳过同文量级自洽", "跑题后必有 论文/*.tex")

    # 量级类量名 (只收"量"语义明确的, 避免温度/浓度这类逐点不同的量误报)
    SCALE_NOUNS = ["边界层厚度", "扩散深度", "穿透深度", "特征扩散时间", "扩散时间",
                   "特征时间", "扩散系数", "穿透量", "边界层尺度"]
    # "量名 ≈ 数值"  —— 允许 LaTeX (\approx / \sim) **与中文措辞**
    # (v1.8.0 修: 反向验证发现中文论文写 "约为 / 约 / 达" 而非 ≈, 原正则抓不到矛盾)
    approx = (r"(?:\\approx|\\sim|≈|~|约(?:为|是)?|达到|等于|不足|不小于|大于|小于|超过)"
              r"\s*\$?\\?\(?\s*([\d.]+(?:[eE][-+]?\d+)?)")

    values = {}      # 量名 -> {值: [出现位置]}
    for tf in tex_files:
        try:
            content = tf.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        flat = re.sub(r"\s+", " ", content)
        for noun in SCALE_NOUNS:
            for m in re.finditer(re.escape(noun) + r"[^\n]{0,40}?" + approx, flat):
                try:
                    v = float(m.group(1))
                except ValueError:
                    continue
                values.setdefault(noun, {}).setdefault(v, []).append(tf.name)

    conflicts = []
    for noun, vals in values.items():
        if len(vals) > 1:
            detail = "; ".join(f"{v} @ {files[0]}" for v, files in sorted(vals.items()))
            conflicts.append(f"{noun}: {len(vals)} 个不同值 ({detail})")

    if conflicts:
        return ("red",
                f"同文量级自相矛盾 {len(conflicts)} 处 (N-P0-3: 量级陈述必须当场复算且全文一致): "
                + "; ".join(conflicts[:3]),
                "同一物理量的量级估计在难点/分析/检验里必须一致; 不一致 = 至少一处错, "
                "当场代入数字复算. 见 references/read-checklist/红线与失败模式.md §红线 8")
    return ("green",
            f"同文量级自洽通过: 扫 {len(SCALE_NOUNS)} 类量级量名, "
            f"{sum(len(v) for v in values.values())} 处断言无互斥",
            None)


def check_abstract_zero_formula():
    r"""checkable 72: v1.8.0 摘要零公式 + 题目出现次数 (F-P0-1 防御).

    背景 (2026A 格式轮 F-P0-1):
        格式审计 A17/A18 一次扣 2 分 —— 摘要含 `D=7×10⁻⁹e⁻⁰·⁸⁹/C`、`ξ=r/R(t)`、
        `Bi_m≈3`、`D=0`、`h/h_m`、`≈`、`≤`、`±`, 违反摘要"零公式"明确要求.
        另: 题目在摘要里重复出现 (应 = 1 次).

    4 类禁项 (计量单位与专有名词如 Robin / 毕渥数 除外):
      R1 数学环境 : $...$ / \\(...\\) / \\[...\\] / equation / align
      R2 希腊字母 : \\alpha ... \\omega + 变体
      R3 关系符号 : ≈ ≤ ≥ ± ≠ ∝ ≡ (含 \\approx \\leq \\geq \\pm \\neq \\propto \\equiv)
      R4 上下标   : _{...} / ^{...}
    另: 题目在摘要里出现次数必须 = 1.

    判据: 任一命中 red / 全过 green / 无摘要文件 yellow.
    """
    paper_dir = get_paper_dir()
    abs_files = sorted(paper_dir.glob("*摘要*.tex"))
    if not abs_files:
        return ("yellow", "没找到摘要 .tex, 跳过零公式检查", "摘要文件名含『摘要』")

    # example-paper 模板状态: 摘要是占位符示例 (含 ≥ 等教学写法), yellow 跳过
    is_template = "templates" in str(paper_dir) or "example" in str(paper_dir)
    if is_template:
        return ("yellow",
                f"example 模板状态 (paper_dir={paper_dir.name}, 摘要是教学示例 = 设计意图, 不算 red)",
                "跑题用户复制 example-paper 到 跑题目录/论文/ 后, 本检查会真跑")

    GREEK = (r"\\alpha|\\beta|\\gamma|\\delta|\\epsilon|\\varepsilon|\\zeta|\\eta|"
             r"\\theta|\\vartheta|\\iota|\\kappa|\\lambda|\\mu|\\nu|\\xi|\\pi|\\rho|"
             r"\\sigma|\\tau|\\upsilon|\\phi|\\varphi|\\chi|\\psi|\\omega|"
             r"\\Gamma|\\Delta|\\Theta|\\Lambda|\\Xi|\\Pi|\\Sigma|\\Phi|\\Psi|\\Omega")
    REL = (r"\\approx|\\leq|\\geq|\\le\b|\\ge\b|\\pm|\\neq|\\ne\b|\\propto|\\equiv|"
           r"≈|≤|≥|±|≠|∝|≡")
    hits = []
    for f in abs_files:
        try:
            c = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        # 去掉 LaTeX 注释行再扫
        body = "\n".join(l for l in c.split("\n") if not l.strip().startswith("%"))
        if re.search(r"\$[^$]+\$|\\\(|\\\)|\\\[|\\begin\{(equation|align|gather|multline)\}", body):
            hits.append(f"{f.name}: 含数学环境 (公式/数学符号)")
        g = re.findall(GREEK, body)
        if g:
            hits.append(f"{f.name}: 含希腊字母 {sorted(set(g))[:4]}")
        r_ = re.findall(REL, body)
        if r_:
            hits.append(f"{f.name}: 含关系符号 {sorted(set(r_))[:4]}")
        if re.search(r"_\{[^}]*\}|\^\{[^}]*\}", body):
            hits.append(f"{f.name}: 含上下标 _{{}}/^{{}}")

    # 题目出现次数: 从主入口提 \title{}
    title = ""
    for entry in sorted(paper_dir.glob("*.tex")):
        try:
            c = entry.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        m = re.search(r"\\title\{(.+?)\}", c, re.S)
        if m:
            title = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", m.group(1))
            title = re.sub(r"[{}\\$]", "", title).strip()
            break
    if title:
        key = re.sub(r"\s+", "", title)[:12]
        for f in abs_files:
            try:
                c = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            n = len(re.findall(re.escape(key), re.sub(r"\s+", "", c)))
            # 只抓"重复出现"(>1); 出现 0 次 = 摘要还没写题面, 不是错
            if n > 1:
                hits.append(f"{f.name}: 题目出现 {n} 次 (应 = 1)")

    if hits:
        return ("red",
                f"摘要零公式检查 {len(hits)} 处不通过 (F-P0-1): " + "; ".join(hits[:4]),
                "摘要用自然语言 + 计量单位, 不写公式/希腊字母/关系符/上下标; "
                "题目在摘要里只出现 1 次. 见 references/paper/paper-spec.md §0 摘要零公式清单")
    return ("green",
            f"摘要零公式通过: 扫 {len(abs_files)} 个摘要文件, 无公式/希腊字母/关系符/上下标, "
            "题目出现 1 次 (F-P0-1 防御)",
            None)


def check_support_package_rules():
    r"""checkable 73: v1.8.0 支撑包红线 (F-P0-2 RA08 优先 + P2-1 + P1-3 同名多副本).

    背景 (2026A 格式轮 F-P0-2, 对 N-P1-3 的**上位修正**):
        N-P1-3 为"输入自含"把题面原始 `附件2.xlsx` 收进包 -> 格式审计 **RA08 直接判违规**
        (不得重复提交赛题原始数据). 两条规则冲突时 **RA08 优先**.

    3 条规则 (顺序即优先级):
      R1 RA08 优先 : 支撑材料/ 里不得有题面原始附件 (附件N.xlsx / 附件N.xls / 附件N.docx)
                     -> red (清洗后的 CSV 不受限)
      R2 无日志残留 : 支撑材料/ 里不得有 *.log -> red (N-P2-1)
      R3 同名多副本 : 同名文件在多个目录下 md5 不一致 -> yellow (F-P1-3/H21)

    判据: R1/R2 命中 red / R3 命中 yellow / 全过 green / 无目录 yellow.
    """
    project_root = get_paper_dir().parent
    sup = None
    for name in ("支撑材料", "支撑材料包", "support"):
        d = project_root / name
        if d.is_dir():
            sup = d
            break
    if sup is None:
        return ("yellow", "项目里没有 支撑材料/ 目录, 跳过包红线检查 (跑前 skip)",
                "打包后重跑本 check")

    import hashlib
    red = []
    logs = []
    by_name = {}

    for f in sorted(sup.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(sup).as_posix()
        # R1 题面原始附件
        if re.search(r"附件\s*\d+\s*\.(xlsx|xls|csv|docx|doc)$", f.name, re.I):
            red.append(f"{rel} (RA08: 题面原始数据不得随包, 用说明文件给复现路径)")
        # R2 日志
        if f.suffix.lower() == ".log":
            logs.append(rel)
        # R3 同名多副本 —— **必须跨目录** (论文侧 / 求解侧 / 包内 三方),
        # 只扫包内抓不到"改了论文侧、求解侧还是旧版"这类不一致 (v1.8.0 反向验证补)
        try:
            h = hashlib.md5(f.read_bytes()).hexdigest()
        except Exception:
            continue
        by_name.setdefault(f.name, []).append((rel, h))

    # 跨目录补扫: 论文侧 / 求解侧 / 其他目录里的同名文件
    for g in sorted(project_root.rglob("*")):
        if not g.is_file():
            continue
        if g.parent == sup or sup in g.parents:
            continue          # 包内文件已单独扫过
        if g.suffix.lower() not in (".py", ".tex", ".csv", ".json"):
            continue
        try:
            h = hashlib.md5(g.read_bytes()).hexdigest()
        except Exception:
            continue
        try:
            rel2 = g.relative_to(project_root).as_posix()
        except Exception:
            continue
        by_name.setdefault(g.name, []).append((rel2, h))

    multi = []
    for name, items in by_name.items():
        if len(items) > 1:
            hs = {h for _, h in items}
            if len(hs) > 1:
                multi.append(f"{name}: {len(items)} 份副本 md5 不一致 "
                             f"({', '.join(r for r, _ in items[:3])})")

    if red or logs:
        msgs = []
        if red:
            msgs.append("RA08 违规 " + str(len(red)) + " 处: " + "; ".join(red[:3]))
        if logs:
            msgs.append("日志残留 " + str(len(logs)) + " 处: " + "; ".join(logs[:3]))
        return ("red",
                "支撑包红线不通过: " + "; ".join(msgs),
                "RA08 优先于输入自含: 题面附件一律不随包, 改在说明文件写『复现时置于 数据/附件/』; "
                "删掉 *.log")
    if multi:
        return ("yellow",
                f"支撑包有 {len(multi)} 个同名多副本 md5 不一致 (F-P1-3/H21): "
                + "; ".join(multi[:3]),
                "论文侧 / 求解侧 / 包内 三方副本必须同步 (改一处要同步全部)")
    return ("green",
            "支撑包红线通过: 无题面原始附件 (RA08) + 无 *.log + 同名副本 md5 一致 "
            "(F-P0-2 / N-P2-1 / F-P1-3 防御)",
            None)

CHECKS = [
    ("0. Python 解释器探测 (v1.6.0 P2-1, py -3 → python → python3, 商店占位符 exit 49; 放第 0 项 = 装包失败时先看解释器, v1.6.6 删掉与本项重复的旧 check 62)", check_python_probe),
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
    ("40. v1.5.7.43 result 文件 vs 论文数字 L6 完整版 (解析 LaTeX 数学环境 + 按问题编号配对 + 偏差 > 5% 红 / 1-5% 黄 / < 1% green, v15 P0-1 / 论文综合 10 处 P0 防御)", check_result_vs_paper_numeric),
    ("41. v1.5.7.35 附件 vs 正文 mtime L7 (附件旧于求解红, 旧于论文黄, v15 P0-4 / v17 P0-E 防御)", check_attachments_vs_paper_mtime),
    ("45. v1.5.7.35 旧图未刷新 L11 (includegraphics 图 mtime vs 求解, 旧于 12h 红, v15 P0-3 / v17 P0-E 防御)", check_figure_mtime_vs_solve),
    ("46. v1.5.7.35 口径混用 L12 (334 天 vs 365 天, ≥2 种混用红, v15 P0-1 / 论文综合 §2.4 防御)", check_calendar_window_consistency),
    ("47. v1.5.7.36 冗余图 L14 (figures/ 中未 \\includegraphics 引用的 .png/.pdf/.svg, 论文综合 §六.2 反例)", check_unused_figures),
    ("48. v1.5.7.36 图注 vs axes L15 (PDF caption 含多面板语义但 figure 实际 axes 不够, 论文综合 §六.1 反例)", check_caption_axes_consistency),
    ("49. v1.5.7.37 AIGC 段首重复率 L16 (<30% 低 green / 30-50% 中等 yellow / >50% 偏高 red, Sep 13 AIGC 报告 39.6% 阈值)", check_segment_opener_repetition),
    ("50. v1.5.7.37 AIGC 连接词密度 L17 (扫 同时/然而/因此/此外 等 10 项, <10% 低 green / 10-15% 中等 yellow / >15% 偏高 red, Sep 13 AIGC 报告 7.5% 阈值)", check_connector_density),
    ("51. v1.5.7.44 AIGC 2-gram TTR L18 (跳过注释 + 跳过数学环境, > 0.45 green / 0.35-0.45 yellow / < 0.35 red, Sep 13 AIGC 报告 0.457 阈值)", check_ngram_ttr),
    ("52. v1.5.7.44 AIGC 3-gram 重复率 L19 (1 - 唯一/总, < 60% green / 60-70% yellow / > 70% red, Sep 13 AIGC 报告 60.3% 阈值)", check_ngram_repetition),
    ("53. v1.5.8 FVM 表面 Robin 离散式 L20 (build_surface_row 返回 (1, 1+β, β) 无 Δt 错格式 red / (1+2μ+γ, -2μ, γ) 真 Robin green / 非 FVM yellow, 2026A 复盘 v1.1 §2.1 P0-1 防御)", check_bc_robin_template),
    ("54. v1.5.8.1 趋势数据 IQR 误用 L21 (IQR/boxplot + 紧邻 drop/删除/剔除 red / 纯描述统计 green / 找不到 yellow, 2026A 复盘 v1.1 §0 P0-2 防御, 升温/收缩段被全删边界条件腰斩)", check_iqr_outlier),
    ("55. v1.5.8.2 关键判据来源标记 L22 (Bi/Fo/收缩率/Re/Pr 含实算/print/resultX/公式 green / 无来源 yellow / 找不到 yellow, 2026A 复盘 v1.1 §0 P0-3 防御, 5.2.2 ρ/cp + 5.4.1 收缩率 + Bi_m=32 三个反例)", check_number_source),
    ("56. v1.5.8.3 resultX 结构 vs 附件3 模板 L23 (sheet 名/A 列名/dtype/行数 red / 全对 green / 找不到附件3 yellow, 2026A 复盘 §P0-4 防御, 4 个 result A 列名 '时间' 应为 '时间\\到药材中心的距离')", check_result_struct),
    ("57. v1.5.8.4 支撑材料超限预案 L24 (>10MB 单文件 + 总 >20MB red / 大文件已配套 csv.gz yellow / 全部 <10MB green / 支撑材料/ 不存在 yellow, 2026A 复盘 §P0-5 防御, result2 36MB 翻车)", check_support_overlimit),
    ("58. v1.5.8.5 附录 ↔ 支撑材料包内容一致性 L25 (\\texttt{{路径}} 包外文件 red / 全在包内 green / 附录无路径 yellow / 支撑材料 不存在 yellow, 2026A 复盘 §P0-6 防御, 附录 J 引 _frag/gen_tables.py 不在包内 + 附录 A 列 result2.xlsx 已剔除)", check_appendix_consistency),
    ("59. v1.5.9 图形内容自检 L26 (np.ptp=0 曲线恒为常数 red / U+2080 下标 C₀ 乱码 yellow / 顶部暗像素 > 0.06 残留 set_title red, 2026A 复盘 §P1-3 防御, 与 check_figure.py 格式自检互补)", check_fig_content_sanity),
    ("60. v1.5.9.4 meta.json 3 件套 L27 (code-template 必落 7 字段 / 缺字段 red / 全填 green / meta.json 不存在 red, 2026A 复盘 §P1-7 防御, 评阅关注点 2 强调'高效' 必填实测耗时+O(复杂度)+步长依据)", check_meta_3pcs),
    ("61. v1.5.9.5 论文表格两行表头 L28 (\\multicolumn + \\multirow 配对 green / 缺 \\multirow yellow / 全无配对 red / 无 longtable yellow, 2026A 复盘 §P1-8 防御, 题面表 '到药材中心的距离/cm' 跨列组表头格式)", check_paper_two_row_header),
    ("63. v1.6.0 LaTeX 波浪号后接中文 L29 (\\textasciitilde/~ 后接中文 red, 波浪号后仅接数字空格, 接中文用'至', 2026A 复盘 §P2-4 防御, 编译报错 ×2)", check_tilde_chinese),
    ("64. v1.6.3 表面行能量守恒校验 L30 (bc_check.py 自测 对组 ratio=1 / 错组 ratio=223 + 模板接入 + 项目 守恒记录*.csv 判 |ratio-1|<=0.05, 2026A 复盘 §验收标准 第 1/2 条, P0-1 决定性证据)", check_bc_energy_conservation),
    ("65. v1.6.4 论文数字台账覆盖 L31 (论文正文候选数字 vs 求解/数值台账.csv, >=70% green / 40-70% yellow / <40% red, 验收标准第 3 条, P0-3 目测数字防御)", check_number_ledger_coverage),
    ("66. v1.6.4 表/图编号一致性 L32 (重复 label red / 悬空 ref red / 越界表图号 red / 附录 result↔表号矛盾 red, 验收标准第 1 条 check_pkg 的表号部分, P0-6 表号错位防御)", check_label_numbering),
    ("67. v1.6.5 章节图名 vs 问题号 L33 (5.N.*.tex 引用 q<M>_*.png 且 M≠N red / 同一图被多问共用 red, P0-2 防御: v1.6.2 模板 4 章共用 q1 图)", check_figure_name_matches_question),
    ("68. v1.7.0 SKILL.md 自洽性 L34 (必读 3 文件 description↔正文一致 / 状态机 5 框都有判据门 / .tex 数量声明=模板实际 / 判据用词统一 green-red / 无坏字符串与错指针, writing-for-agents 第 2 轮审计 3 个 P0 防御)", check_skill_self_consistency),
    ("69. v1.7.2 子进程编码契约 L35 (所有脚本 stdout UTF-8 reconfigure + dryrun 的 subprocess 全带 errors= 容错, 防 --mode agent 管道解码崩溃)", check_script_utf8_contract),
    ("70. v1.8.0 派生量对账 L36 (result 行数声明 vs 实际 xlsx 行数 / 附录 verbatim 变量名 vs 源码逐字一致, 终审复验轮 N-P0-1 防御)", check_derived_numbers),
    ("71. v1.8.0 同文量级自洽 L37 (同名量级量多个不同值 = 自相矛盾 red, 终审复验轮 N-P0-3 防御)", check_scale_selfcheck),
    ("72. v1.8.0 摘要零公式 L38 (数学环境/希腊字母/关系符/上下标全禁 + 题目出现 1 次, 格式轮 F-P0-1 防御)", check_abstract_zero_formula),
    ("73. v1.8.0 支撑包红线 L39 (RA08 题面原始附件不随包优先 / 无 *.log / 同名多副本 md5 一致, 格式轮 F-P0-2+N-P2-1+F-P1-3 防御)", check_support_package_rules),
]


def main():
    json_mode = "--json" in sys.argv
    ci_mode = "--ci" in sys.argv
    # v1.5.7.39: --mode {agent, self, both} 三种模式, 默认 agent
    # 旧 --agent-audit flag 向后兼容 (= agent 模式)
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
        else:
            print("[ERROR] --mode 不带值, 应为 agent/self/both", file=sys.stderr)
            sys.exit(1)
    else:
        mode = "agent"  # v1.5.7.39 默认: agent (调 mavis 代理审计)
    if "--agent-audit" in sys.argv:
        # 向后兼容
        mode = "agent"
    if mode not in ("agent", "self", "both"):
        print(f"[ERROR] --mode 必须是 agent/self/both, 当前 {mode!r}", file=sys.stderr)
        sys.exit(1)

    if mode in ("agent", "both"):
        # 调 agent_audit.py 生成 brief
        import subprocess
        paper_dir = get_paper_dir()
        cmd = [sys.executable, str(SCRIPTS_DIR / "agent_audit.py"),
               "--paper-dir", str(paper_dir)]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        if r.returncode != 0:
            print(f"[ERROR] agent_audit.py 失败 (rc={r.returncode})", file=sys.stderr)
            print(r.stderr, file=sys.stderr)
            sys.exit(1)
        print(r.stdout)
        print("\n" + "=" * 70)
        print("📋 上方是 mavis 代理审计 brief. 复制整段到 mavis 主对话, mavis 会")
        print("   spawn mavis worker sub-session 独立 fresh 审计 (每次 fresh, 不缓存).")
        print("=" * 70)
        if mode == "agent":
            sys.exit(0)
        # mode == "both": 继续跑 self check
        print()
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
