"""mma 通用数据工具:跨题目可复用。

解决的问题:
- Windows PowerShell 5.1 + GBK 环境下,pandas read_csv 默认按 GBK 解码 UTF-8 CSV → 乱码
- PowerShell 子进程 stdout 在中文 Windows 上输出 emoji / Unicode 报 UnicodeEncodeError

用法:
    from data_utils import read_csv_safe, save_csv, ensure_utf8_stdout

    ensure_utf8_stdout()  # 每次脚本顶部调一次
    df = read_csv_safe("data.csv")
    save_csv(df, "result.csv")
"""
import io
import sys
from pathlib import Path

import pandas as pd


def ensure_utf8_stdout():
    """让 print() 能输出中文/emoji,绕过 Windows GBK。

    在每个 py 脚本顶部调一次。
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def read_csv_safe(path, **kwargs):
    """强制 utf-8-sig 读 CSV,绕过 PowerShell GBK 环境问题。

    直接 pd.read_csv 在中文 Windows 环境下会按 GBK 解码 UTF-8 文件 → 列名乱码。
    本函数用 io.StringIO 包装已读文本,让 pandas 收到 StringIO 后不再自行判断 encoding。
    """
    p = Path(path)
    with open(p, "r", encoding="utf-8-sig") as f:
        return pd.read_csv(f, **kwargs)


def save_csv(df, path, index=False, **kwargs):
    """写 CSV(utf-8-sig,Excel 兼容)。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=index, encoding="utf-8-sig", **kwargs)
