#!/usr/bin/env python3
"""Static-only validation of MS1.5 TunerStudio configuration; NEVER builds firmware.

Usage:
    python tools/check_ms15_tuning.py /path/to/patched/029y4a
Original 029y4a must be patched with both WIP integration and tuning
addendum patches; the tuning INI patch must also have been applied.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
ini = (root / "msns-extra.ini").read_text(errors="replace")
asm = (root / "src" / "msns-extra.asm").read_text(errors="replace")
iac = (root / "src" / "ms15_iac.inc").read_text(errors="replace")
defs = (root / "src" / "ms15_defs.inc").read_text(errors="replace")

signature = "MS1/Extra format MS15_003 ******"
assert len(signature.encode('ascii')) == 32
assert signature.startswith('MS1/Extra format ')
assert signature != 'MS1/Extra format 029y3 *********'
assert f'signature    = "{signature}"' in ini
assert f"db   '{signature}'" in asm
assert "MS1.5 TEST rev 0.1 *************" in asm

# Parse page 9 scalar/array definitions; ensure five new calibration
# bytes occupy exclusive offsets and are represented in the firmware.
page = 0
occupied = {}
for line in ini.splitlines():
    line = line.split(";", 1)[0]
    match = re.match(r"\s*page\s*=\s*(\d+)", line)
    if match:
        page = int(match.group(1))
        continue
    if page != 9:
        continue
    match = re.match(r"\s*(\w+)\s*=\s*(scalar|array|bits),\s*U(08|16),\s*(\d+)", line, re.I)
    if not match:
        continue
    name, typ, bits, at = match.group(1), match.group(2).lower(), int(match.group(3)), int(match.group(4))
    count = bits // 8
    if typ == "array":
        shape = re.search(r"\[\s*(\d+)(?:x(\d+))?", line)
        assert shape, f"Array without shape: {name}"
        count *= int(shape.group(1)) * (int(shape.group(2)) if shape.group(2) else 1)
    if typ == "bits" and at < 113:
        continue  # original low-offset feature-bit aliases share bytes
    for i in range(count):
        pos = at + i
        # Legacy CELSIUS/Fahrenheit and MAP/MAF branches deliberately
        # overlap at low offsets; only reject conflicts in our new 113..117 range.
        if pos >= 113:
            assert pos not in occupied, f"MS1.5 calibration overlap at offset {pos}: {name}/{occupied.get(pos)}"
        occupied[pos] = name

assert [occupied[k] for k in range(113,118)] == [
    "iacStepLowMs", "iacHomeSteps", "iacHomeSteps", "iacMaxSteps", "iacMaxSteps"]
# Output rules are seven bytes per physical pin: MODE, SRC_A, ON_A,
# OFF_A, SRC_B, ON_B, OFF_B. Each occupies a distinct page-9 offset.
out_fields=('Mode','SourceA','OnA','OffA','SourceB','OnB','OffB')
for idx in range(6):
    for ofs,field in enumerate(out_fields):
        pos=118+7*idx+ofs
        expected=f'ms15Out{idx}{field}'
        assert occupied.get(pos)==expected,(pos,occupied.get(pos),expected)
        rom_field=('mode','src_a','on_a','off_a','src_b','on_b','off_b')[ofs]
        assert re.search(r'(?mi)^ms15_out'+str(idx)+'_'+rom_field+r'_f:\s*db\s+\d+T',asm),(
            idx,rom_field)
assert max(occupied)==159
assert len({k for k in occupied if 118<=k<=159})==42
for idx,name in enumerate(('LED17','LED18','LED19','JS2','JS3','FIDLE')):
    assert re.search(r'(?im)^\s*subMenu\s*=\s*ms15Output'+str(idx)+r'\b',ini),(idx,'menu')
    assert re.search(r'(?im)^\s*dialog\s*=\s*ms15Output'+str(idx)+r'\s*,',ini),(idx,'dialog')
# Native LED event functions are available only on the three front LEDs.
mode_defaults=(5,6,7,4,0,0)
for idx,mode in enumerate(mode_defaults):
    assert re.search(r'(?mi)^ms15_out'+str(idx)+r'_mode_f:\s*db\s+'+str(mode)+r'T\b',asm),(
        'unexpected output default',idx,mode)
    decl=re.search(r'(?mi)^\s*ms15Out'+str(idx)+r'Mode\s*=\s*bits,\s*U08,\s*\d+,\s*\[0:2\],\s*(.*)

assert all(k < 189 for k in occupied)
labels = ["ms15_step_low_f", "ms15_home_hi_f", "ms15_home_lo_f",
          "ms15_max_hi_f", "ms15_max_lo_f"]
for label in labels:
    assert re.search(r"(?mi)^" + label + r":\s+db\s+", asm), label
    assert label in iac, f"Firmware stepper service does not use {label}"
assert "MS15_INIT_DONE" in defs and "MS15_INIT_DONE" in iac

# The original idlefreq byte is not a motor pulse frequency.
assert re.search(r"(?m)^\s*iacDemandLimit\s*=\s*scalar,\s*U08,\s*011\b", ini)
assert "Idle Valve Frequency" not in ini.split('dialog = idleControl, "MS1.5 Stepper IAC"')[1].split("dialog =", 1)[0]
assert 'subMenu = ms15FanControl' in ini and 'dialog = ms15FanControl' in ini
assert re.search(r"(?m)^\s*subMenu\s*=\s*idleControl\b", ini)
for unused in ("subMenu = WaterInj,", "subMenu = NosSystem,", "subMenu = boostControl,", "subMenu = outputs,"):
    assert not any(x.strip().startswith(unused) for x in ini.splitlines()), unused

print("PASS: unique signature, page-9 byte allocation, UI mapping and source symbol alignment")
print("No TunerStudio GUI test or firmware build was performed.")
,ini)
    assert decl,('output mode menu missing',idx)
    opts=re.findall(r'"([^"]+)"',decl.group(1))
    if idx < 3:
        assert len(opts)==8 and opts[4].startswith('Reserved'),(idx,opts)
        assert opts[5:]==['Squirt (injector activity)','Warmup enrichment',
                          'Acceleration enrichment'],(idx,opts)
    elif idx==3:
        assert len(opts)==5 and opts[4]=='Cooling fan',(idx,opts)
    else:
        assert len(opts)==4,(idx,opts)
assert 'include "ms15_outputs.inc"' in iac

assert all(k < 189 for k in occupied)
labels = ["ms15_step_low_f", "ms15_home_hi_f", "ms15_home_lo_f",
          "ms15_max_hi_f", "ms15_max_lo_f"]
for label in labels:
    assert re.search(r"(?mi)^" + label + r":\s+db\s+", asm), label
    assert label in iac, f"Firmware stepper service does not use {label}"
assert "MS15_INIT_DONE" in defs and "MS15_INIT_DONE" in iac

# The original idlefreq byte is not a motor pulse frequency.
assert re.search(r"(?m)^\s*iacDemandLimit\s*=\s*scalar,\s*U08,\s*011\b", ini)
assert "Idle Valve Frequency" not in ini.split('dialog = idleControl, "MS1.5 Stepper IAC"')[1].split("dialog =", 1)[0]
assert 'subMenu = ms15FanControl' in ini and 'dialog = ms15FanControl' in ini
assert re.search(r"(?m)^\s*subMenu\s*=\s*idleControl\b", ini)
for unused in ("subMenu = WaterInj,", "subMenu = NosSystem,", "subMenu = boostControl,", "subMenu = outputs,"):
    assert not any(x.strip().startswith(unused) for x in ini.splitlines()), unused

print("PASS: unique signature, page-9 byte allocation, UI mapping and source symbol alignment")
print("No TunerStudio GUI test or firmware build was performed.")
