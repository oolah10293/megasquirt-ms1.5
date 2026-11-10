# Dedicated fuel-only ignition removal — source audit (2026-11-10)

**Scope:** physically remove ignition-only code, not merely force a runtime setting.
**Development branch:** `ms15-ignition-removal`, based on `main` SHA `067987733b96a52ba918f285a7bb0a9904acc9b8`. The previous `ms15-fuel-only-config` branch (`703c8090f926f0836fd1f48873daa5b7f0007a01`) is preserved but is **not** a basis for this work.

## Recovered source and artifact provenance

The newly uploaded `029y4a(1).zip` is a repacked archive (outer SHA-256 `f658a885c9d80b0f1f46f02b8d5850df3454e71fb15dac5ec95e211d9bac09b8`; NOT the prior archive SHA). Its original internal files exactly match the independently recorded hashes:
- `src/msns-extra.asm`: `a80d055ebed3349c7bc3541a7d1c63c824bed85d290c41638cd659f63aa9e928`
- `src/msns-extra.h`: `38fe8d9cca8709841147be05925cba60369653952d5606f9e5b6540933ebe37a`
- `msns-extra.ini`: `6e4725fa99d20115dff19acf2adc2f0d9dc8013a86bf5d269e9ed4e51ce7a6aa`
- `msns-extra.s19`: `06bbdf436f4be7803c749d9d1d1a6344d8b66e20fb1135d9691bfb499b2486d1`

Uploaded `MS15_2026-11-10.s19` and `.ini` match the GitHub-documented successful RAM-correction build hashes `471231adeee8e109adc9496c8925c00e5cbdfd96005cb19f198ba07baaa8bd68` and `fea3b5d8f114658cff589652a80f826bb1ab4d2521f26120c0afab3cb2c59e44`, respectively. These are **existing artifacts**, not a new build or an engine-ready result.

## First removal boundary — verified in original source

- `src/msns-extra.asm:3999,4037,4094` enter `spark_lookup:` after fuel pulse widths have been assigned. This means the ignition-only calculation from `spark_lookup:` to immediately before `CheckSoftLimit:` can be eliminated while redirecting all three branches to the existing downstream limit/output path.
- `spark_lookup:` at original line 4101 through original line 4550 contains spark table selection/interpolation, angle corrections, EDIS SAW and spark delay calculations. A static outside-reference scan found no labels inside this range referenced outside it except the three `spark_lookup` entries.
- `chk_out:` through the instruction before `start_adc:` (original lines 1245–1443) handles ignition mode/output validation plus the separate water/fan and nitrous/water checks. A rewrite can physically remove ignition-mode errors while retaining both nonignition conflicts as errors 5 and 6.
- **Preserve** `CheckSoftLimit:` (line 4551) for now: its RPM/launch limiter state participates in fuel cutoff. Preserve `DOSQUIRT:` IRQ (line 10133), `TIMERROLL:` timer (line 8811), RPM calculations, fuel injectors, stepper, ADC, fan, and serial/burn paths.
- **Do not yet delete** `SPARKTIME:` (TIM2 Ch1 at original vector line 13787), `turnallsparkoff:`, `misc_spark:`, shared dwell/timing helpers, or spark-related RAM until their callers and actual output paths have been traced. Some share control flow and interrupt resources with fuel calculations.

## Validation and limits

Direct local inspection used the uploaded original source, not a reconstructed listing. A preliminary nonbuilding transformation of these two bounded regions against the exact original source removed 628 source lines (19,529 text characters), retained the main fuel and interrupt labels, and redirected three fuel-flow branches. **These are source-text counts, NOT assembled ROM/RAM savings.** No full MS1.5 integration, compilation, assembly, firmware generation, flash or new hardware tests have been performed for this removal.

The original code also has spark paths outside the first removal boundary, including startup output configuration, `misc_spark`, `SPARKTIME`, and ignition work mixed into `DOSQUIRT`. The present removal stage is therefore **partial and not safe to flash**. Future work must fully remove output scheduling and audit ISR/processor vectors, while retaining RPM/engine-phase functions needed for fuel.

TunerStudio spark dialogs, flash-calibration-page layout and obsolete error-string pointer tables require a separate compatibility-aware pass; do not compress or move existing page offsets casually. Existing stepper code, fan control, signature and ADC-history RAM correction must remain intact. The stored flash `personality_f` value is not the chosen mechanism for disabling ignition.

**Absolutely no new build, package, release, or flash has been authorized.** The `ms15-test-build` branch's auto-build workflow must not be triggered.

## Source-only Stage 1 checkpoint

- `24f24bd14c95699ed305a9d1693d07f9cd689aa6`: commit the fail-closed `tools/remove_ms15_ignition_stage1.py` transformation (unbuilt).
- `fd562742330f59a9a42d5a15ab11f44cfa17f435`: add exact-upstream-source regression tests.
- `1d2feea520ed04551b5d194a444f6442de5a8437`: make the deleted-character-count check independent of comment spelling.
- Five local `unittest` checks on the verified original assembly passed: physical removal, preservation of key fuel/RPM labels, refusal of new external consumers, refusal of a changed fuel handoff, and refusal of double application. The local preliminary transformer and committed script have the same removal boundaries and call redirection; their comment text is not byte-identical. **The committed script has not yet been rerun on the fully integrated MS1.5 source tree.**

Command for future source-only regression against the original ZIP:

```sh
MS15_ORIGINAL_ZIP=/path/to/029y4a.zip python -m unittest discover -s tests -p 'test_ms15_ignition_stage1.py'
```

Apply the existing MS1.5 integration and tuning patches first to an **extracted working copy** (do not modify the supplied archive or old S19), then run:

```sh
python tools/remove_ms15_ignition_stage1.py /path/to/029y4a/src/msns-extra.asm
```

The script **does not** assemble or install anything; it edits one working source file only. It is intentionally not inserted into the `ms15-test-build` build workflow without separate authorization. No new generated S19 or changed INI exists.

### Critical later-stage dependencies discovered

- TIM2 channel 1 is the spark interrupt: `SPARKTIME` at original line 9863 and its vector at 13787. It is initialized disabled at 930–939, but re-enabled for EDIS2 SAW at 8799–8800 and ignition delay at 11822–11823. **Do not redirect its vector until both producers and all other interrupt dependencies are removed.**
- The IRQ handler `DOSQUIRT` begins at original line 10133. Its `CYCLE_CALC` branch (11163–11880) contains extensive spark scheduling, **but the handler also supplies fuel injection and RPM/trigger timing**. The injection continuation begins at `SKIP_CYCLE_CALC` (11881), followed by `squirtCheck1` (11956); this shared path must survive.
- `SKIP_CYCLE_CALC` also contains trigger logging and prior-period state used by fuel/RPM logic. A source-only string deletion alone is insufficient proof of correct fuel behavior.
- `turnallsparkoff` and `misc_spark` still run, and the original spark output and dwell macros still exist. Stage 1 **does not** prevent these residual ignition activities and is **NOT a deployable fuel-only firmware**.
- The uploaded current INI still exposes Spark Settings, advance tables, dwell and rotary options and contains the original calibration offsets. Remove those UI features separately without arbitrarily shifting flash addresses, menus needed for fuel or tuning signatures.

No actual ROM/RAM savings can be claimed until a separately authorized assembly/map check. The only verified stage-1 size numbers are source-text deletions, **not machine code reduction**.
