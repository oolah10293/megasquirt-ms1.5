# Project specification and decisions

**Status:** Working requirements. This document is not a validated circuit design or implemented feature list.

## 1. Confirmed requirements (from the owner)

| Area | Requirement | Status |
| --- | --- | --- |
| Platform | Reuse old MegaSquirt MS1 | Confirmed intent; board revision unknown |
| Engine | GM 4.3L V6 with TBI | Confirmed |
| Ignition | MS1 does not control spark | Confirmed |
| Injection | MS1 to control TBI fueling | Confirmed goal |
| Idle | Add active IAC; closed-loop control desired | Confirmed goal |
| IAC implementation | Prefer an external **driver**, not a standalone intelligent controller | Confirmed preference |
| Wideband | Add wideband O₂ and useful AFR closed-loop fuel correction | Confirmed goal |
| Tuning | Improve tuning capability / experience | Confirmed goal |
| Fans | One cooling-fan output only | Confirmed |
| Resistors | Resistors already on hand | Confirmed; type/value/purpose not verified |

## 2. Proposed design (not approved as final)

### Fuel injection

- Reuse an appropriate existing injector output path when hardware is verified.
- Determine injector type, impedance and peak/hold or limiting arrangement **before** specifying resistors or driver setup.
- Preserve deterministic injection timing and safe reset/boot behavior.

### Stepper idle air control

- **Source-confirmed:** 029y4a already contains closed-loop *PWM* target-idle/warmup/dashpot/recovery logic. Reuse/adapt it where practical; stepper actuation and position tracking still need design. See [source audit](SOURCE-AUDIT-029Y4A.md).
- Prefer a driver with a simple command interface (e.g. STEP/DIR), **if** its electrical and logical compatibility with the target IAC is confirmed.
- Candidate behaviors: startup homing/reference, coolant-based cranking/warmup positions, target-RPM feedback, dashpot on throttle closing, recovery under electrical/load changes, movement limits and fault handling.
- Do **not** assume unused spark outputs can simply be reassigned without inspecting the actual board routing and firmware.
- A second microcontroller/ECU is a fallback, **not** the preferred design.

### Wideband/AFR control

- Use a real wideband sensor **and its matching sensor controller**.
- Determine the controller's output calibration before writing an AFR-conversion table.
- **Source-confirmed:** 029y4a already has two 8x8 AFR-target tables and bounded stepwise EGO correction; retain/validate before adding or replacing logic.
- Confirm wideband controller scaling and polarity; improve sensor-valid handling, feedback response, correction bounds and diagnostics only as justified by source review.

### Auxiliary control

- Allocate exactly one fan output. **Source-confirmed:** 029y4a already supports X2/PTA5 or LED18/PTC2 fan control, subject to physical board wiring.
- Existing fan-output modification(s), if any, must be mapped before choosing IAC pins.
- Spark outputs and routines are candidates for reuse only after verification.

### Tuning and diagnostics

- Prefer compatibility with existing MegaSquirt tuning software/protocols where feasible.
- Expose important internal variables: commanded AFR, measured AFR, closed-loop correction, IAC target, actual command/step count, RPM target/error, fan state and relevant faults.
- **Source-confirmed:** 029y4a has 12x12 VE tables, two 8x8 AFR target tables, and a bundled tuning INI. Preserve compatibility where possible; do not promise larger tables, logging bandwidth, or new protocol until resource limits are audited.

## 3. Source-inspection status and remaining unknowns

- **Directly inspected on 2026-11-08:** owner-provided MS1/Extra 029y4a assembly/header/INI and an MS3/V3.0 hardware manual. See [firmware audit](SOURCE-AUDIT-029Y4A.md) and [manual scope](HARDWARE-MANUAL-SCOPE.md).
- MS3 hardware guide is not MS1-specific; don't use its MS3 CPU output map to design MS1 IAC circuits.
- Neither a firmware build nor physical I/O validation was performed.

### Explicitly unverified details

- MS1 board PCB revision and CPU/daughtercard details.
- Installed firmware and its exact source/version.
- Available pins after accounting for the owner's earlier modifications.
- TBI injector electrical requirements; resistor values and what they are for.
- Specific IAC model, coil characteristics and best driver IC.
- Wideband controller make, signal characteristics and wiring.
- Available flash, RAM, timer/interrupt budget and communication bandwidth.
- Engine ignition arrangement (only **non-control by MS1** is confirmed).
- Whether hardware or firmware alterations to the analog-input circuitry will be needed.

## 4. Decision log

| Date | Decision | Basis |
| --- | --- | --- |
| 2026-11-08 | Use name **MegaSquirt MS1.5** | Owner chose the name |
| 2026-11-08 | Target **GM 4.3L TBI** rather than the earlier Magnum application | Owner specified current target |
| 2026-11-08 | No ignition control by MS1 | Owner specified |
| 2026-11-08 | Prefer MS1 firmware + external IAC **driver** over second ECU | Owner specified |
| 2026-11-08 | One fan output | Owner specified |
| 2026-11-08 | Add wideband AFR control and improve tuning | Owner specified |
| 2026-11-08 | Research/documentation is permitted; builds require separate explicit go-ahead | Standing project instruction |
| 2026-11-08 | Inspect uploaded MS1/Extra 029y4a source and record existing idle, fan and AFR features | Verified directly from supplied firmware archive; see source audit |

## 5. Design priorities

1. Engine-control safety and deterministic fueling.
2. Reuse existing hardware and functionality where feasible.
3. Good idle response and stable, bounded AFR correction.
4. Simple external IAC electronics and clear diagnostics.
5. Minimal additional hardware and complexity.

**Important:** A design choice appearing in this document is not proof that it will fit the MS1's resources or is safe to deploy.
