import io
import sys
from qrcode.console_scripts import main

# stdout is a text-mode stream (no binary buffer), so PNG bytes cannot be written
sys.stdout = io.StringIO()
try:
    main(["text"])
finally:
    sys.stdout = sys.__stdout__
