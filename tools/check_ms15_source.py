#!/usr/bin/env python3
"""Source-only MS1.5 checks. NOT an assembler or firmware build.

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
sizes.update({"lsla":1,"rola":1})
branches = {"brset","brclr","bra","bhi","blo","bls","bne","beq"}
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

print("PASS: source-only pin writers, RAM aliases and estimated branch spans")
print("ROM screen:", len(instructions), "IAC instructions;", offset, "estimated bytes (NOT assembled)")
print("State locations:", {name:hex(addresses[old]) for name,old in aliases.items()})
print("NOT TESTED: assembly, map/ROM limits, stack, motor behavior, injector jitter, safety.")
