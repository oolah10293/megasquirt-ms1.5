# MS1.5 — stepper IAC firmware and driver design

**Status 2026-11-08:** **Proposed design, not implemented.** No firmware source modifications, assembly, release, vehicle wiring or bench testing authorized/performed. **Updated after full JS0–JS11 map:** preferred IAC pins are PTA5/JS0 and PTA4/JS1; propose JS2 for fan and JS3 as spare. Derived from owner's uploaded **MS1/Extra 029y4a** source and physical MS1/V3.0 photographs.

## Current proposed output architecture (updated after complete JS-pad audit)

**User preference:** Retain **one** of the two existing 2N2222 stages for the single cooling-fan relay and **leave the other intact and unused**. Which stage becomes fan is still a reversible design choice.

**Preferred candidate assignment:** **JS0/PTA5=IAC STEP, JS1/PTA4=IAC DIR, JS2/PTA3=fan transistor, JS3/PTA2=spare transistor**. JS7/PTC3 and JS8/PTC4 are another possible STEP/DIR pair. LED17/PTC0 and LED19/PTC1 remain fallbacks. The verified pad map is [JS-PAD-MAP-MS1-V30.md](JS-PAD-MAP-MS1-V30.md), and the current working proposal is [IO-ALLOCATION-MS1-V30.md](IO-ALLOCATION-MS1-V30.md).

Why: the MS1 source `msns-extra.h:19–25` and the V3.0 schematic confirm **JS0 and JS1 are direct digital output pins**, already output-configured by `msns-extra.asm:898–900`. They do not need the unused 2N2222 stages for logic drive, although the external STEP/DIR signals still need proper buffering, protection and connector routing.

**Firmware work:** Remap existing fan routine `msns-extra.asm:4971–5009` from JS0/PTA5 or LED18/PTC2 to whichever transistor stage is selected for fan (currently proposing JS2/PTA3), and block Output 1/boost from that pin. Gate/disable legacy fan/water/nitrous/tach writes to JS0 and JS1 so **only the IAC service may toggle them**. Establish reset-safe STEP=0 and motor-driver polarity. No code has been built or flashed.

## 1. Goal and deliberate reuse

**Goal:** Have MS1 itself control the GM 4.3 TBI's four-wire IAC while an external dedicated **stepper motor driver** handles current through the two motor coils. **No second intelligent ECU**.

Preserve the proven parts of 029y4a:
- Idle target / throttle entry / RPM error / dashpot / warmup / startup: `029y4a/src/msns-extra.asm:5286-5546`.
- Existing configurable one-fan behavior: `msns-extra.asm:4971-5009`.
- Two 8×8 target-AFR lookup tables and bounded EGO correction: `msns-extra.asm:3019-3148,13466-13659`.
- Both injector channels and hardware PWM/current limitation; **fuel timing takes priority**.

Replace the existing **PWM-on-FIDLE actuator** (`msns-extra.asm:9370-9406`) with **stepper position commands**. Keep the existing idle target algorithm unless tests show it needs retuning or additional damping.

## 2. External driver candidate: DRV8825-class STEP/DIR bipolar driver

**Verified component characteristics, not a final part approval:** Texas Instruments' DRV8825 has two H-bridges, a STEP/DIR interface, 8.2–45 V VM operating supply, adjustable current regulation and a fault output; see https://www.ti.com/product/DRV8825 and https://www.ti.com/lit/ds/symlink/drv8825.pdf.

TI timing table (datasheet §7.6):
- Minimum **STEP high and low**: **1.9 µs** each.
- Minimum DIR setup and hold relative to rising STEP: **650 ns** each.
- Wake from sleep to accepted STEP: up to **1.7 ms**.

**GM valve reference (not yet confirmation of this actual valve):** The MegaSquirt stepper IAC guide describes GM four-wire steppers, sometimes up to ~320 positions, https://www.megamanual.com/ms2/IAC.htm. A GM 4.3 service reference gives 40–80 Ω between the two pairs of coil terminals, with the other pair-to-pair readings open, https://charm.thetinyserver.com/GMC%20Truck/1989/S15%2FT15%204WD%20Jimmy%20V6-262%204.3L/Repair%20and%20Diagnosis/A%20L%20L%20%20Diagnostic%20Trouble%20Codes%20%28%20DTC%20%29/Testing%20and%20Inspection/Related%20Tests%2C%20Information%20and%20Procedures/C%20Charts/Chart%20C-2%20Idle%20Air%20Control%20%28IAC%29%20System%20Check/ and https://manuals.chudov.com/TBI-Fuel-Control.pdf. **Measure/check the particular valve and harness before selecting coil current or pinout.**

### Conceptual signals (not a pin-accurate wiring diagram)

```text
MS1 PTA5 (JS0/X2) --[protected logic interface]--> STEP -------+
MS1 PTA4 (JS1/X3) --[protected logic interface]--> DIR --------+|
Optional FIDLE ----[appropriate low-side/logic circuit]--> nENBL |||
MS1 signal ground -------------------------------------------+   |||
Protected/fused automotive 12V ----------------------------+ |   |||
                                                          | |   |||
                                      [DRV8825-class full-step driver]
                                                |   |
                                             A pair B pair
                                                \___/
                                      GM two-coil stepper IAC

MS1 injector/tach/O₂/fuel pump and ONE fan output retained.
```

- Run **full-step mode initially**, not microstepping, to maintain familiar ECU-style step counts.
- Configure the driver current limit **from measured coil requirements**; don't pick a value just because the IC can deliver amperes.
- Use power/ground conditioning and automotive transient protection. Pololu explicitly warns DRV8825 carriers can experience **destructive LC spikes even at 12 V**, and recommends **at least 47 µF bulk capacitance near VMOT** as one measure: https://www.pololu.com/product/2133/. Automotive load dump/EMI needs additional design review; a printer breakout is a **bench prototype**, not automatically automotive-rated hardware.
- Ensure nSLEEP/nRESET/nENBL are at safe states before firmware begins issuing STEP pulses; do not assume a sleeping driver retains step position.
- **Existing 2N2222 stages:** Keep one for the fan-relay output and preferably leave the other as a spare. They are **not part of the current STEP/DIR logic proposal**. Verify fan relay coil current, base drive and flyback protection; separate raw JS0/JS1 logic routing still needs buffering/protection appropriate to the external driver.
- If two output pins only are available, nENBL could initially be hardware-configured (driver remains energized). A **third signal from FIDLE** would be preferable if safe coil-off control is needed. Keep this as an option until we know the valve's heat/holding needs.

## 3. Firmware ownership and source locations

- **JS0 / PTA5 / X2** proposed for STEP, **JS1 / PTA4 / X3** proposed for DIR. The `msns-extra.h` header confirms both; `msns-extra.asm:898–900` configures these as outputs.
- Legacy **fan, water injection and optional tach-output** code writes JS0; **second water/nitrous and optional tach-output** code writes JS1. Review/gate `msns-extra.asm:4971–5009,5060+,9270–9496,10979–11005,13275–13292`. These are not safe IAC outputs until code ownership is exclusive.
- The **single fan** is proposed on **JS2/PTA3** with the existing owner-built 2N2222; retarget existing fan on/off thresholds/hysteresis and cranking-off logic, and remove generic Output 1/boost writers from PTA3. Leave JS3/PTA2 with its second 2N2222 stage untouched.
- Alternate JS7/PTC3 and JS8/PTC4 are accessible digital outputs but share shift-light/optional spark and second-trigger features. Choose them only if source inspection and external routing favor them.
- Keep `idleDC` as a possible **requested position** (0…255 initially), not PWM duty; refactor startup/closed-loop/dashpot algorithms and the TunerStudio definitions as needed. Do not assume existing tunes are compatible.
- Add minimal position/step-interval/phase/reference state subject to RAM and interrupt budget validation. No implemented or tested state machine yet.

## 4. Proposed nonblocking step schedule

The source already enters **MSEC** at roughly 1 ms intervals from its TIM2 100 µs timebase: `msns-extra.asm:9601-9650`. Prefer a tiny, constant-time **IAC service at MSEC** over adding a motor timing loop to every 100 µs interrupt or busy-waiting in the main thread.

A proposed finite-state progression (illustrative behavior, not actual code):

1. **Disabled:** STEP low; don't command motion until output driver and ECU are initialized.
2. **Reference/homing:** At safe startup, drive a bounded number of steps toward the known mechanical stop as allowed by the valve's actual specifications, set reference position; never home unboundedly.
3. **Ready / wait:** If actual position equals target, do nothing. Otherwise, wait for elapsed inter-step interval, and set DIR appropriately.
4. **DIR settle:** After DIR change, allow at least one service interval before STEP rising; this far exceeds TI's **650 ns minimum**.
5. **STEP high:** Emit one rising edge and maintain high until the next 1 ms service (greatly exceeding TI's **1.9 µs minimum**); advance **commanded** position.
6. **STEP low:** Return low and wait for the next permitted step interval. Prevent another rising edge while high.
7. **Fault / stall / lost position:** Keep injector/fuel safety independent; prevent indefinite motor cycling; use bounded recovery and allow recalibration on a later appropriate startup.

**Preliminary step rate for budgeting, not a validated actuator setting:** one step every **5–10 ms** (100–200 steps/s). Roughly **200 full steps** would take **1–2 s**, excluding other reference/settling delays. The actual GM valve's reliable step rate, motion direction and stop behavior must be tested. Do not promise 200 steps/s for an unmeasured motor.

Because STEP pulse width comes from separate 1 ms ticks, no precise microsecond busy wait is needed. The scheduler must have a bounded worst-case instruction path and cannot disable interrupts for motor motion.

## 5. Idle-control tuning implications

Legacy 029y4a closed-loop idle already increases/decreases `idleDC` **one unit per control update** using an RPM deadband and proportional update interval. With `idleDC` reinterpreted as a valve position:
- Verify that moving **one full step** materially changes RPM enough and moves in the intended direction.
- Maintain cranking opening, poststart reduction, warmup-based positions, TPS-based entry, dashpot and RPM recovery.
- Add adjustable **position min/max, rehome count, step interval**, using existing calibration fields only after checking interactions; additional fields must fit flash page sizes.
- Existing PWM-frequency settings lose their prior meaning. Use a unique MS1.5 firmware/INI identity and deliberate tune migration rather than loading a historical MS1/Extra `.msq` blindly.
- Preserve bounded AFR closed-loop correction, one fan, and RPM/injection diagnostics. Sensor error and motor driver fault behaviors must be specified before any live engine test.

## 6. Not-yet-complete verification

- Current candidate IAC signals JS0/PTA5 and JS1/PTA4 are direct MCU outputs; confirm protected electrical routing to the external STEP/DIR controller. Existing JS2/PTA3 and JS3/PTA2 2N2222 stages are reserved for fan/spare, and actual fan circuit polarity/relay requirements remain unverified.
- Ensure no competing 029y4a Output 1/Output 2/boost write paths remain in the MS1.5 configuration. PTC0/PTC1 would need a separate audit only if chosen as fallbacks.
- Whether 029y4a `MSEC` execution and added service meet worst-case fuel-injection latency requirements.
- Whether adequate stack/RAM can be reclaimed without overlapping the flash calibration buffer.
- Driver enable/holding-current plan and GM valve mechanical stop/homing safety.

**Next gate:** Finish independent source call-site audit and resource allocation; **only after an explicit build authorization** can we produce/assemble test firmware and measure timings.
