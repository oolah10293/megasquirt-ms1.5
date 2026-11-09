# Proposed MS1.5 I/O allocation — GM 4.3 TBI

**Status 2026-11-08:** Source-based **candidate design**, not verified physical wiring and not a completed continuity check. No firmware or hardware modifications performed.

## Evidence and nomenclature

- **Physical board:** Owner's photographs show **MegaSquirt V3.0 MB** with an original MS1 processor in the 40-pin socket (no MS2/MS3 daughtercard).
- **Owner's clarification (2026-11-08):** Two added transistor/resistor output stages connect to **JS2 and JS3**, and **both are currently unused**. Those pads are **already directly wired to original MS1 MCU output pins**, established below. The added *transistor circuits'* voltage levels, output polarity and external connector destinations still require verification.
- **Original processor mapping:** The uploaded `029y4a/src/msns-extra.h:19-80` maps MS1 CPU ports; these are **not** the MS3 CPU-to-JS-pad assignments in the uploaded MS3 hardware guide.
- **V3.0 connector routing:** The official V3.0 assembly guide identifies JS0–JS3 as **jumper pads**, normally connected to the IAC-labelled DB37 connector signals in **MS2 configurations** (JS0→IAC1A/DB37-25, JS1→IAC1B/DB37-27, JS2→IAC2A/DB37-29, JS3→IAC2B/DB37-31). This **does not create MS2 stepper motor outputs on an MS1**; it identifies available routing options, subject to the actual board's jumpering. Source: https://www.megamanual.com/ms2/V3assemble.htm

## Verified JS2 / JS3 pad assignment

**Exact physical pad mapping — VERIFIED FROM TWO INDEPENDENT PROJECT ARTIFACTS:** The official V3.0 schematic (https://www.megamanual.com/ms2/megasquirt_ShemV3.00.pdf, sheet 1) routes **JS2 directly to DIP-40 socket pin 36** and **JS3 directly to socket pin 35**. With the original MS1 MC68HC908GP32 installed, these are **PTA3** and **PTA2**, respectively. The uploaded `029y4a/src/msns-extra.h:19-25,62-70` defines **PTA3=Output 1 (X4)/boost**, **PTA2=Output 2 (X5)**. Even more explicitly, the firmware's tuning definition `029y4a/msns-extra.ini:1383,1389` labels them **“OUTPUT 1 (X4 / JS2)”** and **“OUTPUT 2 (X5 / JS3)”**. These are *direct MCU outputs*, not just anonymous connector-wire routing points. The MS2-specific names **IAC2A/IAC2B** describe what a different daughtercard would use the same socket pins for; MS1 does **not** contain that driver's electronics.

| Pad | Socket pin | Actual MS1 CPU pin | 029y4a output/feature |
| --- | ---: | --- | --- |
| **JS2** | **36** | **PTA3 / port A bit 3** | **X4 / Output 1**, shared with optional boost-control PWM |
| **JS3** | **35** | **PTA2 / port A bit 2** | **X5 / Output 2**, general programmable output |

The 029y4a firmware initializes both as outputs (`msns-extra.asm:898-900` sets `DDRA=$FF`). Its existing programmable output routine writes both pins (`msns-extra.asm:4609-4810`); boost control writes **PTA3** (`msns-extra.asm:9441-9447`). These writes must be removed or excluded by the MS1.5 configuration before giving those pins to STEP/DIR.

## Preferred output allocation — logic pins verified, external driver wiring not verified

| Role | Candidate MS1 CPU signal / hardware | Existing firmware use | Proposed treatment | Confidence |
| --- | --- | --- | --- | --- |
| Injector 1 | PTD4 / injector 1 | Injector drive | **Preserve** | Source-verified; physical harness not traced |
| Injector 2 | PTD5 / injector 2 | Injector drive | **Preserve** | Source-verified; physical harness not traced |
| Tach/RPM input | Existing IRQ/tach path | Injection timing / RPM | **Preserve** even though MS1 does not command spark | Source-verified architecture; actual input source unknown |
| O₂ / EGO | PTB5 / AD5 | Existing EGO conversion | **Preserve** and calibrate for external wideband controller | Source-verified |
| Fuel pump | PTA0 | Pump relay | **Preserve** | Source-verified |
| Cooling fan | **One** of original supported fan configurations: PTA5/X2 or PTC2/LED18 | Coolant on/off with hysteresis, `msns-extra.asm:4971-5009` | **Preserve whichever physical output is actually installed**; never allocate both by assumption | Firmware options source-verified; actual hardware unverified |
| **IAC STEP** | **PTA3 / JS2 (X4)** | Programmable Output 1, alternative boost PWM | **Preferred STEP** using existing unused connection; reassign exclusive firmware ownership | CPU pad and source function verified; added transistor stage electrical suitability unverified |
| **IAC DIR** | **PTA2 / JS3 (X5)** | Programmable Output 2 | **Preferred DIR** using existing unused connection; reassign exclusive firmware ownership | CPU pad and source function verified; added transistor stage electrical suitability unverified |
| **Fallback STEP/DIR** | PTC0 / LED17 and PTC1 / LED19 | Squirt/Accel LEDs and optional ignition | **Fallback only** if JS2/JS3 added stages or connector routing cannot be made suitable | Source mapping verified; physical routing would require additional work |
| IAC driver enable (optional, preferred for final design) | PTA1 / FIDLE | Existing PWM idle drive or spark depending on options | Consider for **nENABLE** after replacing PWM idle actuator; hardware polarity and current/signal conditioning must be checked | Candidate only |

### Why the existing JS2/JS3 pins are now preferred

They **are** PTA3 and PTA2 on the MS1, directly. We do **not** need to wire separate LED outputs into these pads. Both are unused according to the owner. MS1.5 should take exclusive software ownership of these bits instead of leaving generic output/boost handlers active.

- **PTA3 / JS2 / X4:** `Output1` and `boostP` share port A bit 3 (`msns-extra.h:66,70`). Disable or gate existing programmable Output 1 and boost PWM writes.
- **PTA2 / JS3 / X5:** `Output2` is port A bit 2 (`msns-extra.h:65`). Disable or gate programmable Output 2 writes.
- Initialize STEP low and DIR to a defined level; existing `clr porta` at reset is present but must be checked against the external circuit's inversion and pull-up behavior.
- Do not assume the two added transistor output stages are push-pull logic drivers; their output polarity/voltage needs inspection before a STEP/DIR interface is electrically specified.

### Connector routing proposal

**First preference:** **Reuse JS2/PTA3 for STEP and JS3/PTA2 for DIR**. These are **verified direct processor pins**. The custom transistor stages may be low-side/inverting switches, so verify electrical behavior before connecting the external driver. Bypass/rework the output stages or add appropriate pull-ups/conditioning as needed; avoid adding new processor wires unnecessarily.

**Fallback:** If JS2/JS3 routing is unsuitable, consider the unallocated **IAC1A / DB37-25** and **IAC1B / DB37-27** conductors with appropriate internal jumpers/buffers. This repurposes conductors, **not** the V3.0/MS2 stepper-driver circuit.

- JS2/JS3 circuits are **not in use** and need not be left alone. They may use the IAC2A/IAC2B connector conductors (29/31), **but their precise routing and suitability for logic pulses are not yet verified**.
- Do not infer that FIDLE/DB37-30 is available for a third enable signal until fan/output configuration is traced.
- No final connector pin assignment, external wiring, or motor-coil pinout is approved.

## Alternate assignments if front-panel LED signals are unavailable

Potentially use MS1's generic PTA2/X5 and PTA3/X4 (`msns-extra.h:20-25`) **if the existing added unused output circuits are driven by these signals and can be safely repurposed**. Confirm actual source wiring and remaining firmware owners; do not assume JS pad names represent CPU pins.

## Design gate

**Preferred logical partition:** **PTA3/JS2=STEP, PTA2/JS3=DIR**, both sourced directly from the existing MS1 socket pins and unused by the owner. Preserve **one** fan output, PTD4/PTD5 injectors, PTA0 fuel pump, tach input and analog EGO. PTA1/FIDLE is a possible optional motor-driver enable. Only the added transistor/harness circuitry, not the MCU-to-JS-pad connection, remains to be electrically validated.

This is a **logical allocation**, not a verified physical wiring diagram. Resolve exact output-source traces before any hardware hookup or flash.
