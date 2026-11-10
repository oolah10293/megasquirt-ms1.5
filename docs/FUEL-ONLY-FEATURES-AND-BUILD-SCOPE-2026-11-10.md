# Full fuel-only scope and feature preservation — November 10, 2026

This checkpoint records the owner's **explicit authorization to build a bench-test firmware image**. It does **not** authorize flashing, vehicle use, a release, or deployment. The historical no-build notices in other files predate this authorization.

## Nonnegotiable features

Use **MS1/Extra 029y4a as the primary codebase**, with the already-developed MS1.5 integration changes, **not a reversion to the original Bowling & Grippo 2.986/3.000 software**. The owner has supplied original B&G 2.986 source, which is a source reference for clean fuel-only tach/injector behavior.

Preserve: dual 12x12 VE tables and their fuel calculations; wideband O2 input with AFR-target tables and EGO correction; closed-loop PWM-derived idle demand and the custom STEP/DIR IAC state machine; warm-up, afterstart, cranking and TPS/MAP acceleration enrichment; injector channel scheduling and injector PWM/current limiting; RPM capture and period averaging; serial diagnostics and datalogging; retained tune signature/page offsets; single JS2 fan with temperature hysteresis; RAM ownership/ADC smoothing correction; MCU bootloader and vectors. Do not throw away valuable fuel-only features just because they were developed before the MS1.5 project.

Remove: all spark timing/advance lookup, coil on/off and dwell scheduling, EDIS/HEI/TFI/Neon/Wheel ignition mode activation, TIM2 channel-1 spark IRQ, spark-only configuration validation and TunerStudio menus, plus shift/launch/nitrous or other racing-only features where their removal does not compromise fuel and safety functions. Preserve a conventional tach/RPM signal from the existing ignition system as input.

## Confirmed dependency requiring care

Original `msns-extra.asm` uses a 24-bit `iTimeX:iTimeH:iTimeL` timer delta, including its preceding sample for odd-fire averaging, in `CalcRPM:`. Its tach IRQ also manages `rpmch:rpmcl`, afterstart/acceleration/EGO counters, staged fueling, and the injector scheduler. An ignition-free replacement IRQ **must not simply jump to the injector scheduler while abandoning period calculation**, or RPM-dependent fueling will be wrong. The existing TIM2 channel-0 0.1-ms interrupt and main fuel-injection control paths remain essential.

The stage-one `remove_ms15_ignition_stage1.py` only deletes two sections. Further work must remove mixed spark timer and IRQ code, with branch-reference and vector audits, without moving flash calibration pages or breaking tuning. Any successful assembly is still *not* a passing Stim test.

**Status at this checkpoint:** source architecture verified; full removal and build validation still in progress. No new S19 has been declared safe to flash.
