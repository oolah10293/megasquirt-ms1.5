#!/usr/bin/env python3
"""Source-only MS1.5 checks. NOT an assembler or firmware build.

AI/AGENT HANDOFF: Read docs/CURRENT-HANDOFF.md and AGENTS.md and inspect
current Git commits before editing. Do not build or flash without explicit
owner authorization.

Usage: python tools/check_ms15_source.py /path/to/extracted/029y4a/src

Apply patches/ms15-on-029y4a-wip.patch with GNU patch --binary -p1
from extracted 029y4a/ and copy both firmware/*.inc to its src/ first.
"""
from pathlib import Path
import re
import sys

src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
asm = (src / "msns-extra.asm").read_text(errors="replace")
header = (src / "msns-extra.h").read_text(errors="replace")
defs = (src / "ms15_defs.inc").read_text(errors="replace")
iac = (src / "ms15_iac.inc").read_text(errors="replace")
outputs = (src / "ms15_outputs.inc").read_text(errors="replace")

# Account for every DS byte, including unlabeled continuation declarations.
ram, addresses = 0x40, {}
for line in header.splitlines():
    if line.strip().lower().startswith("ms_ram_end:"):
        break
    field = line.split(";", 1)[0]
    match = re.search(r"\bds\s+(\d+)(?:[tT])?\b", field, re.I)
    if match:
        label = field[: match.start()].strip().rstrip(":")
        if label:
            addresses[label.lower()] = ram
        ram += int(match.group(1))
assert ram == 0x112, f"RAM layout moved: {ram:#x}"

aliases = {}
active = "\n".join(row.split(";", 1)[0] for row in asm.splitlines())
for row in defs.splitlines():
    match = re.match(r"\s*(MS15_(?:STATE|POS_L|POS_H|TARGET_L|TARGET_H|HOME_L|HOME_H|WAIT))\s+equ\s+(\w+)", row, re.I)
    if match:
        symbol, old = match.group(1), match.group(2).lower()
        assert old in addresses and addresses[old] <= 0xFF, (symbol, old)
        assert not re.search(r"\b" + re.escape(old) + r"\b", active, re.I), (symbol, "legacy reference remains")
        aliases[symbol] = old
assert len(aliases) == 8 and len(set(aliases.values())) == 8
output_aliases={}
for row in defs.splitlines():
    match=re.match(r'\s*(MS15_OUT_\w+)\s+equ\s+(\w+)',row,re.I)
    if not match: continue
    symbol,old=match.group(1),match.group(2).lower()
    assert old in addresses and addresses[old]<=0xFF,(symbol,old)
    assert not re.search(r'\b'+re.escape(old)+r'\b',active,re.I),(
        symbol,'legacy RAM owner still writes/reads',old)
    output_aliases[symbol]=old
assert len(output_aliases)==16,output_aliases
assert len(set(output_aliases.values()))==16
assert set(output_aliases.values()).isdisjoint(aliases.values())
assert 'MS15_OUTPUT_SERVICE:' in outputs
assert 'include "ms15_outputs.inc"' in iac
assert 'MS15_IAC_CONTINUE:' in iac
assert 'inc     MS15_OUT_CLOCK' in asm

# ADC history is an indexed array: sta lmap,x writes lmat..lego without
# naming those symbols. These five bytes belong to MS1.5 only after that
# obsolete copy is removed. A direct lmap store (offset zero) is retained.
history = range(addresses['lmap'], addresses['lego'] + 1)
assert list(history) == list(range(0x77, 0x7D))
history_refs = [line.strip().lower() for line in active.splitlines()
                if re.search(r'\blmap\b', line, re.I)]
assert len(history_refs) == 1 and re.fullmatch(r'sta\s+lmap', history_refs[0]), (
    'ADC history access conflicts with stepper RAM', history_refs)

# Audit application indexed writers as well as direct aliases. This is a
# deliberately narrow source guard, not a general assembly dataflow proof.
# Reject a new writer until its destination range has been reviewed.
indexed = []
for line in active.splitlines():
    match = re.match(r'\s*(sta|stx|sthx|clr|inc|dec|com|neg|asl|lsl|lsr|rol|ror)\s+(.*?,\s*x\+?)\s*$', line, re.I)
    if match:
        op, operand = match.group(1).lower(), re.sub(r'\s+', '', match.group(2).lower())
        assert op == 'sta' and operand in {',x', 'map,x', 've_r,x'}, (
            'Unaudited indexed RAM writer', line)
        indexed.append(operand)
assert indexed.count(',x') == 1
assert re.search(r'ClearRAM:\s*lda\s+#\$32\s*sta\s*,x\s*aix\s+#1\s*cphx\s+#ram_last\+1\s*bne\s+ClearRAM', active, re.I)
assert active.index('ClearRAM:') < active.index('mov     #$01,MS15_STATE')
assert indexed.count('map,x') == 1
# Runtime ADC input array (offsets 0..5) and calibration page buffer must
# remain disjoint from every stepper byte. The original header's page
# buffer begins immediately after ms_ram_end (0x112).
stepper = {addresses[old] for old in aliases.values()}
assert not stepper.intersection(range(addresses['map'], addresses['map'] + 6))
assert all(a < ram for a in stepper)
assert re.search(r'ms_ram_end:\s*ms_rf_start:\s*VE_r\s+rmb\s+\$90',
                 '\n'.join(x.split(';', 1)[0] for x in header.splitlines()), re.I)
# Preserve the live ADC smoothing path; only the unused history copy goes.
assert re.search(r'Normal_ADSEL:\s*tax\s*lda\s+adr\s*add\s+map,x\s*rora\s*sta\s+map,x', active, re.I)

writers = re.findall(r"^\s*(bset|bclr)\s+(water2|water|output1)\s*,\s*porta\b", active, re.I | re.M)
assert len(writers) == 2 and {(x.lower(), y.lower()) for x,y in writers} == {
    ("bset", "output1"), ("bclr", "output1")}, writers
assert "brset   water,porta,SKIP_ALL_O2" not in active
assert "        jmp    MS15_IAC_SERVICE" in asm
assert "        bset     MS15_TICK,MS15_STATE" in asm
assert 'include "ms15_defs.inc"' in asm and 'include "ms15_iac.inc"' in asm

# Coarse relative branch screening, not real assembled sizes or cycles.
sizes = dict.fromkeys(("bset","bclr","lda","sta","cmp","dec","inc","clr"), 2)
sizes.update(dict.fromkeys(("brset","brclr","jmp","mov"), 3))
sizes.update(dict.fromkeys(("bra","bhi","blo","bls","bne","beq"), 2))
sizes.update({"lsla":1,"rola":1,"ora":2,"bhs":2})
branches = {"brset","brclr","bra","bhi","blo","bls","bne","beq","bhs"}
labels, instructions, offset = {}, [], 0
for row in iac.splitlines():
    line = row.split(";", 1)[0].strip()
    if not line:
        continue
    if line.endswith(":"):
        labels[line[:-1].lower()] = offset
        continue
    mnemonic, *other = line.split(None, 1)
    mnemonic = mnemonic.lower()
    if mnemonic == "include" and '"ms15_outputs.inc"' in line:
        continue
    assert mnemonic in sizes, ("unexpected instruction", line)
    arg = other[0] if other else ""
    instructions.append((offset, mnemonic, arg))
    offset += sizes[mnemonic]
for at, mnemonic, arg in instructions:
    if mnemonic not in branches:
        continue
    label = arg.split(",")[-1].strip().lower()
    if label in labels:
        delta = labels[label] - (at + sizes[mnemonic])
        assert -128 <= delta <= 127, (mnemonic, label, delta)

print("PASS: source-only pin writers, stepper/output RAM aliases and estimated branch spans")
print("Output aliases:", {k:hex(addresses[v]) for k,v in output_aliases.items()})
print("ROM screen:", len(instructions), "IAC instructions;", offset, "estimated bytes (NOT assembled)")
print("State locations:", {name:hex(addresses[old]) for name,old in aliases.items()})
print("NOT TESTED: assembly, map/ROM limits, stack, motor behavior, injector jitter, safety.")
