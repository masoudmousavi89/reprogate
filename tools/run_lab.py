"""Run one lab end to end (host mode): checkouts, venv, provenance check, oracle, fixtures, summary.

    python tools/run_lab.py labs/tabulate-180 --work <dir> [--python <target python>]

The lab directory holds claim.json, repro.py, fixtures/*.py and expected_outcomes.json (written before the run).
Optional claim.json field: "env": {"pip": ["pkg==1.0", ...], "pythonpath": ["src"]}: pip packages are installed into the venv
used as the target python; pythonpath entries (relative to the checkout) are put on sys.path (src layouts).
If claim.json has an issue number, the raw issue body is fetched and claim-check is applied; when it does not
pass, the run continues with the unverified claim and every outcome carries the provenance qualifier.
WARNING: no sandbox, reproducers run on this machine.
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(args, cwd=None, check=True):
    r = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    if check and r.returncode != 0:
        sys.exit("command failed: %s\n%s" % (" ".join(args), r.stdout[-800:]))
    return r


def venv_python(d):
    return os.path.join(d, "Scripts", "python.exe") if os.name == "nt" else os.path.join(d, "bin", "python")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lab")
    ap.add_argument("--work", required=True)
    ap.add_argument("--python", default=sys.executable, help="interpreter used to create the venv")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--origin", help="reproducer_origin recorded in the evidence (default: the tool default)")
    a = ap.parse_args()
    lab = os.path.abspath(a.lab)
    name = os.path.basename(lab)
    claim_path = os.path.join(lab, "claim.json")
    claim = json.load(open(claim_path, encoding="utf-8"))
    repo = claim["issue"]["repo"]
    work = os.path.abspath(a.work)
    os.makedirs(work, exist_ok=True)
    clone = os.path.join(work, repo.replace("/", "__"))
    if not os.path.isdir(clone):
        sh(["git", "clone", "-q", "https://github.com/%s" % repo, clone])
    sides = {}
    for side, rev in (("before", claim["target"]["affected_commit"]), ("after", claim["target"]["fix_commit"])):
        sha = sh(["git", "rev-parse", rev], cwd=clone).stdout.strip()
        d = os.path.join(work, "%s-%s" % (name, side))
        if not os.path.isdir(d):
            sh(["git", "worktree", "add", "-q", "--detach", d, sha], cwd=clone)
        sides[side] = (d, sha)
    venv = os.path.join(work, "%s-venv" % name)
    if not os.path.isdir(venv):
        sh([a.python, "-m", "venv", venv])
        pips = claim.get("env", {}).get("pip", [])
        if pips:
            sh([venv_python(venv), "-m", "pip", "install", "-q"] + pips)
    py = venv_python(venv)
    ver = sh([py, "-c", "import sys;print(sys.version.split()[0])"]).stdout.strip()

    ev = os.path.join(work, "evidence-" + name)
    os.makedirs(ev, exist_ok=True)
    use_claim, extra = claim_path, ["--allow-unverified-provenance"]
    number = claim["issue"].get("number")
    if number and not a.no_fetch:
        pfx = os.path.join(ev, "issue")
        r = sh([sys.executable, os.path.join(ROOT, "tools", "fetch_issue.py"), "--repo", repo, "--number", str(number),
                "--out", pfx], check=False)
        if r.returncode == 0:
            frozen = os.path.join(ev, "claim.frozen.json")
            r = sh([sys.executable, "-m", "reprogate", "claim-check", "--claim", claim_path, "--issue-body",
                    pfx + ".body.md", "--out", frozen], cwd=ROOT, check=False)
            print(r.stdout.strip())
            if "provenance_sufficient: True" in r.stdout:
                use_claim, extra = frozen, []
        else:
            print("issue fetch failed:", r.stdout[-200:])
    print("provenance:", "VERIFIED" if not extra else "UNVERIFIED", "| python", ver)

    base = [sys.executable, "-m", "reprogate"]
    for e in claim.get("env", {}).get("pythonpath", []):
        extra = extra + ["--pythonpath-extra", e]
    if a.origin:
        extra = extra + ["--origin", a.origin]
    sh(base + ["oracle", "--before-repo", sides["before"][0], "--after-repo", sides["after"][0], "--python", py,
               "--claim", use_claim, "--reproducer", os.path.join(lab, "repro.py"), "--out", os.path.join(ev, "oracle"),
               "--allow-host-execution"] + extra, cwd=ROOT, check=False)
    fx = os.path.join(lab, "fixtures")
    for f in sorted(os.listdir(fx)) if os.path.isdir(fx) else []:
        if f.endswith(".py"):
            sh(base + ["run", "--repo", sides["before"][0], "--python", py, "--claim", use_claim, "--reproducer",
                       os.path.join(fx, f), "--out", os.path.join(ev, f[:-3]), "--allow-host-execution"] + extra,
               cwd=ROOT, check=False)
    res = os.path.join(ev, "results.md")
    r = sh([sys.executable, os.path.join(ROOT, "tools", "lab_summary.py"), "--evidence", ev, "--expected",
            os.path.join(lab, "expected_outcomes.json"), "--out", res], check=False)
    print(r.stdout)
    print("before=%s after=%s" % (sides["before"][1][:7], sides["after"][1][:7]))
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
