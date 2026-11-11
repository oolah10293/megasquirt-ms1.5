# Completed fuel-only source cleanup — November 10, 2026

**CURRENT STATUS: SOURCE-EDITED AND SOURCE-CHECKED, NOT ASSEMBLED.** No new firmware S19/INI release or installer exists for this checkpoint. The last successful assembled bench image in `ms15-test-build` predates this cleanup and must **not** be represented as this revision. No flash/deployment authorization exists. The request for this checkpoint expressly prohibits any build.

**Development branch:** `ms15-ignition-removal`.
**Last source test commit:** `d649aa297bd6c419ec5aa994a361b3bce25e9b82`.
**Verified GitHub Actions source-only run:** [42932812680](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42932812680), **PASS**, all 6 final-cleanup tests + 2 existing MS1.5 checker scripts. This CI workflow runs exclusively on the development branch, invokes **no assembler**, and does not push to the separate `ms15-test-build` branch with its automatic build workflow.

## Implementation (physical source transformations; not a runtime personality workaround)

The ordered non-building source pipeline is:

1. Independently SHA-pin original MS1/Extra `029y4a` source, verify its original ASM/S19 hashes; extract to disposable tree.
2. Apply the three existing MS1.5 integration/tuning source patches and copy the existing STEP/DIR include files.
3. Apply `tools/remove_ms15_ignition_full.py` (already removed coil/dwell/spark lookups and scheduling, spark ISR, MSnS output selection/validation, and substituted fuel-only tach IRQ).
4. Apply **`tools/finalize_ms15_fuel_only.py`** (new cleanup and explicit fuel-only limiting / output audit).
5. Apply `tools/simplify_ms15_fuel_only_ini.py` and **`tools/finalize_ms15_fuel_only_ini.py`**. These remove obsolete menus and user dialogs **without changing the existing [Constants] section**, page sizes, old flash offsets or signature.
6. Run `tools/check_ms15_source.py`, `tools/check_ms15_tuning.py`, and `tests/test_ms15_source_final_cleanup.py` **against the actual integrated source**, not only raw upstream source. `tools/verify_integrated_source_only.py` reproduces this on Linux without invoking CASM08Z.

## Removed / neutralized

- Ignition output configuration requirements (including the error demanding LED17 or FIDLE), spark advance, rotary/EDIS/TFI/Neon output handling, spark dwell and spark compare ISR.
- The remaining launch/flat-shift/traction/knock adjustment, generic output and shift-light writers, boost-actuator controller, water injection, nitrous/anti-lag operation and countdowns.
- Three leftover `add NosPW` additions to **real staged injector pulse-width arithmetic**, and obsolete nitrous output control / pump inhibition.
- Last startup spark-output3 port writer; spark-table-2 delay clock and obsolete generic output clock. All direct spark-output pin ownership of STEP/DIR/fan is eliminated.
- The old fatal, serial-blocking `config_error1` loop, spark/water/nitrous error-string table, and stale flash-mode lockouts.
- Obsolete spark/knock/nitrous/launch/traction/boost/rotary user tuning dialogs and menu entry points.

### Legitimate non-ignition validation restored WITHOUT a lockout

The original two nonignition error cases were **water-injection vs. X2 fan** and **nitrous vs. water-injection**. Those functions, and all their output writers, have now been physically removed. Reintroducing their error codes would lock out valid fuel-only setups with historical tune bits, so their old faults remain removed.

Instead, the active `DO_FAN_Check` verifies **fan-on temperature greater than fan-off temperature**. Invalid/equal/reversed thresholds set the existing `config_error` *diagnostic status bit* (visible to the old serial status packet) and force fan on, while leaving **serial and injection fully enabled**. Correct thresholds clear the bit; no historical configuration setting can reenter the fatal loop. IAC travel/homing clamping and other existing fuel-related protections remain.

## Fuel and tune capability retained

- Dual 12×12 VE maps and alternate 12×12 VE3 table selection.
- Both 8×8 AFR target maps, closed-loop wideband/EGO correction and overrun/accel/decel safety exclusions.
- Cranking, afterstart/warmup, TPS/MAP enrichment, priming, staged injector pulse-width calculations, injector PWM/current limiting, tach IRQ/RPM timing, engine stall/pump handling.
- The RPM-based hard **fuel** cut and configurable delayed soft **fuel** cut. No spark/launch cut modes.
- The existing closed-loop idle-demand logic and independent MS1.5 STEP/DIR IAC state machine, one JS2 cooling-fan output with hysteresis, serial tuning and datalogging.
- Existing VE3 delayed switch: `VE3Timer` is genuinely used by the fuel-table lookup and was deliberately **not** removed alongside the dead spark-table delay.
- A few historically named ABI-only RAM/flash fields remain for old tune/serial offset compatibility. The previously spark-named `TCSparkCut` live prime counter is now aliased as `MS15_PrimeCount`, using exactly the same RAM byte. The old `NosDcOk` flag still drives *extra-cranking-fuel logic*, and the legacy `NosIn` signal is now used **only as a VE3 fuel-table selector**; neither is nitrous operation. Legacy spark/knock/CLT-angle serial data bytes are initialized to zero to avoid false readings.

## Verification evidence / explicit limits

**Verified from GitHub source-only CI:** hash-pinned upstream source, successful application of all three patches, successful ordered transformations, strict preservation of TunerStudio `[Constants]` ABI, existing RAM-alias and ADC-overwrite guards, required output-writer audit, six source-only regression tests on the actual integrated assembly/INI. No dangling symbol references were detected by the regression scan for labels deleted by the cleanup, and tests reject replaying the transform.

**NOT VERIFIED in this authorized source-only task:** machine-code assembly, assembled branch displacement/flash footprint, interrupt and pulse jitter, real tach frequencies, injector duty/staging behavior, serial burn/power-cycle reconnect, IAC homing/direction travel, physical fan and ignition pin behavior, real TunerStudio GUI, and vehicle operation. The source-only branch has **no validated flashable artifact**. Hardware and build testing require separate explicit authorization.

**Do not use the earlier assembled bench image as a result of this newer cleanup.** No build, release, packaging, flashing or deployment was performed for the above source changes.
