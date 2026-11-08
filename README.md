# MegaSquirt MS1.5

Modernizing an existing **MegaSquirt MS1** to run a **GM 4.3L V6 with throttle-body injection (TBI)**, focusing on better idle control, useful wideband O₂ feedback, and a better tuning experience.

**Status:** Requirements recorded and **initial MS1/Extra 029y4a source audit completed** using the owner's uploaded firmware ZIP. Board-specific I/O, stepper-driver feasibility, processor headroom, and installed ECU firmware remain **unverified**. No project firmware has been written, compiled, flashed, or released.

## Confirmed project requirements

These items come directly from the project owner's discussion on November 8, 2026:

- **Engine/application:** GM 4.3L TBI.
- **Controller:** Reuse the existing MegaSquirt MS1 if technically feasible.
- **Fueling:** Control the engine's TBI injection.
- **Ignition:** The MS1 **will not control spark** on this engine. Do not reserve ignition outputs without a reason.
- **Idle air:** Add active IAC control. The earlier MS1 installation was run without an IAC.
- **IAC architecture preference:** Keep the idle-control intelligence in the MS1 firmware; use an **external motor driver**, not a second ECU, if feasible.
- **Oxygen sensor:** Add wideband O₂-based AFR control.
- **Cooling fan:** **Exactly one fan-control output is needed.**
- **Resistors:** The owner already has resistors. Their intended application and values have **not yet been confirmed**.
- **Tuning:** Improve the available tuning and diagnostics compared with the old MS1 experience.

## Intended features (design goals, not implemented features)

1. Closed-loop idle-speed control using a stepper IAC and suitable external driver.
2. Tunable startup, warm-up, idle-target, dashpot and idle-recovery behavior.
3. Wideband-calibrated AFR readings and AFR-target-based closed-loop fuel correction.
4. Usable fuel/AFR tables, diagnostics and datalogging; reuse existing tuning protocols/tools where practical.
5. Preserve one cooling-fan control output and the injection functions.
6. Retain reliable fuel-control timing as the highest priority.

**Source-audit update (2026-11-08):** MS1/Extra 029y4a **already implements** fan control with separate on/off coolant thresholds, two 8×8 AFR-target tables with EGO fuel correction, and PWM closed-loop idle targeting with warm-up, dashpot and recovery. The missing major feature is **stepper-actuator output/control**, not the entirety of idle or AFR logic. These findings apply to the uploaded historical firmware, **not yet to the unknown firmware installed in the physical ECU**. Real-time timing, flash/RAM, and board I/O feasibility remain unverified.

## Architecture preference

```text
 GM engine sensors ───────> MegaSquirt MS1 ──────> TBI injector outputs
        │                        │
        └─ RPM/TPS/CLT/etc.      ├───────────────> One cooling-fan output
                                 └─ IAC command ─> External stepper driver ─> IAC

 Wideband O₂ sensor ─> Wideband controller ─> Calibrated analog signal ─> MS1

 Ignition timing: managed outside the MS1 in this application.
```

The diagram is **conceptual**. Output assignments, driver interface, and signal availability are not yet validated.

## Project documents

- [Requirements and design decisions](docs/PROJECT-SPEC.md)
- [Research status and verification needs](docs/RESEARCH-NOTES.md)
- [Verified MS1/Extra 029y4a source audit with line references](docs/SOURCE-AUDIT-029Y4A.md)
- [Stepper IAC timing and memory feasibility plan](docs/STEPPER-FEASIBILITY-PLAN.md)
- [Scope warning for uploaded MS3/V3.0 hardware manual](docs/HARDWARE-MANUAL-SCOPE.md)
- [Open questions / investigation checklist](docs/OPEN-QUESTIONS.md)

## Engineering ground rules

- **Do not guess hardware revisions, connector pins, spare I/O, firmware variants, or electrical limits.** Verify them from the physical board, schematics, and source.
- **Do not confuse past installations with this engine.** Earlier MegaSquirt/Magnum/EDIS history does not establish the wiring of the GM 4.3 TBI project.
- **No build, installer, firmware release, or flash without explicit authorization.** Discussing or approving a design does not authorize a build.
- Bench-test injection, idle actuator, error handling and reset behavior before any on-engine use.
- Keep project facts, proposed designs, and unverified assumptions distinguishable in the repository.

*Initial planning notes: November 8, 2026.*
