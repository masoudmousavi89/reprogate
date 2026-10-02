# ReproGate checkout-by-SHA lab (req_005) for Windows PowerShell 5.1+ (ASCII only on purpose).
# Usage (repo root):  powershell -ExecutionPolicy Bypass -File labs\checkout-sha\run_checkout_sha.ps1 -Yes
# Needs the Lab #1 layout (<Lab>\jinja = full clone, <Lab>\jinja-before with .venv, <Lab>\jinja-after) and
# labs\jinja-843\claim.frozen.json. Runs the jinja oracle from two SHAs with the real .venv as read-only template.
param(
    [string]$Lab = (Join-Path $HOME "reprogate-lab"),
    [switch]$Yes
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$proj = Split-Path -Parent (Split-Path -Parent $here)
$src = Join-Path $Lab "jinja"
$handBefore = Join-Path $Lab "jinja-before"
$handAfter = Join-Path $Lab "jinja-after"
$venv = Join-Path $handBefore ".venv"
$py = Join-Path $venv "Scripts\python.exe"
$claim = Join-Path $proj "labs\jinja-843\claim.frozen.json"
$repro = Join-Path $proj "labs\jinja-843\repro.py"
$shaB = "81825095d24f4dbccb40f787fff70db54989b91c"
$shaA = "9a7dd7b28b50fd8adc019ab2702b50ae5c6ed782"
foreach ($p in @($src, $handBefore, $handAfter, $py, $claim, $repro)) {
    if (-not (Test-Path $p)) { Write-Host ("MISSING: " + $p); exit 2 }
}
if (-not $Yes) { Write-Host "Runs small vetted Python files on THIS computer. Re-run with -Yes."; exit 1 }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ev = Join-Path $here ("evidence-" + $stamp)
$tmp = Join-Path $env:TEMP ("reprogate-checkout-lab-" + $stamp)
New-Item -ItemType Directory -Force -Path $ev, $tmp | Out-Null

function TreeSha($dir) {
    & py -3.8 -c "import sys; from reprogate.runner import tree_hash; print(tree_hash(sys.argv[1])[0])" $dir
}
function ArchiveSha($sha, $name) {
    # independent reference: the bytes of the commit exactly as git stores them (git archive), no worktree involved
    $d = Join-Path $tmp $name
    $zip = Join-Path $tmp ($name + ".zip")
    & git -c core.autocrlf=false -C $src archive --format=zip -o $zip $sha
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, $d)
    return (TreeSha $d)
}

Push-Location $proj
try {
    $srcHeadBefore = (& git -C $src rev-parse HEAD)
    $srcTreeBefore = TreeSha $src
    $wtBefore = @(& git -C $src worktree list).Count
    Write-Host "=== oracle from two SHAs"
    & py -3.8 -m reprogate oracle --before-repo $src --before-sha $shaB --after-repo $src --after-sha $shaA --python $py --env-template $venv --claim $claim --reproducer $repro --out (Join-Path $ev "oracle") --allow-host-execution | Out-Host
    $wtAfter = @(& git -C $src worktree list).Count
    Write-Host ("SOURCE head_unchanged=" + ($srcHeadBefore -eq (& git -C $src rev-parse HEAD)) + " tree_unchanged=" + ($srcTreeBefore -eq (TreeSha $src)) + " worktrees_before=" + $wtBefore + " after=" + $wtAfter)
    foreach ($side in @("before", "after")) {
        $co = Get-Content (Join-Path $ev ("oracle\" + $side + "\checkout.json")) -Raw | ConvertFrom-Json
        $env1 = Get-Content (Join-Path $ev ("oracle\" + $side + "\environment.json")) -Raw | ConvertFrom-Json
        Write-Host ("CHECKOUT " + $side + " requested=" + $co.requested_sha + " head=" + $co.head_sha + " cleanup=" + $co.cleanup + " git.commit=" + $env1.git.commit)
        Write-Host ("TREE " + $side + " evaluated=" + $env1.repository_tree_sha256_before)
    }
    Write-Host ("TREE reference_archive_before=" + (ArchiveSha $shaB "arch_before"))
    Write-Host ("TREE reference_archive_after=" + (ArchiveSha $shaA "arch_after"))
    Write-Host ("TREE hand_made_jinja-before=" + (TreeSha $handBefore))
    Write-Host ("TREE hand_made_jinja-after=" + (TreeSha $handAfter))
    Write-Host "=== refused inputs"
    & py -3.8 -m reprogate run --repo $src --checkout-sha "81825095" --python $py --claim $claim --reproducer $repro --out (Join-Path $ev "refused_abbrev") --allow-host-execution
    Write-Host ("EXIT abbreviated=" + $LASTEXITCODE)
    & py -3.8 -m reprogate run --repo $src --checkout-sha "master" --python $py --claim $claim --reproducer $repro --out (Join-Path $ev "refused_branch") --allow-host-execution
    Write-Host ("EXIT branch=" + $LASTEXITCODE)
    Write-Host ("WORKTREES after refusals=" + @(& git -C $src worktree list).Count)
} finally {
    Pop-Location
}
Write-Host ""
Write-Host ("Evidence folder: " + $ev + "  (temp dir: " + $tmp + ")")
