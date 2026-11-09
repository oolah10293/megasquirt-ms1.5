# MS1/Extra 029y4a firmware source audit

**Analyzed:** 2026-11-08. **Status:** Direct, read-only inspection of the uploaded ZIP; **no build/flash, no runtime bench test**.

**Important provenance:** This document cites paths and **1-based line numbers inside the owner's uploaded `029y4a.zip`**, not files currently committed to this GitHub repository. It is an inspection of the supplied firmware package, **not proof that the owner's physical ECU is running 029y4a**.

## Artifact identification and reproducibility

- ZIP: `029y4a.zip`; 426,172 bytes; SHA-256 `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`.
- Main implementation: `029y4a/src/msns-extra.asm`, 507,138 bytes, 14,944 lines; SHA-256 `a80d055ebed3349c7bc3541a7d1c63c824bed85d290c41638cd659f63aa9e928`.
- MCU/variable definitions: `029y4a/src/msns-extra.h`, 30,544 bytes; SHA-256 `38fe8d9cca8709841147be05925cba60369653952d5606f9e5b6540933ebe37a`.
- Tuning definition: `029y4a/msns-extra.ini`, 185,716 bytes; SHA-256 `6e4725fa99d20115dff19acf2adc2f0d9dc8013a86bf5d269e9ed4e51ce7a6aa`.
- Precompiled S-record firmware: `029y4a/msns-extra.s19`, 76,808 bytes; SHA-256 `06bbdf436f4be7803c749d9d1d1a6344d8b66e20fb1135d9691bfb499b2486d1`.
- The package also includes calibration table `.inc` files, `src/Gp32.equ`, `src/boot_r12.asm`, legacy Windows assembler `src/CASM08Z.EXE`, `src/compile.bat`, sample `.msq` tunes, and readme/upgrading instructions. The assembler/batch files were **not executed**.
- The ZIP's `readme.txt` identifies **MS1/Extra 029y4** and supports MegaTune 2.25, TunerStudio and MegaTunix.
- `msns-extra.asm:13733-13737` embeds code revision `MS1/Extra rev 029y4`, while the tuning-data signature remains `MS1/Extra format 029y3` because the data format did not change. **Do not interpret this as proof of a wrong firmware/INI pairing.**

## 1. MS1 processor / original port assignments — VERIFIED IN SOURCE

`src/msns-extra.h:19-80` enumerates the original controller's port/function mapping:

| Original MS1 MCU signal | Source-defined function | Evidence |
| --- | --- | --- |
| PTA0 | Fuel-pump relay control | `msns-extra.h:19-21,62-68` |
| PTA1 | **FIDLE** (existing idle actuator) | `msns-extra.h:19-21,62-68` |
| PTA2, PTA3 | Generic outputs X5 / X4 | `msns-extra.h:22-25,64-66` |
| PTA5 | **X2 / fan** (or water injection) | `msns-extra.h:25,67-68` |
| **PTA3 / DIP40 pin 36 / JS2** | **X4 / Output 1**, also boost-control PWM | `msns-extra.h:23,66,70`; `msns-extra.ini:1383` |
| **PTA2 / DIP40 pin 35 / JS3** | **X5 / Output 2** | `msns-extra.h:22,65`; `msns-extra.ini:1389` |
| PTC0, PTC1, PTC2 | LED17, LED19, LED18; optional spark/other uses | `msns-extra.h:39-44,73-80` |
| PTD4, PTD5 | Injector outputs 1 and 2 | `msns-extra.h:46-52,55-60` |
| PTB5/AD5 | Primary EGO/O₂ analog input | `msns-extra.h:29-37` |
| PTB6/AD6, PTB7/AD7 | Optional analog inputs X7, X6 | `msns-extra.h:35-37` |

**These are original MS1 firmware MCU mappings.** The **V3.0 mainboard schematic** independently confirms that JS2/JS3 are direct taps from MS1 DIP-40 socket pins 36/35, respectively. The owner's photo confirms the V3.0 board and the owner confirms the added JS2/JS3 circuits are unused. This **does not prove the added transistor stages' electrical behavior or downstream connector routing**. In particular, do not substitute MS3 CPU/JS mappings for the original MS1.

The `msns-extra.ini:260-304` tuning configuration includes FIDLE/spark selection, three LED assignments, X2 fan selection, and additional programmable outputs. The original source's configuration check at `msns-extra.asm:1235-1265` explicitly accommodates a *fuel-only* configuration (no spark output control). **A usable RPM/tach input is still necessary for injection and closed-loop idle.** This conclusion is based on the code's RPM-dependent operation, not on a verified engine wiring diagram.

## 2. Idle control — MOST OF THE ALGORITHM ALREADY EXISTS

The firmware implements on/off idle and two-wire PWM idle control; it **does not expose a native four-wire stepper actuator in this package**:

- `msns-extra.asm:5286-5319` selects FIDLE idle mode and enters PWM/warm-up or closed-loop idle.
- `msns-extra.asm:5323-5387` handles coolant-based warm-up, cranking/startup duty and a settling period.
- `msns-extra.asm:5391-5546` handles TPS-based idle entry, target RPM derived from coolant temperature, an RPM deadband, dashpot, closing rate, proportional-to-error **update frequency**, and 1-unit steps of `idleDC`.
- `msns-extra.asm:9370-9406` is the *actuator* stage, modulating the **single FIDLE/ PTA1 output** from `idleDC` and `idlefreq_f`.
- `msns-extra.ini:949-983,1485-1526` exposes existing tuning controls: PWM mode, warmup/closed-loop selection, fast/hot idle RPM, throttle threshold, deadband, recovery timing, startup, and dashpot.

**Design implication (inference, not an implemented feature):** Preserve and adapt the existing closed-loop RPM/warm-up/dashpot *logic* where suitable; replace or extend its PWM actuator layer with a target-position + direction/step-pulse scheduler for the external driver. A stepper will need bounded position tracking, startup referencing/homing, movement scheduling independent of injector critical timing, and safe initialization. The existing `idleDC` could be a command quantity, but its semantics and resolution must be redesigned/validated.

**Not yet proven:** Available distinct physical outputs, whether the chosen stepper driver's command interface matches the GM IAC, timer/interrupt priority, flash/RAM headroom, and acceptable response time. No actual stepper code or real-time performance was tested.

## 3. Cooling fan — FEATURE ALREADY PRESENT

`msns-extra.asm:4971-5009` implements fan control via **X2/PTA5 and/or LED18/PTC2**, depending on configuration. It has separate coolant-based on/off temperatures (hysteresis) and turns off during cranking.

- `msns-extra.ini:272-278,303-304` selects fan output usage.
- `msns-extra.ini:585-592,1411-1413` defines fan on/off thresholds and tuning controls.
- `msns-extra.asm:1291-1300` checks for an **X2 fan vs. water-injection conflict**.
- `msns-extra.asm:4900-4911` shows LED18 also has generic-output conflicts.

**Project requirement:** One fan output, and no more. **The owner's already-added output wiring is still unverified**, so we cannot assign its physical line yet. Preserve the existing fan implementation where compatible.

## 4. Wideband AFR targeting — ALREADY PRESENT, NOT JUST A DISPLAY

Earlier discussion suggested MS1 needed AFR-target-based EGO control added from scratch. **That was incorrect for this 029y4a package.**

- `msns-extra.asm:13466-13659`: Two **8x8 AFR target lookup tables** for different VE-table modes. The lookup uses RPM plus MAP/load or TPS/Alpha-N configuration and interpolation.
- `msns-extra.asm:14602-14662`: Actual AFR table values in firmware flash, represented internally as **raw 0–255 ADC counts from the O₂ analog signal**.
- `msns-extra.asm:3019-3050`: Selects fixed EGO target or the applicable AFR table target.
- `msns-extra.asm:3052-3148`: Already compares measured EGO with target and changes EGO fuel correction in **bounded steps**. Includes 30-second startup suppression, coolant/RPM thresholds, TPS/MAP-based open-loop disable conditions, accel/decel exclusions and two configurable limits according to load. See especially `3097-3143` for the narrowband vs. wideband direction branches and adjustment limits.
- `msns-extra.ini:800-877,2684-2771`: AFR-table definitions support multiple named wideband transfer functions / scaling configurations (including Innovate, AEM, Tech Edge, etc.).
- `msns-extra.ini:1255-1264`: EGO sensor type, step size, authority, operating conditions exposed for tuning.

**Design implication (inference):** Start with the existing 8x8 lookup and EGO feedback. Potential work is compatibility with the actual wideband controller and improvements to validation/fail-safe behavior, control quality, logging, and tuning UI—not inventing AFR-target feedback from zero.

**Critical caveat:** Existing code compares **raw voltages/ADC units**, not an inherently universal AFR value. The particular wideband controller's voltage–AFR transfer function and **signal direction/polarity** must match the tuned table and correction logic. No wideband sensor/controller model has been selected or verified. Do not assume all 0–5 V widebands have the same scaling.

## 5. Fueling and tuning — EXISTING STRUCTURE

- `msns-extra.h:46-52`: Two injector-control channels (PTD4 and PTD5).
- `msns-extra.asm:9310-9370`: Existing injector PWM/current-limiting timing and shutdown paths are present; maintain safety semantics.
- `msns-extra.ini:80-138,140-158,750-760`: VE tables are **12x12**. The INI exposes injector PWM and opening-time parameters and engine-speed/load setup.
- `msns-extra.ini:949-983`: Idle configuration already has its own page (page 9).
- Package `readme.txt`: MegaTune 2.25, TunerStudio and MegaTunix support; bundled `msns-extra.ini` and sample tunes. A more useful tuning interface may build upon these definitions rather than invent a new protocol.

**Safety note from package:** `readme.txt` explicitly warns that an upgrade from some earlier 029-series firmware changed 3-/4-bar MAP sensor scaling and **requires a VE retune**. This is not permission to load the included image or default tunes onto a running ECU.

## 6. Resource limitations and what this inspection does NOT prove

- The provided `src/mem_map.txt` identifies itself as correct for **029h (February 2006)**, so its exact variable/address map must **not** be treated as authoritative for 029y4a.
- The S19 contains Motorola S1 records spanning addresses roughly **0x8128–0xFFFF**; it includes code, calibrations/tables, and vector/boot-related locations. Raw unoccupied address ranges do **not** establish allocatable flash or timing headroom.
- `msns-extra.asm:13749` requires main code to remain before `$DFFF`; `13753+` contains vector-related definitions. Exact available headroom needs an assembler map/listing and an approved compile; **none has been performed**.
- Existing pin/port names do not prove spare outputs after the owner's previous board changes.
- Disabling the *function* of ignition does not automatically remove compiled code or free RAM. A deliberate firmware source refactor would be needed to reclaim some resources.

## 7. Scope and licensing caution

The archive includes copyright notices and a request that original authors' headers be retained on derivatives (`msns-extra.h:1-10`, `msns-extra.asm:~628-638`). **No explicit general redistribution license was verified in the uploaded ZIP.** For now, the repository records *audit findings* and artifact hashes; the original third-party code, S19 firmware image, and proprietary Windows assembler binary have **not** been mirrored into this public repository. Source reuse / redistribution terms should be checked before importing a derivative tree.

## Priority next engineering work (not authorized to build)

1. Confirm board revision, actual I/O mods, one fan output wiring, and which inputs the physical MS1 uses for RPM.
2. Audit selected output pins against injector/fan/serial/idle uses, including electrical protection of external STEP/DIR driver inputs.
3. Determine target IAC type, coil electrical characteristics, driver interface, and required position range/homing.
4. Evaluate timer/interrupt and memory changes, then draft an implementable source-level design.
5. Validate the owner's wideband controller calibration before any AFR changes.
6. Separate future code development, compilation, flashing and vehicle testing into expressly authorized stages.
