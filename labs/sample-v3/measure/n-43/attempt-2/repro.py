import os
import sys
import tempfile

# Force a non-UTF-8 default encoding (like 'gbk' in the report) by re-executing.
if os.environ.get("REPRO_CHILD") != "1":
    env = dict(os.environ, REPRO_CHILD="1", LC_ALL="C", LANG="C",
               PYTHONCOERCECLOCALE="0", PYTHONUTF8="0")
    os.execve(sys.executable, [sys.executable] + sys.argv, env)

from iniconfig import IniConfig

content = "[pytest]\nlog_cli=true\n# 中文\n"
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "pytest.ini")
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    IniConfig(p)
