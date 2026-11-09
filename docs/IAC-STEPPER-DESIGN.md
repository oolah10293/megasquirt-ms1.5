# MS1.5 — stepper IAC firmware and driver design

**Status 2026-11-08:** **Proposed design, not implemented.** No firmware source modifications, assembly, release, vehicle wiring or bench testing authorized/performed. Derived from owner's uploaded **MS1/Extra 029y4a** source and physical MS1/V3.0 photographs.

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
MS1 PTC0 (LED17) --[protected/conditioned output]--> STEP -------+
MS1 PTC1 (LED19) --[protected/conditioned output]--> DIR --------+|
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
- If two output pins only are available, nENBL could initially be hardware-configured (driver remains energized). A **third signal from FIDLE** would be preferable if safe coil-off control is needed. Keep this as an option until we know the valve's heat/holding needs.

## 3. Firmware ownership and source locations

- **PTC0** (candidate STEP) and **PTC1** (candidate DIR) need exclusive ownership in MS1.5. The original code still toggles them for **squirt/acceleration LEDs** and optional spark even with spark output disabled. Review all writes to `sled/aled/coila/coilb` in `portc`, notably `2616-2619, 2865-2928, 6915-6955, 9232-9252, 9457`, and the startup `sta portc` at `~902`.
- **Do not use the original turn-all-spark-off macro unchanged**: `TurnAllSpkOff` toggles PTC0/PTC1 during stall/reset. It must hand pins to the new IAC service or force a deliberately safe, known STEP=0/DIR default only once.
- **Idle algorithm**: keep `idleDC` as **requested position** (0…255 units initially) rather than PWM duty. Map existing `idlecrankdc_f`, `idleclosedc_f`, `idle_dc_lo/hi`, `idlemindc_f`, `idledashdc_f` to new position semantics with updated TunerStudio definitions.
- Reinterpret the existing `idlefreq_f` PWM-period/upper-duty setting as a **position maximum** only if all source uses are audited and the matching tuning INI is updated. No automatic compatibility with existing tunes.
- Add `iacActualPosition`, `iacStepInterval`/divider, `iacPhase` flags, and bounded homing/reference count. A one-byte target may handle a practical operating region but may **not cover the whole documented GM mechanical travel**. The exact count widths and calibration range are still design choices.

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

- Which pin/outgoing conductor drives each of the owner's **unused** JS2/JS3 custom output circuits, and whether their transistors should be **bypassed/reworked** to carry valid STEP/DIR logic rather than preserving unused auxiliary outputs.
- Whether PTC0/PTC1 are free of other *active* non-spark modes on this board.
- Whether 029y4a `MSEC` execution and added service meet worst-case fuel-injection latency requirements.
- Whether adequate stack/RAM can be reclaimed without overlapping the flash calibration buffer.
- Driver enable/holding-current plan and GM valve mechanical stop/homing safety.

**Next gate:** Finish independent source call-site audit and resource allocation; **only after an explicit build authorization** can we produce/assemble test firmware and measure timings.
