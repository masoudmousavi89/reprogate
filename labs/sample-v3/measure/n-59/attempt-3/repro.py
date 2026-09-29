import io
import sys

# Modern Pillow special-cases a real io.TextIOWrapper sys.stdout (writes to .buffer), which
# hides the bug. Use a plain text-only stdout that is not a tty, like a text pipe.
sys.stdout = io.StringIO()

from qrcode import console_scripts

console_scripts.main(["text"])
