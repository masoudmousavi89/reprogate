# ReproGate Lab #1 runner for Windows PowerShell 5.1+ (ASCII only on purpose).
# Usage (from anywhere):
#   powershell -ExecutionPolicy Bypass -File labs\jinja-843\run_lab001.ps1
# Expects the layout you created by hand:
#   <Lab>\jinja-before   (worktree at the parent of the fix, with .venv and .venv-unpinned)
#   <Lab>\jinja-after    (worktree at the fix merge commit)
param(
    [string]$Lab = (Join-Path $HOME "reprogate-lab")
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent (Split-Path -Parent $here)
$before = Join-Path $Lab "jinja-before"
$after = Join-Path $Lab "jinja-after"
$pinned = Join-Path $before ".venv\Scripts\python.exe"
$unpinned = Join-Path $before ".venv-unpinned\Scripts\python.exe"

foreach ($p in @($before, $after, $pinned, $unpinned)) {
    if (-not (Test-Path $p)) { Write-Host ("MISSING: " + $p); exit 2 }
}

Write-Host ""
Write-Host "WARNING: this prototype has NO sandbox. It runs the small Python files in"
Write-Host "  labs\jinja-843\repro.py and labs\jinja-843\fixtures\*.py on THIS computer."
Write-Host "  Read them first if you want (each is 3-12 lines). Nothing is installed."
$answer = Read-Host "Type YES to continue"
if ($answer -ne "YES") { Write-Host "Cancelled."; exit 1 }

Push-Location $proj
try {
    $pyArgs = @("-3.8", "-m", "reprogate")
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $ev = Join-Path $here ("evidence-" + $stamp)
    $repro = Join-Path $here "repro.py"

    # 1. freeze claim provenance from the RAW issue body (needs internet); otherwise continue, clearly marked
    $claim = Join-Path $here "claim.json"
    $extra = @("--allow-unverified-provenance")
    $bodyPrefix = Join-Path $here "issue843"
    & py -3.8 (Join-Path $proj "tools\fetch_issue.py") --out $bodyPrefix
    if ($LASTEXITCODE -eq 0) {
        $frozen = Join-Path $here "claim.frozen.json"
        & py @pyArgs claim-check --claim $claim --issue-body ($bodyPrefix + ".body.md") --out $frozen
        if ($LASTEXITCODE -eq 0) {
            $claim = $frozen
            $extra = @()
        } else {
            Write-Host "claim-check: provenance NOT sufficient. Continuing with unverified provenance (recorded)."
        }
    } else {
        Write-Host "Could not download the issue body. Continuing with unverified provenance (recorded)."
    }

    # 2. oracle: before (pinned) must reproduce; after (same interpreter) must complete cleanly
    & py @pyArgs oracle --before-repo $before --after-repo $after --python $pinned --claim $claim --reproducer $repro --out (Join-Path $ev "oracle") --allow-host-execution @extra

    # 3. environment failure: same reproducer, unpinned MarkupSafe
    & py @pyArgs run --repo $before --python $unpinned --claim $claim --reproducer $repro --out (Join-Path $ev "case_c_unpinned") --allow-host-execution @extra

    # 4. fake / gamed reproducers on the buggy commit
    foreach ($f in @("f01_direct_raise", "f02_direct_deque_popleft", "f03_fake_traceback_stdout", "f04_subclass_override")) {
        & py @pyArgs run --repo $before --python $pinned --claim $claim --reproducer (Join-Path $here ("fixtures\" + $f + ".py")) --out (Join-Path $ev $f) --allow-host-execution @extra
    }

    # 5. compare with the expectations written before the run
    & py -3.8 (Join-Path $proj "tools\lab_summary.py") --evidence $ev --expected (Join-Path $here "expected_outcomes.json") --out (Join-Path $ev "results.md")
    Write-Host ""
    Write-Host ("Evidence folder: " + $ev)
    Write-Host "Send me results.md (printed above) and any error text."
} finally {
    Pop-Location
}
