#!/usr/bin/env python3
"""Stage 1 ignition deletion from 029y4a-derived MS1.5 assembly. SOURCE ONLY.

Apply after existing 029y4a integration and tuning patches, on a working copy.
This script neither assembles nor builds firmware. Fails on unexpected source
layout/branch consumers. The firmware is NOT safe to flash after this stage:
spark ISR, output control, shared RPM paths and tune UI still need review.
"""
from pathlib import Path
import re
import sys


def transform(source: str) -> str:
    eol = '\r\n' if '\r\n' in source else '\n'
    lines = source.splitlines(keepends=True)

    def find(label: str) -> int:
        found = [i for i, line in enumerate(lines)
                 if re.match(r'^' + re.escape(label) + r':', line, re.I)]
        assert len(found) == 1, f'Expected one {label}, got {len(found)}'
        return found[0]

    cfg_start, cfg_end = find('chk_out'), find('start_adc')
    spk_start, spk_end = find('spark_lookup'), find('CheckSoftLimit')
    assert cfg_start < cfg_end < spk_start < spk_end
    assert 170 <= cfg_end - cfg_start <= 220
    assert 420 <= spk_end - spk_start <= 480

    # All labels inside removed ranges must be locally referenced, apart
    # from chk_out and the three fuel-path branches into spark_lookup.
    def defined_labels(block):
        return {m.group(1).lower() for line in block
                if (m := re.match(r'^([A-Za-z_]\w*):', line))}
    removed = defined_labels(lines[cfg_start:cfg_end]) | defined_labels(lines[spk_start:spk_end])
    assert {'spark_lookup', 'check_msns', 'check10', 'sttablelookup'} <= removed
    external = []
    for idx, line in enumerate(lines):
        if cfg_start <= idx < cfg_end or spk_start <= idx < spk_end:
            continue
        instruction = line.split(';', 1)[0].strip()
        if not instruction or instruction.startswith('*'):
            continue
        for label in removed:
            if re.search(r'(?i)\b' + re.escape(label) + r'\b', instruction):
                external.append((idx, label, instruction))
    assert len(external) == 4, f'Unexpected references to deleted code: {external}'
    assert sorted(lab for _, lab, _ in external) == ['chk_out'] + ['spark_lookup'] * 3, external
    assert any(re.match(r'\s*brclr\s+DUALEDIS,personality,chk_out', ins, re.I)
               for _, _, ins in external), external

    # Retain fuel calculation and the existing shared limiter/output tail.
    # Absolute JMP replaces BRA as required for the longer branch span.
    adjusted = 0
    for idx, label, _ in external:
        if label != 'spark_lookup':
            continue
        m = re.match(r'^(\s*)(?:jmp|bra)(\s+)spark_lookup\b(.*?)(\r?\n)?$', lines[idx], re.I)
        assert m, f'Unexpected fuel-to-spark handoff: {lines[idx]!r}'
        lines[idx] = m.group(1) + 'jmp' + m.group(2) + 'CheckSoftLimit' + (m.group(3) or '') + (m.group(4) or '')
        adjusted += 1
    assert adjusted == 3

    # Preserve the ONLY two non-ignition conflicts in the original block.
    # Error codes 5/6 remain; MSNS/LED17/FIDLE ignition checks disappear.
    # turnallsparkoff stays temporarily because other spark paths remain.
    checks = '''chk_out:
        ; MS1.5 FUEL ONLY: ignition-output validation removed.
        ; Keep original nonignition X2 fan/water conflict (error 5).
        lda     feature3_f
        bit     #WaterInjb
        beq     ms15_check_nitrous
        brclr   X2_FAN,outputpins,ms15_check_nitrous
        mov     #5,tmp4
        bset    config_error,feature2
        bra     ms15_checks_done
ms15_check_nitrous:
        ; Keep original nitrous/water conflict (error 6).
        brclr   Nitrous,feature1,ms15_checks_done
        lda     feature3_f
        bit     #WaterInjb
        beq     ms15_checks_done
        mov     #6,tmp4
        bset    config_error,feature2
ms15_checks_done:
        ; Temporary safety call: remaining spark paths are not yet removed.
        jsr     turnallsparkoff
'''.replace('\n', eol)
    updated = ''.join(lines[:cfg_start] + [checks] + lines[cfg_end:spk_start] + lines[spk_end:])
    assert 'spark_lookup:' not in updated
    assert 'STTABLELOOKUP:' not in updated
    assert 'check_msns:' not in updated
    assert re.search(r'(?mi)^CheckSoftLimit:', updated)
    assert re.search(r'(?mi)^start_adc:', updated)
    return updated


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python tools/remove_ms15_ignition_stage1.py /path/to/patched/029y4a/src/msns-extra.asm')
    path = Path(sys.argv[1])
    source = path.read_bytes().decode('latin-1')
    changed = transform(source)
    assert changed != source
    path.write_bytes(changed.encode('latin-1'))
    print('SOURCE ONLY: spark lookup and ignition configuration removed; NOT built/flashed')


if __name__ == '__main__':
    main()
