# Research status and evidence log

This file distinguishes **what we know from the owner**, **what earlier discussion suggested**, and **what still needs independent source/hardware verification**.

## Hardware/project facts supplied by owner

- An old MegaSquirt MS1 is available for this project.
- Intended engine is a GM 4.3L TBI.
- Spark is controlled elsewhere; MS1 ignition control is not needed.
- One fan-control output is required.
- Resistors are already owned; do not assume their resistance, wattage or function.
- Earlier engine setup used no active IAC.
- Preferred new IAC solution is to have MS1 command an external motor **driver**, not to add a separate ECU.

## Firmware/source leads — not yet a verified audit

Earlier investigation in conversation identified these topics:

- Original MegaSquirt-I firmware and MS1/Extra firmware are leads for open/source-available implementation.
- **MS1/Extra 029y4a** was mentioned as a candidate historical firmware reference, **not** verified as the firmware currently installed on this ECU.
- An original MS1 processor type and small RAM/flash budget were discussed, but exact hardware and usable headroom still need re-verification from the board and source.
- MS1/Extra was said to have programmable output/fan controls and wideband-related capabilities, but the exact pin/feature map must be checked against the specific firmware build and board modifications.

These are **leads, not completed findings**. Do not claim that source code has been fully inspected, or that IAC support fits, until the relevant code is actually fetched and analyzed.

## Source audit to perform

1. Obtain the exact installed firmware/version, or establish a replacement source baseline explicitly.
2. Locate the original source, assembler/build instructions, processor datasheet and board schematics.
3. Inventory each existing injector, spark, fan, idle and auxiliary-output assignment and any hardware mods.
4. Determine reusable I/O for IAC STEP/DIR (or alternative driver interface), including signal polarity and electrical constraints.
5. Inspect timing/interrupt use for injection, RPM capture, PWM, serial transfer and any optional ignition features.
6. Audit code size, flash/page layout, RAM consumption and calibrations.
7. Inspect existing wideband scaling, AFR-target table, feedback logic and tuning-serial fields before adding new logic.
8. Document feasibility with source references and measured or reproducible figures — not just intuition.

## Safety and test requirements

- Keep injectors safe/off on reset, watchdog faults and corrupted configuration.
- Bound EGO feedback corrections; do not let a missing or warming wideband sensor drive fueling uncontrollably.
- Bound stepper position and movement rates; define re-homing/startup behavior.
- Use an appropriate fused/protected stepper driver compatible with the actual IAC.
- Bench-test at simulated RPM/sensor states, especially crank-to-run and rapidly changing load, before engine operation.
- Build and flashing are **separate, explicitly authorized stages**.
