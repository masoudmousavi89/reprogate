import os
import tempfile

from iniconfig import IniConfig

path = os.path.join(tempfile.mkdtemp(), "pytest.ini")
with open(path, "wb") as f:
    f.write("[pytest]\nlog_file = pytest.log\n# 中文\n".encode("utf-8"))

# Run with a non-UTF-8 locale encoding (like gbk in the report) so open() uses it by default.
IniConfig(path)
