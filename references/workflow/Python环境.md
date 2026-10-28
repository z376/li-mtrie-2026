# Python 环境规范 (v1.6.0 新建, P2-1 + P2-2 防御)

> **踩坑教训 (2026A 复盘 §P2-1)**: `python` 为**微软商店占位符** (exit 49), 全程被迫用 `py`. 改进: 环境节改**探测式** — `py -3` / `python` / `python3` 依次尝试, 锁定后固化; dryrun 第 0 项 (check 62) 自动探测.
>
> **踩坑教训 (2026A 复盘 §P2-2)**: GBK 控制台反复 `UnicodeEncodeError`. 改进: 脚本模板头部强制 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` (调用方无需关心).
>
> **本规范权威源**: 赛前 1 天必做 + 开赛第 1 小时必做. SKILL.md §Python 环境 留 1 行指针 → 本文件.

---

## 1. 探测式 (P2-1 核心, 别假设 `python` 能用)

**Windows 上 `python` 可能是 3 种东西**:
1. **微软商店占位符** — 装了但没真装, 执行报 `exit 49` + 弹商店页面. **最坑的一种**
2. **Anaconda / 系统版** — 真 Python, 但版本可能太老
3. **完全没装** — `command not found`

**探测脚本** (PowerShell, 依次尝试):

```powershell
$ErrorActionPreference = 'SilentlyContinue'
foreach ($cmd in @('py -3', 'python', 'python3')) {
    $ver = Invoke-Expression "$cmd -c `"import sys; print(sys.version_info[:2])`"" 2>$null
    if ($LASTEXITCODE -eq 0 -and $ver) {
        Write-Host "[OK] 可用: $cmd  →  $ver"
        # 锁定后固化:
        Set-Alias py "$cmd"    # 或在 PATH 最前放一个 shim
        break
    } elseif ($LASTEXITCODE -eq 49) {
        Write-Host "[占位符] $cmd 是微软商店占位符 (exit 49), 跳过"
    } else {
        Write-Host "[无] $cmd 不可用"
    }
}
```

**exit 49 = 商店占位符的判定标志**. 见到 49 直接换下一个, 别在这上面耗时间.

**固化**: 锁定后在 `跑题目录/环境.md` 写一行 `PY=py -3` (或 `PY=python`), 之后所有命令统一用 `$PY`. 别在赛中发现 `python` 变了.

**推荐版本**: 3.10 / 3.11 / 3.12 (3.13+ 部分老包兼容性差, e.g. `pulp` / `scipy` 旧版).

---

## 2. 3 步绿验证 (checkable)

**绿 = 1 行 `core ok` 输出**, **红 = 任何 import 失败或 pip/python 不一致**.

```powershell
# Step 1: 解释器一致 (1 行)
py -3 -c "import sys; print(sys.executable)"

# Step 2: pip/python 同源 (1 行)
py -3 -m pip --version

# Step 3: import 验证 (1 行 = 绿)
py -3 -c "import pandas, numpy, scipy, matplotlib, openpyxl, fitz, pulp; print('core ok')"
```

**Why 5 分钟排查 = 1 行提前验证**: Windows 上常同时存在多个 Python (微软商店版 / Anaconda / 系统版 / VS Code 选中版), `pip install` 装到 A 解释器, Jupyter 用 B → `import pulp` 仍 `ModuleNotFoundError`.

---

## 3. GBK 控制台兼容 (P2-2 核心)

**问题**: 中文 Windows 控制台默认 GBK (CP936), 脚本 print 中文/emoji 会 `UnicodeEncodeError`.

**解法**: 所有脚本头部强制 reconfigure (调用方无需关心):

```python
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        # Python < 3.7 或 stream 已关闭时降级到 TextIOWrapper
        import io
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass
```

**已在 `references/code-template.py` §Windows GBK 终端兼容 段内置** (v1.5.x 起). 跑题用户复制模板即可继承.

**P2-2 附带坑 (实测)**: 模板里的 emoji (✅ ❌ ⚠️) 在 GBK 终端下 print 必炸, 所以 reconfigure 必须在 **import 阶段**就做, 不能等到 main() 里.

---

## 4. venv 隔离 (强烈建议, 每赛题目录一个)

```powershell
py -3 -m venv .venv ; .\.venv\Scripts\Activate.ps1

# 激活后命令行前缀变 (.venv) PS ... = 隔离绿
```

**为什么**: 赛场只有一台机, 但你赛前装了 5 个包 (torch / sklearn / 某统计包), 某个把 numpy 降级了 → 全线炸. venv 隔离保平安.

---

## 5. 装包 + 封闭赛场预下载

**装包** (核心 + 优化, 缺 pulp → 规划类解不了):

```powershell
py -3 -m pip install pandas numpy scipy matplotlib openpyxl PyMuPDF pulp

# 可选: py -3 -m pip install seaborn plotly scikit-learn
```

**封闭赛场预下载** (赛前 1 天必做, 开赛当晚来不及):

```powershell
py -3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
py -3 -m pip download -d ./pkgs pandas numpy scipy matplotlib openpyxl PyMuPDF pulp

# 比赛时: py -3 -m pip install --no-index --find-links=./pkgs <pkgs>
```

**镜像源**: 清华 TUNA 优先 (国内快), 阿里云/腾讯云备选.

---

## 6. dryrun check 62 (第 0 项, P2-1 自动探测)

`references/scripts/dryrun.py` `check_python_probe` (v1.6.0 新增):

- 依次探测 `py -3` / `python` / `python3`
- 命中 exit 49 (商店占位符) → 跳过并报告
- 探测到可用的 → **green** (报告版本 + 路径)
- 全部不可用 → **red** (赛前必须修)
- 顺带验证 `pip` 与解释器同源

**用法**: `python references/scripts/dryrun.py --mode self` 输出第 0 项 = Python 探测.

---

## 7. 踩坑案例库

| 坑 | 症状 | 修复 |
|---|------|------|
| `python` 是商店占位符 | exit 49 + 弹商店 | 改 `py -3`, 固化 `$PY` |
| 装包后 import 仍失败 | `ModuleNotFoundError: pulp` | `py -3 -m pip install` (同源), 别用裸 `pip` |
| GBK 编码炸 | `UnicodeEncodeError: 'gbk' codec` | 脚本头部 `sys.stdout.reconfigure(encoding='utf-8')` |
| emoji 在 GBK 炸 | 同上 | reconfigure 放 import 阶段 |
| 赛场断网 | pip 装不上 | 赛前 `pip download` 到 ./pkgs |
| 多 Python 混用 | pip 装到 A, Jupyter 用 B | 每赛题 venv |

---

## 8. 引用

- `SKILL.md` §Python 环境 (1 行指针 → 本文件)
- `references/scripts/dryrun.py check_python_probe` (L29, 第 0 项)
- `references/code-template.py` §Windows GBK 终端兼容 (内置 reconfigure)
- 2026A 复盘 v1.1 §P2-1 + §P2-2 (Sep 28 改进意见原始素材)
