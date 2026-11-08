# Research status and evidence log

**Updated 2026-11-08 after directly inspecting uploaded files.** This document separates owner-confirmed project facts, facts established from supplied artifacts, and remaining unknowns.

## Owner-confirmed project facts

- GM 4.3L TBI is the target engine; an existing MegaSquirt MS1 is to be reused.
- The MS1 **will not control spark**. It still needs a usable RPM/tach input to calculate injection and idle corrections.
- One fan output is required.
- A stepper IAC is wanted; preference is **MS1 firmware driving an external driver**, not a second ECU.
- Wideband O₂ closed-loop AFR and better tuning are major goals.
- The owner already has resistors; their specific purpose and values have not been verified.
- The earlier engine setup ran without an IAC. Do not assume that setup's wiring applies to the GM 4.3.

## Verified from supplied MS1/Extra ZIP

The user provided `029y4a.zip` (historical MS1/Extra 029y4a source/binary/tuning package). The ZIP **does contain** the complete main `msns-extra.asm` assembly source, `msns-extra.h` CPU definitions, `msns-extra.ini` tuning definition, `msns-extra.s19` and legacy assembler tools. This is a source **inspection**, not a compile or runtime validation.

**Most important findings:**

1. **Native fan control exists:** X2/PTA5 or LED18/PTC2; separate on/off coolant thresholds. See `msns-extra.asm:4971-5009`. One fan output suffices for the project.
2. **Closed-loop PWM idle exists:** coolant-temperature targets, RPM error/deadband, startup, dashpot, idle recovery and FIDLE actuator. See `msns-extra.asm:5286-5546,9370-9406`. **No stepper-actuator routine found** in the inspected package. Adapting PWM demand to stepper positioning is proposed, not yet designed or proven.
3. **Wideband AFR targets and correction already exist:** two 8x8 tables and stepwise, bounded EGO correction. See `msns-extra.asm:3019-3149,13466-13659,14602-14662`, `msns-extra.ini:800-877`. Earlier discussion describing this as absent needs correcting for 029y4a.
4. **Original MS1 CPU signals are mapped in its own header:** PTA1=FIDLE; PTA5=X2/fan; PTC0/1/2=LED17/19/18 alternatives; PTD4/5=injectors; PTB5=EGO. See `msns-extra.h:19-80`. **Physical modified-board connector wiring remains unknown.**
5. **Existing tuning structure:** 12x12 VE tables, EGO/idle/fan configuration, and bundled INI; readme lists TunerStudio/MegaTune/MegaTunix. No need to reinvent those from zero.
6. Package readme warns that certain older 029-series MAP sensor changes require a VE retune. Don't flash legacy firmware or assume old tune compatibility.

For exact file names, hashes, and source line references see **[SOURCE-AUDIT-029Y4A.md](SOURCE-AUDIT-029Y4A.md)**.

## Uploaded hardware manual: caveat

`MS3baseV30_Hardware-1.5.pdf` is explicitly an **MS3 1.5.x on a V3.0 mainboard** guide from 2018. It is **not an MS1 guide**. Its general V3.0 mainboard schematics and connector context can be useful once this ECU's PCB revision is confirmed, but the MS3-specific CPU pin assignments and motor drivers do not establish MS1 capabilities.

See **[HARDWARE-MANUAL-SCOPE.md](HARDWARE-MANUAL-SCOPE.md)**.

## Still not verified

- PCB revision and existing add-on circuitry, especially fan outputs and available signals.
- Firmware version currently installed in the user's MS1; 029y4a is **an available reference baseline**, not necessarily its installed version.
- Injector type/impedance and series resistor specifications.
- GM stepper IAC model, coil configuration, electrical limits and correct driver choice.
- Whether a suitable STEP/DIR (or alternative) interface can be driven using otherwise-unused I/O.
- Flash/RAM headroom, MCU/interrupt priorities and timing during fuel scheduling.
- Actual wideband controller model, analog voltage/AFR transfer function and polarity.
- Correct MS1-specific V3.0 schematic and connector routing.
- Source redistribution permissions for the historical firmware; uploaded ZIP has copyright headers but no verified redistribution license.

## Safety and working practices

- No ECU or software build, release, firmware flashing, or hardware rewiring was authorized by the documentation request.
- Preserve reliable fuel/injector timing and safe startup/shutdown states.
- Handle loss/warm-up/errors from O₂ controller with bounded or disabled EGO corrections.
- Bound IAC movement and define startup homing/reference and fault response.
- Bench-test injection/IAC/fan/tach input and fault cases before running an engine.
- Source files have been *inspected*, not mirrored to this public repo, pending source licensing review.
