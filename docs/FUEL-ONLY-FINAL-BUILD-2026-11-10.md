# Final fuel-only MS1.5 bench assembly — November 10 local / November 11 UTC, 2026

**Status: ASSEMBLED + STATIC-VERIFIED; NOT BENCH-FLASHED, NOT STIM-TESTED, NOT ENGINE-READY.** The owner explicitly authorized building on November 10, 2026. No authorization to flash, release, deploy or use on a running engine was given.

## Exact source and build provenance

- Final source checkpoint: `ms15-ignition-removal` at **`91c1defdb4b44a32663a780d5570643141eaf71f`**.
- Authorized assembly checkpoint: `ms15-test-build` at **`6c1621e76cc05d96d76ace232292875c6e54abbb`**. A single atomic Git tree/commit/ref update copied all 15 reviewed source, test, patch and include files, plus the modified `tools/windows-test-build.ps1` from a known previous build branch state. This one update triggered the Windows assembler workflow.
- Exact successful GitHub Actions [run 42946540078](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42946540078), job `130280604726`, conclusion **success**.
- Upstream verified 029y4a source ZIP SHA-256: `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`. Original CASM08Z-assembled baseline is byte-identical to shipped source archive S19.
- Windows build applied all three integration/tuning patches, both physical source-cleanup stages (`remove_ms15_ignition_full.py`, `finalize_ms15_fuel_only.py`), and both TunerStudio INI cleanups (`simplify_ms15_fuel_only_ini.py`, `finalize_ms15_fuel_only_ini.py`). It ran five earlier fuel-only regression tests **and nine actual integrated cleanup tests**, followed by the source checker and the tuning checker, all PASS **before assembling** the final image. Both original and modified CASM08Z executions reported `Successful assembly - No errors.`

## Files from THIS completed run

- `MS15-FUEL-ONLY-BENCH-UNVALIDATED.s19` — SHA-256 **`ac1fab5fb792a166e8972e4f8a61c06d50a065b4fb5d8b3ba6076018967fe7bb`**; 34,296 bytes.
- `MS15-FUEL-ONLY-BENCH-UNVALIDATED.ini` — SHA-256 **`65640321bb090e19f2d4a583de94525d66fe1a4160d4d905b271932c6481bf84`**; 156,717 bytes.
- Complete CI test-only artifact `MS15-FUEL-ONLY-UNVALIDATED-DO-NOT-FLASH`, artifact ID `13822617741`, additionally contains the assembled listing, original build, error logs and REPORT. These hashes distinguish the final cleanup from the obsolete prior successful bench build.

## Independent binary audit on downloaded artifact

- Independently parsed **all 795 S1 records**, verifying count/checksum and that no mapped address overlaps. New S19 maps 12,372 bytes overall, including preserved high-memory areas.
- Application program address range `0x8128..0x9F1D`, **7,670 occupied code bytes** (original unmodified 029y4a: 23,135 code bytes; 15,465 fewer than original). The contiguous free addresses after code to `0xDFFF` number **16,610**. Do not interpret this as measured CPU/RAM/timing savings.
- All **18 JMP-vector stubs at `0xFACA..0xFAFF`** contain JMP opcodes with target addresses mapped inside the application. The **TIM2 channel 1 ignition vector `0xFAE5`** points to `0x9A31`, which begins with `0x80` (RTI; Dummy). The vital **TIM2 channel 0** vector `0xFAE8` points to application `0x932B` (TIMERROLL); main IRQ vector `0xFAF7` points to `0x9590` (DOSQUIRT). Reset vector `0xFAFD` points to `0x8128`.
- Compared baseline vs. new S19 at **every address `>=0xE000`**; every difference is within the legitimate vector target addresses or the **five new page-9 stepper bytes at `0xE871..0xE875`**. These bytes are `04 01 68 01 40` (4ms low, 360 homing, 320 maximum: test presets, not mechanically validated). Bootloader and old calibration unchanged.
- The unique firmware 32-byte `MS1/Extra format MS15_001 ******` signature also appears in the corresponding INI. INI has active VE1/VE2, AFR1/AFR2, idle, fan and fuel-rev-limit menus; removed ignition/racing dialog/help entries are not presented.
- Current image contains verified code assembly paths for fuel tables, closed-loop EGO, stepper IAC, fan and RPM/injector timing by source/CI checks. This is **not** simulation/bench verification of their runtime behavior.

## Authorization and next gates

**No release was published, and no ECU was flashed or deployed.** The historical previous fuel-only S19 at `3e8e80e2` is obsolete. This new `6c1621e7` image is a build/test artifact only.

Still untested on real ECU/Stim: true RPM sampling across frequencies, injector pulse width/current limiting, periodic scheduling jitter, configuration burn followed by power-cycle/TunerStudio reconnect (including elimination of former MSnS spark-output error), physical JS0 STEP/JS1 DIR homing limits, JS2 fan hysteresis and fail-safe, electrical absence of ignition output activity, actual wideband/AFR behavior and vehicle operation.

**The owner must authorize flashing separately**, with hardware safeguards and fuel-pump/injector actuator isolation during initial bench checks.
