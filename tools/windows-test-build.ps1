# Test assembly of original MS1/Extra 029y4a and MS1.5 WIP.
# Runs only on disposable Windows GitHub Actions runner.
# IMPORTANT: test image is NOT safe to flash or deploy to an engine.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$working = Join-Path $env:RUNNER_TEMP 'ms15-assembly'
$results = Join-Path $repo 'test-build-results'
New-Item -ItemType Directory -Force -Path $working,$results | Out-Null
$zip = Join-Path $working '029y4a.zip'
$expected = '212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790'
$urls = @(
  'https://www.msextra.com/doc/ms1extra/Downloads/029y4a.zip',
  'https://msextra.com/doc/ms1extra/Downloads/029y4a.zip',
  'https://forum.motorkontrolle.de/download/file.php?id=1527'
)
$gotZip = $false
foreach ($url in $urls) {
  try {
    Write-Host "Downloading official 029y4a source: $url"
    Invoke-WebRequest -Uri $url -OutFile $zip -TimeoutSec 50 -MaximumRedirection 8 -UseBasicParsing
    $hash = (Get-FileHash -Algorithm SHA256 $zip).Hash.ToLowerInvariant()
    Write-Host "Source ZIP SHA256: $hash"
    if ($hash -eq $expected) { $gotZip = $true; break }
    Write-Warning 'Downloaded ZIP does not match the uploaded source archive. Trying next URL.'
  } catch {
    Write-Warning $_.Exception.Message
  }
}
if (-not $gotZip) { throw 'No archive source URL returned bytes matching the uploaded ZIP SHA256. No assembly attempted.' }

$extract = Join-Path $working 'source'
Expand-Archive -Path $zip -DestinationPath $extract -Force
$tree = Join-Path $extract '029y4a'
$src = Join-Path $tree 'src'
$assembler = Join-Path $src 'CASM08Z.EXE'
if (-not (Test-Path $assembler)) { throw 'CASM08Z.EXE missing from official source ZIP' }

function Invoke-OriginalAssembler([string]$name) {
  $generated = Join-Path $src 'msns-extra.s19'
  if (Test-Path $generated) { Remove-Item $generated -Force }
  Write-Host "Running original CASM08Z.EXE for $name"
  $p = Start-Process -FilePath $assembler -ArgumentList @('msns-extra.asm','S','L','I','M') -WorkingDirectory $src -Wait -PassThru
  Write-Host "CASM08Z exit code: $($p.ExitCode)"
  Get-ChildItem $src | Where-Object { $_.Name -match '^(msns-extra|error|errors).*\.(s19|lst|map|err|log)$' } |
    ForEach-Object { Write-Host "Assembler result: $($_.Name) $($_.Length) bytes" }
  if ($p.ExitCode -ne 0) { throw "CASM08Z failed on $name (exit code $($p.ExitCode))" }
  if (-not (Test-Path $generated)) { throw "Assembler did not produce msns-extra.s19 on $name" }
  Copy-Item $generated (Join-Path $results "$name.s19") -Force
  foreach ($ext in 'lst','map','err','log') {
    $path = Join-Path $src "msns-extra.$ext"
    if (Test-Path $path) { Copy-Item $path (Join-Path $results "$name.$ext") -Force }
  }
}
Invoke-OriginalAssembler 'baseline'

# Do not publish a modified copy of the third-party original source.
# Only include the two original new MS1.5 include files and integration patch.
foreach ($file in 'ms15_defs.inc','ms15_iac.inc') {
  $inputFile = Join-Path $repo "firmware\$file"
  $destFile = Join-Path $src $file
  $t = [System.IO.File]::ReadAllText($inputFile)
  [System.IO.File]::WriteAllText($destFile, ($t -replace "\r?\n", "`r`n"), [System.Text.Encoding]::ASCII)
}
$patch = Join-Path $env:ProgramFiles 'Git\usr\bin\patch.exe'
if (-not (Test-Path $patch)) { throw 'GNU patch not found on Windows runner; cannot validate source integration.' }
Push-Location $tree
try {
  & $patch --binary --forward -p1 -i (Join-Path $repo 'patches\ms15-on-029y4a-wip.patch')
  if ($LASTEXITCODE -ne 0) { throw "MS1.5 patch failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }

# Run only STATIC checks: no hardware interaction.
python (Join-Path $repo 'tools\check_ms15_source.py') $src
if ($LASTEXITCODE -ne 0) { throw "Static checker failed: $LASTEXITCODE" }

Invoke-OriginalAssembler 'MS15-UNVALIDATED-TEST-IMAGE'

# Compare map regions and ensure bootloader/calibration image remained unchanged.
@'
from pathlib import Path
root = Path("test-build-results")
def parse(path):
    memory = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("S1"):
            continue
        n = int(line[2:4], 16)
        address = int(line[4:8], 16)
        data = bytes.fromhex(line[8:8 + (n - 3) * 2])
        for i, v in enumerate(data):
            assert address + i not in memory, (path, hex(address+i))
            memory[address+i] = v
    return memory
before = parse(root / "baseline.s19")
after = parse(root / "MS15-UNVALIDATED-TEST-IMAGE.s19")
assert before and after
high_before = {k:v for k,v in before.items() if k >= 0xE000}
high_after = {k:v for k,v in after.items() if k >= 0xE000}
assert high_before == high_after, "Bootloader or calibration pages differ from baseline assembly"
main_keys = [k for k in after if 0x8128 <= k < 0xE000]
assert main_keys and max(main_keys) <= 0xDFFF, "Main code extends past flash boundary"
assert before != after, "No code delta was generated"
report = [
    f"Baseline S-record programmed bytes: {len(before)}",
    f"Test S-record programmed bytes: {len(after)}",
    f"Main-code final occupied address: 0x{max(main_keys):04X}",
    f"Calibration/bootloader bytes >= E000: {len(high_before)} (identical)",
    "TEST ASSEMBLY ONLY. NOT VALIDATED OR SAFE TO FLASH.",
]
print("\n".join(report))
(root / "REPORT.txt").write_text("\n".join(report) + "\n")
'@ | Set-Content -Encoding ascii (Join-Path $repo 'check_built_image.py')
Push-Location $repo
try {
  python .\check_built_image.py
  if ($LASTEXITCODE -ne 0) { throw "Image-space verification failed: $LASTEXITCODE" }
} finally { Pop-Location }
Write-Host 'Completed test assembly. DO NOT FLASH image before actual validation.'
