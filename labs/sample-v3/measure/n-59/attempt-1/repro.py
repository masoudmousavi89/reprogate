import io, sys
from qrcode.console_scripts import main

# stdout is a pipe/file (not a tty); on Python 3 sys.stdout is a text stream
sys.stdout = io.StringIO()
try:
    main(["text"])
finally:
    out, sys.stdout = sys.stdout, sys.__stdout__
