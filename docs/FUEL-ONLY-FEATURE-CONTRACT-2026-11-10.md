# MS1.5 fuel-only feature preservation contract — 2026-11-10

**Decision from owner:** Build a dedicated fuel-only controller from the useful MS1/Extra 029y4a feature base, using Bowling & Grippo 2.986/3.000 fuel-only code as a **design/reference comparison**, NOT as a feature-reducing replacement. The completed, previously authorized assembly is a baseline; no new firmware assembly or verified fuel-only executable has yet been produced by this source-only checkpoint.

## Required to retain

- Both physical injector drivers, tach IRQ/RPM computation, trigger period capture, stall/pump safety, injector PWM/current limiting, alternating/staging behavior where it is needed for fueling.
- 12x12 VE tables and associated interpolated fuel calculations, speed-density/Alpha-N/load handling, cranking enrichment, after-start and warm-up enrichment, TPS/MAP acceleration and deceleration enrichment, battery-voltage injector corrections.
- Existing dual 8x8 AFR targets and 029y4a EGO/wideband closed-loop fuel correction, with the necessary calibration pages, safeguards and TunerStudio definitions.
- Existing closed-loop idle *demand logic* (including warm-up, dashpot, target RPM, settling/recovery) plus the custom STEP/DIR IAC state machine and its calibration bytes. JS0 = STEP, JS1 = DIR.
- One cooling-fan output using JS2 and hysteresis/cranking policy.
- The corrected ADC RAM ownership, including absence of the obsolete indexed ADC-history writer that formerly corrupted MS1.5 stepper state.
- Core serial protocol, tune-read/write/burn/reconnect, firmware and TunerStudio signature compatibility, all unrelated engine protection and usable diagnostics.

## Required to remove

- Ignition output pin selection and ignition-only configuration errors, including the original MSnS requirement to assign LED17 or FIDLE.
- Ignition dwell, coil drivers/output writes, ignition angle calculation, spark table lookups, ignition timer interrupt and spark scheduling that are not shared with fuel timing.
- Spark-only TunerStudio menu entry points, while initially preserving calibration-page sizes/offsets to avoid breaking old tunes.

## Distinguish carefully

Original B&G 2.986 source directly confirms *fuel-only* architecture, RPM pulse scheduling, basic O2 loop and 8x8 VE lookup. Those are useful architectural precedents, not a reason to discard 029y4a fuel/AFR features.

Do not indiscriminately remove code with words `ign`, `spark`, `trigger`, or `wheel`: some event counters and timing fields are shared with **fuel injection, staged fuel, closed-loop idle, RPM, or EGO**. Likewise preserve genuine fuel-rev-limit protections unless the owner explicitly agrees otherwise. Unused racing/boost/nitrous outputs can be removed as separate audited steps rather than destabilizing an otherwise useful fuel controller.

**Validation gates:** static symbol/port/interrupt analysis; source-level feature retention assertions; successful original-baseline and modified CASM08Z assembly; S19 checksums, vectors, protected memory, page addresses, and signature comparison; TunerStudio offline check; then separately authorized Stim/ECU flash and power-cycle/STEP-DIR/fan/fuel bench tests. Assembly alone is NOT bench or engine validation.

**Build authority:** The owner's November 10 message explicitly authorizes engineering and a new build. It does not authorize flashing the ECU or publishing a release. Keep the existing `ms15-test-build` branch and the historical `ms15-fuel-only-config` checkpoint unchanged until a controlled, verifiable workflow is prepared.
