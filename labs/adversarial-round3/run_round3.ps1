# ReproGate adversarial round 3 runner for Windows PowerShell 5.1+ (ASCII only on purpose).
# Usage (repo root):  powershell -ExecutionPolicy Bypass -File labs\adversarial-round3\run_round3.ps1 -Yes
# Needs the Lab #1 layout (<Lab>\jinja-before with .venv, <Lab>\jinja-after) and labs\jinja-843\claim.frozen.json
# (run labs\jinja-843\run_lab001.ps1 first). d01-d03 run against COPIES of the venv in %TEMP%; the real venv and
# the checkouts are never written. The copies and the marker file are deleted at the end.
param(
    [string]$Lab = (Join-Path $HOME "reprogate-lab"),
    [switch]$Yes
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent (Split-Path -Parent $here)
$before = Join-Path $Lab "jinja-before"
$after = Join-Path $Lab "jinja-after"
$venv = Join-Path $before ".venv"
$pinned = Join-Path $venv "Scripts\python.exe"
$claim = Join-Path $proj "labs\jinja-843\claim.frozen.json"
foreach ($p in @($before, $after, $pinned, $claim)) {
    if (-not (Test-Path $p)) { Write-Host ("MISSING: " + $p); exit 2 }
}
if (-not $Yes) {
    Write-Host "NO SANDBOX: runs small vetted Python files on THIS computer. Re-run with -Yes to continue."
    exit 1
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ev = Join-Path $here ("evidence-" + $stamp)
$tmp = Join-Path $env:TEMP ("reprogate-round3-" + $stamp)
$marker = Join-Path $env:TEMP "reprogate_r3_d02_marker.txt"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
New-Item -ItemType Directory -Force -Path $ev | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue $marker

function Run-Attack($name, $py, $repro) {
    Write-Host ("--- " + $name)
    & py -3.8 -m reprogate run --repo $before --python $py --claim $claim --reproducer $repro --out (Join-Path $ev $name) --allow-host-execution
}
function New-VenvCopy($name) {
    $dst = Join-Path $tmp $name
    Copy-Item -Recurse -Force $venv $dst
    return $dst
}
function Env-Sha($py) {
    & py -3.8 -c "import sys; from reprogate.runner import capture_environment; print(capture_environment(sys.argv[1])[1])" $py
}

Push-Location $proj
try {
    # d01: benign tamper of an installed dependency file, then check what the evidence says
    $v1 = New-VenvCopy "venv_d01"
    $py1 = Join-Path $v1 "Scripts\python.exe"
    $f1 = Join-Path $v1 "Lib\site-packages\markupsafe\__init__.py"
    $envBefore = Env-Sha $py1
    $shaBefore = (Get-FileHash $f1 -Algorithm SHA256).Hash
    Run-Attack "d01_tamper_dependency_file" $py1 (Join-Path $here "d01_tamper_dependency_file.py")
    $shaAfter = (Get-FileHash $f1 -Algorithm SHA256).Hash
    $envAfter = Env-Sha $py1
    $recEnv = (Get-Content (Join-Path $ev "d01_tamper_dependency_file\outcome.json") -Raw | ConvertFrom-Json).environment_sha256
    Write-Host ("D01 file_hash_changed=" + ($shaBefore -ne $shaAfter) + " env_sha_before_equals_after=" + ($envBefore -eq $envAfter) + " recorded_env_equals_after=" + ($recEnv -eq $envAfter))

    # d02: sitecustomize written into site-packages by run 1 executes in later runs before the harness
    $v2 = New-VenvCopy "venv_d02"
    $py2 = Join-Path $v2 "Scripts\python.exe"
    Run-Attack "d02_sitecustomize_persistence" $py2 (Join-Path $here "d02_sitecustomize_persistence.py")
    $n = 0
    if (Test-Path $marker) { $n = (Get-Content $marker -Raw).Length }
    Write-Host ("D02 marker_writes=" + $n)

    # d03: run 1 poisons markupsafe so that later imports raise the claimed message at import time
    $v3 = New-VenvCopy "venv_d03"
    $py3 = Join-Path $v3 "Scripts\python.exe"
    Run-Attack "d03_poison_dependency_claim_text" $py3 (Join-Path $here "d03_poison_dependency_claim_text.py")

    # d04: malicious issue whose claim matches an intended behaviour; single run, then the before/after oracle
    Write-Host "--- d04_malicious_issue"
    $mal = Join-Path $here "malicious-issue"
    $frozen = Join-Path $ev "d04_claim.frozen.json"
    $repro4 = Join-Path $here "d04_malicious_issue_reproducer.py"
    & py -3.8 -m reprogate claim-check --claim (Join-Path $mal "claim.json") --issue-body (Join-Path $mal "issue.body.md") --out $frozen
    & py -3.8 -m reprogate run --repo $before --python $pinned --claim $frozen --reproducer $repro4 --out (Join-Path $ev "d04_run") --allow-host-execution
    & py -3.8 -m reprogate oracle --before-repo $before --after-repo $after --python $pinned --claim $frozen --reproducer $repro4 --out (Join-Path $ev "d04_oracle") --allow-host-execution
    Write-Host ""
    Write-Host ("Evidence folder: " + $ev)
} finally {
    Pop-Location
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $tmp
    Remove-Item -Force -ErrorAction SilentlyContinue $marker
}
