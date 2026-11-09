# Project specification and decisions

**Status:** Working requirements. This document is not a validated circuit design or implemented feature list.

## 1. Confirmed requirements (from the owner)

| Area | Requirement | Status |
| --- | --- | --- |
| Platform | Reuse existing MegaSquirt MS1 processor on **physically verified V3.0 mainboard** | Confirmed from owner's PCB photo and source/board schematic |
| Engine | GM 4.3L V6 with TBI | Confirmed |
| Ignition | MS1 does not control spark | Confirmed |
| Injection | MS1 to control TBI fueling | Confirmed goal |
| Idle | Add active IAC; closed-loop control desired | Confirmed goal |
| IAC implementation | Prefer an external **driver**, not a standalone intelligent controller | Confirmed preference |
| Wideband | Add wideband O₂ and useful AFR closed-loop fuel correction | Confirmed goal |
| Tuning | Improve tuning capability / experience | Confirmed goal |
| Fans | One cooling-fan output only | Confirmed |
| Resistors | Resistors already on hand | Confirmed; type/value/purpose not verified |

## Current firmware status — WIP source only

First unassembled MS1.5 source draft, 029y4a integration diff and repeatable static checks are now in GitHub. See [source implementation log](FIRMWARE-WIP-2026-11-08.md). No build, flash, or release performed. Previous alternate allocations below are historical.

## 2. Proposed design (not approved as final)

### Fuel injection

- Reuse an appropriate existing injector output path when hardware is verified.
- Determine injector type, impedance and peak/hold or limiting arrangement **before** specifying resistors or driver setup.
- Preserve deterministic injection timing and safe reset/boot behavior.

### Latest provisional allocation after checking all V3.0 JS pads — 2026-11-08

**Schematic/source verified:** JS0=PTA5/X2, JS1=PTA4/X3, JS2=PTA3/X4, JS3=PTA2/X5; JS7/PTC3 and JS8/PTC4 are additional possible digital outputs. See [complete pad map](JS-PAD-MAP-MS1-V30.md).

**Current design preference (not yet built or final):** **JS0/PTA5=IAC STEP, JS1/PTA4=IAC DIR; JS2/PTA3=one existing 2N2222 fan-relay output; JS3/PTA2=unused spare 2N2222**. The owner wants one transistor stage for the fan and the other intact; JS2 versus JS3 for the fan remains a proposed choice. Repurpose the source's native fan routine (normally X2/PTA5 or LED18) to the selected transistor output, and remove competing code writes on the IAC pins. JS7/JS8 are a fallback pair. **JS6 is reset; never connect JS9 to 12 V with an MS1.**

### Prior output decision — now superseded

**Owner preference:** Use **one existing JS2/JS3 2N2222 + nominal 1 kΩ transistor circuit for the single fan relay**, and **leave the other circuit alone** if the MS1 has separate outputs for IAC. **Current provisional design:** JS2/PTA3 as fan, JS3/PTA2 untouched, **PTC0/LED17 as STEP, PTC1/LED19 as DIR**. Owner did not specify whether JS2 or JS3 should be fan; switch them if physical routing favors it.

The native 029y4a fan code (`msns-extra.asm:4971-5009`) operates X2/PTA5 and/or LED18/PTC2, **not JS2/PTA3**. Redirect the existing fan logic to the chosen custom output in a future authorized firmware revision. Verify fan relay coil current, base drive and flyback protection, plus IAC logic-signal routing. This **supersedes the historical JS2=STEP/JS3=DIR suggestion below**, not the existing closed-loop idle design.

### Stepper idle air control

**2026-11-08 revised design after verifying the real PCB schematic and uploaded 029y4a source/INI:** **JS2 is directly connected to original MS1 PTA3 (X4/Output 1); JS3 is directly connected to PTA2 (X5/Output 2)**, confirmed explicitly by `msns-extra.ini:1383,1389`. Both added output circuits are unused. **Preferred STEP=JS2/PTA3; DIR=JS3/PTA2**; PTC0/PTC1 LEDs are fallback only. Exclude original Output 1/Output 2/boost firmware writes from these pins. The transistors' electrical behavior and external routing still need verification; an optional FIDLE driver enable remains a design choice. Preserve one fan output. Reuse the 029y4a idle target code and schedule motor pulses via a nonblocking state machine in the 1 ms service. See [I/O allocation](IO-ALLOCATION-MS1-V30.md), [design](IAC-STEPPER-DESIGN.md) and [budget](MS1-RESOURCE-BUDGET.md).


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
