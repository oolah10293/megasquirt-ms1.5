# MS1.5 tuning-integrated test assembly — 2026-11-09

**Status: PASS for source application, CASM08Z assembly and static flash-layout/signature checks only. NOT bench-tested, NOT a firmware release, and NOT approved for flashing.**

## Test provenance and artifact

- **Passing run:** [GitHub Actions run 42666625242](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42666625242) on separate `ms15-test-build` branch (commit `b40a66e2b0c5cecdf7a38c2ebcd1cfb52d1fcbd0`).
- **Source archive:** 029y4a ZIP SHA-256 `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`, identical to owner's uploaded ZIP. Assembler was original **CASM08Z version 3.14** from that archive.
- **Inputs:** [original MS1.5 firmware integration patch](../patches/ms15-on-029y4a-wip.patch), [new tuning firmware addendum](../patches/ms15-tuning-firmware-addendum.patch), [new INI patch](../patches/ms15-tuning-ini.patch), and [updated STEP/DIR source](../firmware/ms15_iac.inc), [definitions](../firmware/ms15_defs.inc).
- **Test-only artifact:** `MS15-UNVALIDATED-DO-NOT-FLASH` in passing GitHub Actions run. It contains the S19, matched test INI, baseline and test listings/error diagnostics, and verification report; retained by workflow for 7 days. This is **not a GitHub release**.
- **MS1.5 S19 SHA-256:** `97bb79390aad12bf60c69f2a9267b2d48983850207053d4b6daed3c85820f8d5`.
- **TunerStudio source-draft INI SHA-256:** `9c782c48d012838f24481ae4d809bdb877f87f76417c6c035cf327049e7f4730`.

## Verified test results

| Check | Outcome |
| --- | --- |
| Original 029y4a assembly | **PASS**, CASM08Z no errors, matches shipped S19 byte-for-byte |
| Tuned MS1.5 assembly | **PASS**, CASM08Z no errors |
| 029y4a firmware patch | Applied |
| New tuning flash patch and TunerStudio INI patch | Applied |
| Source-only port write/RAM/branch checks | **PASS** |
| Tuning signature and source/INI address alignment checks | **PASS** |
| New 32-byte signature | **Present once** in compiled image: `MS1.5 format 001 ***************` |
| New 32-byte text version | **Present once**: `MS1.5 TEST rev 0.1 *************` |
| New page-9 calibration addresses | **E871–E875**, defaults `[4, 1, 104, 1, 64]` = 4 ms low, 360-step startup homing, 320-step max |
| Other original calibration and bootloader bytes | **Unchanged**, except normal interrupt-vector target relocation |
| Relocated interrupt jump vectors | **17 of 18** changed targets, valid and pointing into application |
| Original main-program high address | `0xDB86` |
| New main-program high address | **`0xDBEF`** |
| Added occupied program bytes | **105 bytes total**, including changed signature and five new table bytes; +58 relative to prior unconfigured 47-byte draft |
| Main-program addresses remaining through `0xDFFF` | **1,040** |

The *first attempted run* of the tuning build stopped at the source-only checker because the new IAC routine contained `ORA` and `BHS` instructions that the checker did not recognize. That checker was updated (also mirrored to `main`). The **next run passed** all checks and produced the assembled S19.

## Important restrictions and unresolved checks

1. **Do not flash or use on an engine.** The assembly and layout checks do not prove safe real-time operation, injector timing, interrupt latency, or stack high-water.
2. **IAC travel values are placeholders**, not validated GM 4.3 valve limits. Startup homing and motor current need electrical/mechanical bench tests with the actual IAC and driver.
3. **Fan electrical circuit is unverified.** Check 2N2222 relay-coil current, base drive, output polarity, flyback diode and harness route.
4. **Partial offline TunerStudio GUI rendering has now been verified** by owner screenshots (project, IAC dialog and fan dialog), but **calibration values were implausibly large**. The owner recalled a warning about no tune loaded; its role is unproven. INI value decoding, actual ECU serial tuning, full dialog coverage, saved-tune migration and forbidden legacy feature bits still require validation. See [UI observations](TUNERSTUDIO-OFFLINE-UI-2026-11-09.md).
5. No firmware has been flashed, released, distributed as an installer or packaged as a production artifact.

**Next minimum-effort check:** resolve offline TunerStudio calibration-value displays with a known-compatible tune (if available) and verify settings round-trip; after that, plan safe Stim-based bench checks for STEP/DIR/injector timing.
