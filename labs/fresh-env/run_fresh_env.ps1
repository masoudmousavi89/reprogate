# ReproGate fresh-environment-per-run runner (F-032) for Windows PowerShell 5.1+ (ASCII only on purpose).
# Usage (repo root):  powershell -ExecutionPolicy Bypass -File labs\fresh-env\run_fresh_env.ps1 -Yes
# Needs the Lab #1 layout (<Lab>\jinja-before with .venv, <Lab>\jinja-after) and labs\jinja-843\claim.frozen.json.
# d01-d03 (labs\adversarial-round3) run against a COPY of the venv used as --env-template; the real .venv is used only as a
# read-only template for the last (oracle) step. Copies and the marker file are deleted at the end.
param(
    [string]$Lab = (Join-Path $HOME "reprogate-lab"),
    [switch]$Yes
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent (Split-Path -Parent $here)
$r3 = Join-Path $proj "labs\adversarial-round3"
$before = Join-Path $Lab "jinja-before"
$after = Join-Path $Lab "jinja-after"
$venv = Join-Path $before ".venv"
$pinned = Join-Path $venv "Scripts\python.exe"
$claim = Join-Path $proj "labs\jinja-843\claim.frozen.json"
foreach ($p in @($before, $after, $pinned, $claim)) {
    if (-not (Test-Path $p)) { Write-Host ("MISSING: " + $p); exit 2 }
}
if (-not $Yes) { Write-Host "NO SANDBOX: runs small vetted Python files on THIS computer. Re-run with -Yes to continue."; exit 1 }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ev = Join-Path $here ("evidence-" + $stamp)
$tmp = Join-Path $env:TEMP ("reprogate-fresh-" + $stamp)
$marker = Join-Path $env:TEMP "reprogate_r3_d02_marker.txt"
New-Item -ItemType Directory -Force -Path $tmp, $ev | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue $marker

function TreeSha($dir) {
    & py -3.8 -c "import sys; from reprogate.runner import tree_hash; print(tree_hash(sys.argv[1])[0])" $dir
}
function Attack($name, $repro, $tmpl, $py) {
    Write-Host ("--- " + $name)
    $t = Measure-Command {
        & py -3.8 -m reprogate run --repo $before --python $py --env-template $tmpl --claim $claim --reproducer $repro --out (Join-Path $ev $name) --allow-host-execution | Out-Host
    }
    $copies = @(Get-ChildItem (Join-Path $ev "$name\runs") -Directory | ForEach-Object { (Get-Content (Join-Path $_.FullName "run.json") -Raw | ConvertFrom-Json).env_copy_seconds })
    $avg = ($copies | Measure-Object -Average).Average
    Write-Host ("COST " + $name + " total_seconds=" + [math]::Round($t.TotalSeconds, 1) + " env_copy_seconds=" + ($copies -join ",") + " avg=" + [math]::Round($avg, 2))
}

Push-Location $proj
try {
    $tmpl = Join-Path $tmp "template"
    Copy-Item -Recurse -Force $venv $tmpl
    $tpy = Join-Path $tmpl "Scripts\python.exe"
    $mk = Join-Path $tmpl "Lib\site-packages\markupsafe\__init__.py"
    $tSha0 = TreeSha $tmpl
    $fSha0 = (Get-FileHash $mk -Algorithm SHA256).Hash

    Attack "d01_tamper_dependency_file" (Join-Path $r3 "d01_tamper_dependency_file.py") $tmpl $tpy
    $fSha1 = (Get-FileHash $mk -Algorithm SHA256).Hash
    Write-Host ("D01 template_file_hash_unchanged=" + ($fSha0 -eq $fSha1))
    $rec = (Get-Content (Join-Path $ev "d01_tamper_dependency_file\environment.json") -Raw | ConvertFrom-Json).environment_isolation
    Write-Host ("D01 recorded_mode=" + $rec.mode + " recorded_hash_equals_independent=" + ($rec.template_tree_sha256 -eq $tSha0))

    Attack "d01_again" (Join-Path $r3 "d01_tamper_dependency_file.py") $tmpl $tpy
    $rec2 = (Get-Content (Join-Path $ev "d01_again\environment.json") -Raw | ConvertFrom-Json).environment_isolation
    Write-Host ("DETERMINISM same_template_hash=" + ($rec.template_tree_sha256 -eq $rec2.template_tree_sha256))

    Attack "d02_sitecustomize_persistence" (Join-Path $r3 "d02_sitecustomize_persistence.py") $tmpl $tpy
    $n = 0
    if (Test-Path $marker) { $n = (Get-Content $marker -Raw).Length }
    Write-Host ("D02 marker_writes=" + $n)

    Attack "d03_poison_dependency_claim_text" (Join-Path $r3 "d03_poison_dependency_claim_text.py") $tmpl $tpy
    $o3 = Get-Content (Join-Path $ev "d03_poison_dependency_claim_text\outcome.json") -Raw | ConvertFrom-Json
    Write-Host ("D03 completed=" + $o3.counts.completed + " clean_completion_runs=" + $o3.counts.clean_completion_runs)
    Write-Host ("TEMPLATE tree_hash_unchanged_after_all_attacks=" + ((TreeSha $tmpl) -eq $tSha0))

    # jinja oracle with the REAL venv as a read-only template
    Write-Host "--- jinja_oracle_real_venv_as_template"
    $realBefore = TreeSha $venv
    $t = Measure-Command {
        & py -3.8 -m reprogate oracle --before-repo $before --after-repo $after --python $pinned --env-template $venv --claim $claim --reproducer (Join-Path $proj "labs\jinja-843\repro.py") --out (Join-Path $ev "jinja_oracle") --allow-host-execution | Out-Host
    }
    Write-Host ("COST jinja_oracle total_seconds=" + [math]::Round($t.TotalSeconds, 1))
    Write-Host ("REAL_VENV tree_hash_unchanged=" + ((TreeSha $venv) -eq $realBefore))
    foreach ($b in @("before", "after")) {
        & py -3.8 -m reprogate inspect --evidence (Join-Path $ev "jinja_oracle\$b") | Select-String "outcome  |invariants" | ForEach-Object { Write-Host ($b + ": " + $_.Line.Trim()) }
    }
    Write-Host ""
    Write-Host ("Evidence folder: " + $ev)
} finally {
    Pop-Location
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $tmp
    Remove-Item -Force -ErrorAction SilentlyContinue $marker
}
