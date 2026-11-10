#!/usr/bin/env python3
"""Source-only, checked fuel-only transformation for patched 029y4a assembler.

Run AFTER the existing integration and tuning patches on an extracted working
source tree. This does not assemble, build, flash, or package firmware.

The saved page-0 ignition personality remains unchanged for tune compatibility.
The MS1.5 application uses a zero runtime personality at startup and after
page-0 burns; spark decisions read that zero runtime value, not flash directly.
"""
from pathlib import Path
import re
import sys


def instruction(line: str) -> str:
    """Get an assembly instruction, excluding comments and whitespace."""
    return line.split(';', 1)[0].strip().lower()


def is_instruction(line: str, opcode: str, operand: str) -> bool:
    return re.fullmatch(rf'{re.escape(opcode)}\s+{re.escape(operand)}', instruction(line)) is not None


def transform(source: str) -> str:
    lines = source.splitlines(keepends=True)
    loads = [i for i, line in enumerate(lines) if is_instruction(line, 'lda', 'personality_f')]
    stores = [i for i, line in enumerate(lines) if is_instruction(line, 'sta', 'personality')]
    assert len(loads) == 4, f'Expected four live personality_f loads, found {len(loads)}'
    assert len(stores) == 2, f'Expected two runtime personality stores, found {len(stores)}'

    # Both flash-to-RAM copies are immediately preceded by the outputpins load.
    # Cover boot and page-0 burn; leaving either one intact can re-enable spark.
    copy_loads = []
    for i in loads:
        if i + 1 < len(lines) and is_instruction(lines[i + 1], 'sta', 'personality'):
            assert i >= 2
            assert is_instruction(lines[i - 2], 'lda', 'outputpins_f')
            assert is_instruction(lines[i - 1], 'sta', 'outputpins')
            copy_loads.append(i)
    assert len(copy_loads) == 2 and stores == [i+1 for i in copy_loads], (
        'Expected exactly two outputpins-adjacent personality copies', copy_loads, stores)

    # The two remaining direct flash checks are in the spark timing paths.
    # Require their exact nearby labels to avoid silently rewriting an
    # unrelated flash read if the upstream assembler changes.
    spark_loads = sorted(set(loads) - set(copy_loads))
    def nearest_label(idx: int) -> str:
        for j in range(idx - 1, -1, -1):
            line = instruction(lines[j])
            if re.fullmatch(r'[a-z_][\w]*:', line):
                return line[:-1]
        return ''
    assert [nearest_label(i) for i in spark_loads] == ['spark_lookup', 'nospkoff'], (
        'Unexpected direct-flash spark checks', [nearest_label(i) for i in spark_loads])

    replacements = {}
    for i in copy_loads:
        indent = re.match(r'\s*', lines[i]).group(0)
        # Preserve the original line ending instead of normalizing the source.
        ending = '\r\n' if lines[i].endswith('\r\n') else '\n'
        replacements[i] = indent + 'clr     personality     ; MS1.5: force runtime fuel-only mode' + ending
        replacements[i+1] = ''
    for i in spark_loads:
        replacements[i] = re.sub(r'(?i)\bpersonality_f\b', 'personality', lines[i], count=1)

    transformed = ''.join(replacements.get(i, line) for i, line in enumerate(lines))
    assert sum(is_instruction(line, 'clr', 'personality') for line in transformed.splitlines()) == 2
    assert sum(is_instruction(line, 'lda', 'personality') for line in transformed.splitlines()) >= 2
    assert not any(is_instruction(line, 'lda', 'personality_f') or is_instruction(line, 'sta', 'personality') for line in transformed.splitlines())
    # Keep the original check_msns/error machinery in place: it now evaluates
    # the zero runtime personality; subsequent conflict checks still run.
    assert re.search(r'(?mi)^\s*check_msns:\s*$', transformed)
    assert re.search(r'(?mi)^\s*brclr\s+MSNS,personality,check3\b', transformed)
    assert re.search(r'(?mi)^\s*check3:\s*;?\s*', transformed)
    return transformed


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python tools/apply_ms15_fuel_only.py /path/to/patched/029y4a/src/msns-extra.asm')
    path = Path(sys.argv[1])
    raw = path.read_bytes()
    original = raw.decode('latin-1')  # reversible for original 8-bit assembler bytes
    changed = transform(original)
    assert changed != original
    path.write_bytes(changed.encode('latin-1'))
    print('PASS: source-only fuel-only runtime isolation applied (not assembled or flashed)')


if __name__ == '__main__':
    main()
