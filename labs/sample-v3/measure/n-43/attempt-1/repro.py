import os, sys, tempfile, locale
from iniconfig import IniConfig

# Simulate a system whose default encoding is not UTF-8 (e.g. gbk on Windows).
import builtins, io
_open = builtins.open
def gbk_open(file, mode="r", *a, **k):
    if "b" not in mode and "encoding" not in k and len(a) < 2:
        k["encoding"] = "gbk"
    return _open(file, mode, *a, **k)
builtins.open = gbk_open

d = tempfile.mkdtemp()
p = os.path.join(d, "pytest.ini")
with _open(p, "w", encoding="utf-8") as f:
    f.write("[pytest]\nlog_file = pytest.log\n# 中文\n;--basetemp=../results\n")
IniConfig(p)
