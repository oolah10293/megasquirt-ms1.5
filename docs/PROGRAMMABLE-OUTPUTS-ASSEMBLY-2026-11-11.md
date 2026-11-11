# MS1.5 six programmable outputs — authorized assembler checkpoint (2026-11-11 UTC)

**Status: ASSEMBLED + STATIC/ARTIFACT-VERIFIED. NOT FLASHED, NOT TESTED IN TUNERSTUDIO GUI, NOT STIM OR VEHICLE VERIFIED. NO RELEASE OR INSTALLER.**

## Authorization and provenance

The owner explicitly instructed: “proceed with assembly of the updated firmware and matching INI.” This authorizes assembly and the corresponding INI generation only; no authorization to flash, deploy or release was given.

- Source branch: `ms15-ignition-removal`, finalized source commit `8e396c379b82c661879ccabf7b6f426c92694482`; [source-only CI run 42965615664](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42965615664) **success**.
- Assembler branch: `ms15-test-build`, committed build source `eef96cf943dc783a8cb32b66554d4211ca2653ae`.
- Official historical archive: 029y4a ZIP SHA-256 `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`.
- [Successful Windows CASM08Z build/verification run 42965620172](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42965620172), job `130342033267`, conclusion **success**.
- [GitHub Actions artifact](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42965620172/artifacts/13831670354) contains both matching files, assembler listing, .err, baseline and report (GitHub artifact retention currently seven days).

## Exact assembled files

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED.s19` | 35,810 | `0983b037d4e2b24e2e53e177786d7e23181b4ef0f42199c4e66e0df7b5e549a8` |
| `MS15-PROGRAMMABLE-OUTPUTS-UNVALIDATED.ini` | 167,684 | `4e7248efc02aa5143712f35c7504de4c70a5de8f667cae0570ab9e09f8696834` |

**INI/firmware serial signature:** `MS1/Extra format MS15_002 ******` (32 ASCII bytes). Old `MS15_001` INIs and firmware are **not** an interchangeable calibration ABI for the new 47-byte page-9 extension. Firmware and INI must be used as a matched pair.

## Completed checks

- Official CASM08Z V3.14 reported **“Successful assembly - No errors.”** for both original 029y4a and modified image. Five original regression tests plus ten final integrated cleanup tests passed, with both source and tuning checkers.
- The assembled original baseline is byte-identical to the shipped historical 029y4a S19.
- Independent post-run download parsed **829 S1 records**, verified all record counts/checksums with no memory overlap. The new S19 maps 12,925 bytes total, of which **8,181 occupied application code bytes**, from `0x8128` through `0xA11C`. This leaves **16,099** contiguous addresses to `0xDFFF`. Earlier final fuel-only code ended `0x9F1D`; this version is larger by 511 occupied application bytes. This is a code-size result, *not* a CPU timing or memory-stack measurement.
- 47 new page-9 calibration bytes are present in `0xE871–0xE89F`: IAC startup count/motor limits first five, followed by six 7-byte configurable-output records. Defaults: outputs 0–2 and 4–5 disabled, JS2 output 3 remains native fan controller (mode 4). Prior calibration and bootloader bytes were confirmed unchanged, except intended interrupt vector address relocations; all 18 vector JMP entries were validated in the build report.
- Independently checked the generated INI: signature matches, six programmable output `dialog` definitions and six `subMenu` entries exist; 13 default plus five right-click-only optional dashboard indicator definitions exist.
- The custom source-only output-RAM ownership and coarse branch-span checks passed. They do **not** substitute for cycle/stack measurement or bench tests.

## Assembly blockers found and fixed, source-only checkpoints retained

1. A legacy regression test still expected the `MS15_001` signature. Updated to `MS15_002`, then the regression suite passed.
2. CASM08Z reported duplicate labels in the new output evaluator due to colliding long label prefixes. Renamed the three colliding labels; later assembly passed.
3. CASM08Z rejected the `batADC` source identifier in `ms15_outputs.inc` (a TunerStudio alias rather than an assembly symbol). Corrected the firmware to use source RAM symbols `batt` and `tps`, not TunerStudio's `batADC`/`tpsADC` aliases. Subsequent complete assembly passed.

## Still unverified

- Real TunerStudio GUI behavior, loading the INI with the matched 002 image, persisted calibration edits/burn, right-click indicator choices.
- Output threshold hysteresis, AND/OR transitions, fan fail-safe, physical pin polarity and relay-driver operation, power-on defaults, retained IAC step/dir motion.
- Injector timing, interrupt jitter and stack high-water under 10Hz six-output evaluation, bench Stim and engine safety.

**No flash, deployment, release, public installer or vehicle test was performed.** `main` remains unchanged. The owner must separately authorize hardware flashing.
