# Proposed MS1.5 I/O allocation — GM 4.3 TBI

**Status 2026-11-08:** Source-based **candidate design**, not verified physical wiring and not a completed continuity check. No firmware or hardware modifications performed.

## Evidence and nomenclature

- **Physical board:** Owner's photographs show **MegaSquirt V3.0 MB** with an original MS1 processor in the 40-pin socket (no MS2/MS3 daughtercard).
- **Owner's clarification:** Two added transistor/resistor output stages connect to **JS2 and JS3**. Their upstream control signal, downstream connector/load and fan assignment remain **unverified**.
- **Original processor mapping:** The uploaded `029y4a/src/msns-extra.h:19-80` maps MS1 CPU ports; these are **not** the MS3 CPU-to-JS-pad assignments in the uploaded MS3 hardware guide.
- **V3.0 connector routing:** The official V3.0 assembly guide identifies JS0–JS3 as **jumper pads**, normally connected to the IAC-labelled DB37 connector signals in **MS2 configurations** (JS0→IAC1A/DB37-25, JS1→IAC1B/DB37-27, JS2→IAC2A/DB37-29, JS3→IAC2B/DB37-31). This **does not create MS2 stepper motor outputs on an MS1**; it identifies available routing options, subject to the actual board's jumpering. Source: https://www.megamanual.com/ms2/V3assemble.htm

## Preferred logical pin assignment — not yet physical pin assignment

| Role | Candidate MS1 CPU signal / hardware | Existing firmware use | Proposed treatment | Confidence |
| --- | --- | --- | --- | --- |
| Injector 1 | PTD4 / injector 1 | Injector drive | **Preserve** | Source-verified; physical harness not traced |
| Injector 2 | PTD5 / injector 2 | Injector drive | **Preserve** | Source-verified; physical harness not traced |
| Tach/RPM input | Existing IRQ/tach path | Injection timing / RPM | **Preserve** even though MS1 does not command spark | Source-verified architecture; actual input source unknown |
| O₂ / EGO | PTB5 / AD5 | Existing EGO conversion | **Preserve** and calibrate for external wideband controller | Source-verified |
| Fuel pump | PTA0 | Pump relay | **Preserve** | Source-verified |
| Cooling fan | **One** of original supported fan configurations: PTA5/X2 or PTC2/LED18 | Coolant on/off with hysteresis, `msns-extra.asm:4971-5009` | **Preserve whichever physical output is actually installed**; never allocate both by assumption | Firmware options source-verified; actual hardware unverified |
| Extra outputs | Owner's transistor/resistor stages at JS2 and JS3 | Unknown signal source/load | **Reserve / don't rewire** until actual destination and active function are established | Connections confirmed by owner only |
| **IAC STEP** | **PTC0 / LED17 / D14** | Injector event LED / optional ignition A | Preferred dedicated STEP signal; disable or replace **all existing writes** to PTC0 in the MS1.5 configuration | CPU port source-verified; availability is design hypothesis |
| **IAC DIR** | **PTC1 / LED19 / D16** | Acceleration LED / optional ignition B | Preferred dedicated DIRECTION signal; disable or replace **all existing writes** to PTC1 in MS1.5 | CPU port source-verified; availability is design hypothesis |
| IAC driver enable (optional, preferred for final design) | PTA1 / FIDLE | Existing PWM idle drive or spark depending on options | Consider for **nENABLE** after replacing PWM idle actuator; hardware polarity and current/signal conditioning must be checked | Candidate only |

### Why PTC0/PTC1?

They are individual CPU outputs documented in the actual **MS1** header, and the owner will not use MS1-controlled spark. Their legacy LED function is dispensable in an IAC-focused firmware. **However, the source still writes these bits in fuel-only operation**, so their apparent availability **is not** enough: MS1.5 must ensure one software owner per output.

Source examples needing audit and removal/gating:
- Injector LED state: `msns-extra.asm:9232,9252,9457`, plus related paths.
- Acceleration LED state: `msns-extra.asm:2616-2619,2865-2867,2906-2908,2926-2928`.
- Initial port setup / stall/spark safety macro: `msns-extra.asm:892-904,6915-6955`.
- Other spark/coil outputs and shared features throughout the source must be **audited across all active code paths**.

**Do not simply jumper LED circuit outputs to a driver.** PTC0/PTC1 are MCU logic signals behind existing LED/resistor/transistor circuitry. Their voltages/polarity must be verified and buffered/conditioned to the external driver, with transient protection.

### Connector routing proposal

If available after inspection, prefer unused **IAC1A / DB37-25** and **IAC1B / DB37-27** as *two signal conductors* for STEP and DIR, with appropriate internal jumpers/buffers. This **repurposes connector conductors, not the V3.0/MS2 stepper-driver circuit**.

- Leave the owner-confirmed existing JS2/JS3 circuits alone. They may use the IAC2A/IAC2B connector conductors (29/31), **but their exact external routing is not verified**.
- Do not infer that FIDLE/DB37-30 is available for a third enable signal until fan/output configuration is traced.
- No final connector pin assignment, external wiring, or motor-coil pinout is approved.

## Alternate assignments if front-panel LED signals are unavailable

Potentially use MS1's generic PTA2/X5 and PTA3/X4 (`msns-extra.h:20-25`) **only after tracing existing added output circuits**. This alternative could collide with the custom JS2/JS3 stages or other owners' features.

## Design gate

**Preferred provisional partition:** PTC0=STEP; PTC1=DIR; existing custom JS2/JS3 stages reserved; keep the actual one fan output; PTD4/PTD5 injection, PTA0 fuel pump, tach input, analog EGO unchanged. PTA1/FIDLE is a possible optional motor-driver enable.

This is a **logical allocation**, not a verified physical wiring diagram. Resolve exact output-source traces before any hardware hookup or flash.
