# Authorized bench-only CASM08Z assembly of FINAL MS1.5 fuel-only source and INI.
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
  'https://forum.motorkontrolle.de/download/file.php?id=1527',
  'https://www.msextra.com/doc/ms1extra/Downloads/029y4a.zip',
  'https://msextra.com/doc/ms1extra/Downloads/029y4a.zip'
)
$gotZip = $false
foreach ($url in $urls) {
  try {
    Write-Host "Downloading official 029y4a source: $url"
    & curl.exe --fail --location --silent --show-error --max-time 18 --connect-timeout 5 --output $zip $url
    if ($LASTEXITCODE -ne 0) { throw "curl failed: $LASTEXITCODE" }
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
  $p = Start-Process -FilePath $assembler -ArgumentList @('msns-extra.asm','S','L','I','M') -WorkingDirectory $src -PassThru
  Start-Sleep -Seconds 6
  $p.Refresh()
  Write-Host "CASM08Z process: HasExited=$($p.HasExited), MainWindowHandle=$($p.MainWindowHandle), MainWindowTitle='$($p.MainWindowTitle)'"
  Get-ChildItem -Path $src -File | Where-Object { $_.Name -match '(msns-extra|casm|error)' } |
    ForEach-Object { Write-Host "At 6s: $($_.Name), $($_.Length) bytes, modified=$($_.LastWriteTimeUtc)" }
  if (-not $p.HasExited) {
    try {
      $w = New-Object -ComObject WScript.Shell
      $activated = $w.AppActivate($p.Id)
      Write-Host "AppActivate returned: $activated"
      if ($activated) {
        $w.SendKeys('{ENTER}')
        Write-Host "Sent ENTER to CASM08Z window"
      }
    } catch { Write-Warning "Window interaction unavailable: $($_.Exception.Message)" }
  }
  if (-not $p.WaitForExit(15000)) {
    $p.Kill()
    throw "CASM08Z did not exit after 6-second inspection and 15-second window check on $name"
  }
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
foreach ($file in 'ms15_defs.inc','ms15_iac.inc','ms15_outputs.inc') {
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
  & $patch --binary --forward -p1 -i (Join-Path $repo 'patches\ms15-tuning-firmware-addendum.patch')
  if ($LASTEXITCODE -ne 0) { throw "Tuning firmware addendum patch failed with exit code $LASTEXITCODE" }
  & $patch --binary --forward -p1 -i (Join-Path $repo 'patches\ms15-tuning-ini.patch')
  if ($LASTEXITCODE -ne 0) { throw "TunerStudio INI patch failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }

# Fuel-only source transform and menu cleanup. Owner explicitly authorized
# a test assembly on 2026-11-10; this job NEVER flashes hardware.
# Keep the *actual fully patched* preclean assembly/INI in the source tree
# for the integrated regression test; no assembler has been called for this
# modified source yet. The original baseline above is unchanged.
$env:MS15_INTEGRATED_ASM = Join-Path $src 'ms15-integrated-source-preclean.asm'
$env:MS15_INTEGRATED_INI = Join-Path $tree 'ms15-integrated-preclean.ini'
$env:MS15_REQUIRE_INTEGRATED = '1'
Copy-Item (Join-Path $src 'msns-extra.asm') $env:MS15_INTEGRATED_ASM -Force
Copy-Item (Join-Path $tree 'msns-extra.ini') $env:MS15_INTEGRATED_INI -Force
$env:MS15_ORIGINAL_ZIP = $zip
$env:MS15_TUNING_INI = Join-Path $tree 'msns-extra.ini'
python -m unittest discover -s (Join-Path $repo 'tests') -p 'test_ms15_fuel_only_full.py' -v
if ($LASTEXITCODE -ne 0) { throw "Fuel-only regression suite failed before transformation: $LASTEXITCODE" }
python (Join-Path $repo 'tools\remove_ms15_ignition_full.py') (Join-Path $src 'msns-extra.asm')
if ($LASTEXITCODE -ne 0) { throw "Fuel-only ignition removal failed: $LASTEXITCODE" }
python (Join-Path $repo 'tools\simplify_ms15_fuel_only_ini.py') (Join-Path $tree 'msns-extra.ini')
if ($LASTEXITCODE -ne 0) { throw "Fuel-only INI cleanup failed: $LASTEXITCODE" }

# The previous bench-image script stopped after ignition stage one.
# Current source cleanup must also remove launch/NOS/knock/boost code
# and its old TunerStudio dialog/help entries before any assembly.
python (Join-Path $repo 'tools\finalize_ms15_fuel_only.py') (Join-Path $src 'msns-extra.asm')
if ($LASTEXITCODE -ne 0) { throw "Full fuel-only source finalization failed: $LASTEXITCODE" }
python (Join-Path $repo 'tools\finalize_ms15_fuel_only_ini.py') (Join-Path $tree 'msns-extra.ini')
if ($LASTEXITCODE -ne 0) { throw "Full fuel-only INI finalization failed: $LASTEXITCODE" }
python -m unittest discover -s (Join-Path $repo 'tests') -p 'test_ms15_source_final_cleanup.py' -v
if ($LASTEXITCODE -ne 0) { throw "Integrated final fuel-only regression tests failed: $LASTEXITCODE" }


# Run only STATIC checks: no hardware interaction.
python (Join-Path $repo 'tools\check_ms15_source.py') $src
if ($LASTEXITCODE -ne 0) { throw "Static checker failed: $LASTEXITCODE" }
python (Join-Path $repo 'tools\check_ms15_tuning.py') $tree
if ($LASTEXITCODE -ne 0) { throw "Tuning/source consistency checker failed: $LASTEXITCODE" }

# This is the matching INI source for the newly assembled firmware, NOT a release.
Copy-Item (Join-Path $tree 'msns-extra.ini') (Join-Path $results 'MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED.ini') -Force
Invoke-OriginalAssembler 'MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED'

# Compare map regions and ensure bootloader/calibration image remained unchanged.
@'
from pathlib import Path
import sys

root = Path("test-build-results")
def parse(path):
    memory = {}
    for line in Path(path).read_text(errors="replace").splitlines():
        if not line.startswith("S1"):
            continue
        n = int(line[2:4], 16)
        raw = bytes.fromhex(line[4:])
        assert len(raw) == n and ((n + sum(raw)) & 255) == 255, f"Bad S19 checksum: {path}"
        a = int.from_bytes(raw[:2], "big")
        for i, b in enumerate(raw[2:-1]):
            assert a + i not in memory
            memory[a+i] = b
    assert memory, f"Empty S19: {path}"
    return memory

before = parse(root / "baseline.s19")
after = parse(root / "MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED.s19")
shipped = parse(sys.argv[1])
assert before == shipped, "Assembled original differs from shipped 029y4a image"
for name in ("baseline","MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED"):
    err = (root / (name+".err")).read_text(errors="replace")
    assert "Successful assembly - No errors." in err, f"{name} assembler reported errors: {err}"

# Code must stay below E000.
main_before = {k:v for k,v in before.items() if 0x8128 <= k < 0xE000}
main_after = {k:v for k,v in after.items() if 0x8128 <= k < 0xE000}
assert main_before and main_after and min(main_after) == 0x8128
last = max(main_after)
assert last <= 0xDFFF, f"Code overflow at {last:04X}"
assert before != after, "No MS1.5 code changes produced"

# Calibration, lookup and actual bootloader unchanged byte-for-byte.
# Page 9 new bytes: prior five IAC settings plus 6 seven-byte output records.
# Exactly 47 bytes at E871..E89F; original calibration and bootloader unchanged.
new_cal = set(range(0xE871, 0xE8A0))
expected_defaults = [4, 1, 104, 1, 64]
for n in range(6):
    expected_defaults += [4 if n==3 else 0] + [0]*6
assert len(expected_defaults)==47, expected_defaults
assert [after.get(k) for k in sorted(new_cal)] == expected_defaults, "Wrong IAC/output calibration defaults"
assert all(before.get(k) is None for k in new_cal), "Original source occupied planned new calibration addresses"
for lo, hi in ((0xE000,0xFAC3),(0xFB00,0x10000)):
    assert all(before.get(k)==after.get(k) for k in range(lo,hi) if k not in new_cal), f"Unexpected protected flash changes in {lo:04X}..{hi:04X}"
assert all(before.get(k)==after.get(k) for k in range(0xFAC3,0xFACA)), "Fixed vector header changed"
allowed = set()
relocations = 0
for index in range(18):
    a = 0xFACA + index*3
    assert before.get(a)==after.get(a)==0xCC, f"JMP opcode at {a:04X} changed"
    allowed.update((a+1,a+2))
    target = after[a+1]*256 + after[a+2]
    old_target = before[a+1]*256 + before[a+2]
    assert target in main_after, f"Vector {index} target {target:04X} outside application"
    if target != old_target: relocations+=1
assert 0xFACA + 18*3 == 0xFB00
high_changes = [k for k in before.keys()|after.keys() if k>=0xE000 and before.get(k)!=after.get(k)]
assert set(high_changes).issubset(allowed|new_cal), f"Unexpected high-memory differences: {high_changes}"
assert set(high_changes)&new_cal == new_cal, "Not all 47 page-9 calibration bytes were added"
signature = b"MS1/Extra format MS15_002 ******"
version = b"MS1.5 TEST rev 0.1 *************"
assert len(signature)==32 and len(version)==32
main_blob = bytes(after.get(k,0) for k in range(0x8128, 0xE000))
assert main_blob.count(signature)==1, "New 32-byte signature missing or duplicate"
assert main_blob.count(version)==1, "New 32-byte version missing or duplicate"
report = [
    "PASS: CASM08Z assembled both images without errors",
    "PASS: Baseline is byte-for-byte identical to shipped 029y4a S19",
    "PASS: Original calibration tables and bootloader unchanged except exactly 47 new page-9 bytes",
    "PASS: New tuning fields at E871-E89F: IAC 5 bytes + six 7-byte output records, JS2 fan default",
    "PASS: Firmware contains matching MS15_002 signature and 32-byte text version",
    f"PASS: {relocations} interrupt vectors correctly relocated ({len(high_changes)} address-byte changes)",
    f"Main-code end: baseline 0x{max(main_before):04X}; MS1.5 0x{last:04X}",
    f"Net occupied program growth: {len(main_after)-len(main_before)} bytes",
    f"Remaining contiguous flash addresses to DFFF: {0xDFFF-last}",
    "WARNING: UNVALIDATED TEST IMAGE. DO NOT FLASH OR USE ON AN ENGINE.",
    "Not yet tested: real-time injector timing, stack depth, IAC valve/homing safety or TunerStudio GUI/serial compatibility."
]
print("\n".join(report))
(root/"REPORT.txt").write_text("\n".join(report)+"\n")
from hashlib import sha256
for file in ('MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED.s19','MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED.ini'):
    path = root / file
    assert path.is_file(), f'Missing paired build result {path}'
    digest=sha256(path.read_bytes()).hexdigest()
    print(f'Paired file SHA256: {file} {digest}')
    with (root/'REPORT.txt').open('a') as out: out.write(f'{file} SHA256 {digest}\n')
'@ | Set-Content -Encoding ascii (Join-Path $repo 'check_built_image.py')
Push-Location $repo
try {
  python .\check_built_image.py (Join-Path $tree 'msns-extra.s19')
  if ($LASTEXITCODE -ne 0) { throw "Image-space verification failed: $LASTEXITCODE" }
} finally { Pop-Location }
Write-Host 'Completed test assembly. DO NOT FLASH image before actual validation.'
