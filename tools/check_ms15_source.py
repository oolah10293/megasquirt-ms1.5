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

iac_estimated_bytes=offset
# Additional conservative static check of the entire new output evaluator.
# This is an instruction-form and *approximate* branch-distance screen, NOT
# assembler validation. Direct-port owners must be exclusive by construction.
out_ops=dict.fromkeys(('lda','ldx','sta','cmp','bit','and','ora','add','clr','inc','mov'),3)
out_ops.update(dict.fromkeys(('bset','bclr'),2))
out_ops.update(dict.fromkeys(('brset','brclr','jmp'),3))
out_ops.update(dict.fromkeys(('beq','bne','bhs','blo','bls','bhi','bra'),2))
out_ops.update(dict.fromkeys(('clrh','coma','lsla','psha','pula','tpa','tap'),1))
out_labels={}
out_instructions=[]
offset=0
for raw in outputs.splitlines():
    code=raw.split(';',1)[0].strip()
    if not code: continue
    if code.endswith(':'):
        key=code[:-1].lower()
        assert key not in out_labels,('duplicate label',key)
        out_labels[key]=offset
        continue
    op,*args=code.split(None,1)
    op=op.lower()
    assert op in out_ops,('unsupported HC08 instruction form in output module',code)
    out_instructions.append((offset,op,args[0] if args else ''))
    offset+=out_ops[op]
out_branches={'brset','brclr','beq','bne','bhs','blo','bls','bhi','bra'}
for at,op,args in out_instructions:
    if op not in out_branches:continue
    target=args.split(',')[-1].strip().lower()
    assert target in out_labels,('undefined output-module branch target',op,target)
    delta=out_labels[target]-(at+out_ops[op])
    assert -128<=delta<=127,('relative output branch could exceed range',op,target,delta)
assert 'ms15_out_next' in out_labels and 'ms15_out_eval' in out_labels
assert 'ms15_out_advance' in out_labels
assert re.search(r'(?im)^\s*clrh\b',outputs), 'HX must be cleared before ROM indexed lookup'
normal,sep,handlers=outputs.partition('; Fast native Squirt LED handlers')
assert sep and all(name+':' in handlers for name in
                   ('MS15_IL_ON1','MS15_IL_ON2','MS15_IL_OFF'))
pin_writes=re.findall(
    r'(?im)^\s*(bset|bclr)\s+(sled|wled|aled|output1|output2|iasc),'
    r'(portc|porta)\b',normal)
for bit,port in (('sled','portc'),('wled','portc'),('aled','portc'),
                 ('output1','porta'),('output2','porta'),('iasc','porta')):
    assert sorted(op.lower() for op,b,p in pin_writes
                  if b.lower()==bit and p.lower()==port)==['bclr','bset'],bit
assert len(pin_writes)==12,('Unexpected primary output writer',pin_writes)
# The original relative injector IRQ branch spans contain only JMP hooks.
assert not re.search(r'(?im)^\s*(bset|bclr)\s+(sled|wled|aled|coila|coilb),portc\b',active),(
    'Original IRQ still has an unguarded LED write')
native_pin_writes=re.findall(r'(?im)^\s*(bset|bclr)\s+(sled|wled|aled),portc\b',handlers)
for pin in ('sled','wled','aled'):
    assert sum(1 for op,p in native_pin_writes if p.lower()==pin and op.lower()=='bset')==2,pin
    assert sum(1 for op,p in native_pin_writes if p.lower()==pin and op.lower()=='bclr')==1,pin
assert len(native_pin_writes)==9,('Unexpected fast LED writer',native_pin_writes)
for event,on in (('ON1',True),('ON2',True),('OFF',False)):
    assert active.count('jmp     MS15_IL_'+event)==1,event
    assert active.count('ILE_RET_'+event+':')==1,event
    assert handlers.count('MS15_IL_'+event+':')==1,event
    assert handlers.count('jmp     ILE_RET_'+event)==1,event
    for idx,pin in enumerate(('sled','wled','aled')):
        stmt='bset' if on else 'bclr'
        matcher=re.compile(
            r'(?im)^\s*lda\s+ms15_out'+str(idx)+r'_mode_f\s*'
            r'cmp\s+#5T\s*bne\s+IL_'+event+'_'+str(idx)+r'\s*'
            +stmt+r'\s+'+pin+r',portc\s*IL_'+event+'_'+str(idx)+r':')
        assert matcher.search(handlers),('unprotected fast LED handler',event,pin)
    body=handlers.split('MS15_IL_'+event+':',1)[1].split('jmp     ILE_RET_'+event,1)[0]
    assert re.search(r'(?im)^\s*psha\s+tpa\s+psha\s+',body)
    assert re.search(r'(?im)^\s*pula\s+tap\s+pula\s*$',body)

assert not re.search(r'(?im)^\s*bclr\s+iasc,porta\b',active),(
    'Legacy PWM idle FIDLE writer was not removed')
assert 'ms15_out3_mode_f' in active and 'DO_FAN_Check:' in active
# Native original MegaSquirt LED modes are in addition to sensor logic.
for name in ('M15_EVT_SQUIRT:', 'M15_EVT_WARM:', 'M15_EVT_ACCEL:'):
    assert name in outputs,name
assert 'brset   firing1,squirt,M15_EVT_ACTIVE' in outputs
assert 'brset   firing2,squirt,M15_EVT_ACTIVE' in outputs
assert 'brset   warmup,engine,M15_EVT_ACTIVE' in outputs
assert 'brset   TPSAEN,engine,M15_EVT_ACTIVE' in outputs


print("PASS: source-only pin writers, stepper/output RAM aliases and estimated branch spans")
print("Output aliases:", {k:hex(addresses[v]) for k,v in output_aliases.items()})
print("ROM screen:", len(instructions), "IAC instructions;", iac_estimated_bytes, "estimated bytes (NOT assembled)")
print("Output ROM screen:",len(out_instructions),"instructions;",offset,"estimated bytes (NOT assembled)")
print("State locations:", {name:hex(addresses[old]) for name,old in aliases.items()})
print("NOT TESTED: assembly, map/ROM limits, stack, motor behavior, injector jitter, safety.")
