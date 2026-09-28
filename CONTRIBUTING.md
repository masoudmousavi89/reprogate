# Feedback and contributions

ReproGate is an early prototype (one lab, Python 3.8+, no sandbox). The most useful contribution
right now is **criticism of the idea and the evidence**, not new features.

Questions I would like answered:

1. Is "independent verifier of AI-generated bug-reproduction claims" a real need for maintainers?
2. Which claim kinds matter most after exception type (wrong output, unexpected exit, hang)?
3. Can you construct a reproducer that gets `SYMPTOM_REPRODUCED` without really triggering the bug?
   See `THREAT_MODEL.md` and `labs/jinja-843/fixtures/`; a working bypass is a valuable bug report.
4. Which other real issues would make a good lab #2?

How to help:

- Open an issue (bypasses, wrong outcomes, unclear docs, lab suggestions).
- Run `python -m unittest discover -s tests -t .` on your Python and report failures.
- Run the lab (`labs/jinja-843/README.md`) and send the result table.

Rules of the project: architecture changes only with an entry in `findings.md` that cites evidence.
Reproducers run as plain host processes with **no sandbox**; only run code you have read.
