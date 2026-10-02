# ReproGate wheelhouse lab (req_004, oq_003) for Windows PowerShell 5.1+ (ASCII only on purpose).
# Usage (repo root):  powershell -ExecutionPolicy Bypass -File labs\wheelhouse\run_wheelhouse.ps1 -Yes
# Needs the Lab #1 layout (<Lab>\jinja-before, <Lab>\jinja-after) and labs\jinja-843\claim.frozen.json.
# Downloads MarkupSafe wheels from PyPI into a temp wheelhouse; builds venvs from it with --no-index.
param(
    [string]$Lab = (Join-Path $HOME "reprogate-lab"),
    [switch]$Yes
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent (Split-Path -Parent $here)
$before = Join-Path $Lab "jinja-before"
$after = Join-Path $Lab "jinja-after"
$claim = Join-Path $proj "labs\jinja-843\claim.frozen.json"
$repro = Join-Path $proj "labs\jinja-843\repro.py"
foreach ($p in @($before, $after, $claim, $repro)) {
    if (-not (Test-Path $p)) { Write-Host ("MISSING: " + $p); exit 2 }
}
if (-not $Yes) { Write-Host "Downloads wheels from PyPI and runs small vetted Python files on THIS computer. Re-run with -Yes."; exit 1 }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ev = Join-Path $here ("evidence-" + $stamp)
$tmp = Join-Path $env:TEMP ("reprogate-wheelhouse-" + $stamp)
$wh = Join-Path $tmp "wheelhouse"
$free = Join-Path $tmp "unconstrained"
New-Item -ItemType Directory -Force -Path $tmp, $wh, $free, $ev | Out-Null
$versions = @("2.0.0", "2.0.1", "2.1.0", "2.1.1", "2.1.2", "2.1.3", "2.1.4", "2.1.5")

Write-Host "=== 1. download"
foreach ($v in $versions) {
    & py -3.8 -m pip download --python-version 3.8 --only-binary=:all: --no-deps --disable-pip-version-check -q -d $wh ("MarkupSafe==" + $v) 2>&1 | Out-Host
    Write-Host ("DOWNLOAD " + $v + " exit=" + $LASTEXITCODE)
}
& py -3.8 -m pip download --python-version 3.8 --only-binary=:all: --disable-pip-version-check -q -d $free "MarkupSafe>=0.23" 2>&1 | Out-Host
Write-Host ("UNCONSTRAINED resolves to: " + ((Get-ChildItem $free | ForEach-Object { $_.Name }) -join ","))
$hashes = Get-ChildItem $wh -File | Sort-Object Name | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower() + "  " + $_.Name }
$hashes | Set-Content -Encoding ASCII (Join-Path $ev "wheelhouse.sha256.txt")
$hashes | Out-Host
Get-ChildItem $wh -File | ForEach-Object { $_.IsReadOnly = $true }
Write-Host ("WHEELHOUSE files=" + (Get-ChildItem $wh -File).Count + " all_read_only=" + (-not (Get-ChildItem $wh -File | Where-Object { -not $_.IsReadOnly })))

function BuildVenv($name, $v) {
    $d = Join-Path $tmp $name
    & py -3.8 -m venv $d | Out-Host
    $py = Join-Path $d "Scripts\python.exe"
    & $py -m pip install --no-index --find-links $wh --disable-pip-version-check -q ("MarkupSafe==" + $v) 2>&1 | Out-Host
    Write-Host ("INSTALL " + $name + " exit=" + $LASTEXITCODE)
    return $d
}
function PkgHash($d) {
    (Get-ChildItem (Join-Path $d "Lib\site-packages\markupsafe") -File -Filter *.py* | Sort-Object Name | ForEach-Object { $_.Name + ":" + (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower() }) -join ";"
}
function TreeSha($dir) {
    & py -3.8 -c "import sys; from reprogate.runner import tree_hash; print(tree_hash(sys.argv[1])[0])" $dir
}

Write-Host "=== 2. import jinja2 (pre-fix checkout) per version"
foreach ($v in $versions) {
    $d = BuildVenv ("v_" + $v) $v
    $py = Join-Path $d "Scripts\python.exe"
    & $py -c "import sys; sys.path.insert(0, sys.argv[1]); import jinja2; print('IMPORT_OK', jinja2.__file__)" $before 2>&1 | Select-Object -Last 1 | Out-Host
    Write-Host ("IMPORT " + $v + " exit=" + $LASTEXITCODE)
}

Write-Host "=== 3. rebuild determinism (2.0.1 twice)"
$a = BuildVenv "tmpl_a" "2.0.1"
$b = BuildVenv "tmpl_b" "2.0.1"
Write-Host ("REBUILD installed_markupsafe_files_identical=" + ((PkgHash $a) -eq (PkgHash $b)))

Push-Location $proj
try {
    $tpy = Join-Path $a "Scripts\python.exe"
    $t0 = TreeSha $a
    Write-Host "=== 4a. oracle with the wheelhouse-built 2.0.1 template"
    & py -3.8 -m reprogate oracle --before-repo $before --after-repo $after --python $tpy --env-template $a --claim $claim --reproducer $repro --out (Join-Path $ev "oracle") --allow-host-execution | Out-Host
    $t1 = TreeSha $a
    Write-Host ("TEMPLATE tree_hash_before=" + $t0 + " after=" + $t1 + " unchanged=" + ($t0 -eq $t1))
    Get-ChildItem (Join-Path $ev "oracle") -Recurse -Filter environment.json | ForEach-Object { Write-Host ("ENVIRONMENT_JSON " + $_.FullName); Get-Content $_.FullName -Raw | Out-Host }
    Write-Host "=== 4b. run with the 2.1.5 template"
    $d5 = Join-Path $tmp "v_2.1.5"
    & py -3.8 -m reprogate run --repo $before --python (Join-Path $d5 "Scripts\python.exe") --env-template $d5 --claim $claim --reproducer $repro --out (Join-Path $ev "case_2_1_5") --allow-host-execution | Out-Host
} finally {
    Pop-Location
}
Write-Host ""
Write-Host ("Evidence folder: " + $ev + "  (temp dir kept for inspection: " + $tmp + ")")
