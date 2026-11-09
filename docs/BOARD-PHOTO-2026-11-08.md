# Physical MS1 board photo — initial identification

**Reviewed:** 2026-11-08. **Source:** owner's front-side photograph `20261108_184902.jpg` posted in conversation. **Status:** Visual inspection only; no electrical tracing, continuity measurements, or reverse-side view.

## Directly visible / established by the photograph

- **Board revision marked on PCB silkscreen:** `MegaSquirt V3.0 MB` (right board edge in supplied orientation). This establishes the *mainboard* revision from the actual hardware, not an assumption based on a downloaded manual.
- **Processor:** Large, directly mounted/socketed 40-pin Motorola/Freescale device; the package marking appears to begin `MC68HC908GP32`, consistent with MS1. The remaining package suffix is faint. **No MS2/MS3-style processor daughtercard is present.**
- **Visible rework/custom additions:** The lower-right `Proto Area` has two small black three-lead devices, two vertically mounted axial resistors, and **red and white wires** running along the right side towards the upper connector area. **Owner later identified the two devices as 2N2222 NPN transistors and the resistors as gold–red–black–brown bands (read backwards as brown–black–red–gold = nominally 1 kΩ ±5%).** The precise electrical connections are not yet traced.
- Some additional hand-soldered/jumper work is visible near the central `U7` / `R44` area. Its electrical function is **not established** from the photograph.
- The original board edge has three LED indicators (`D14`, `D15`, `D16` nearby silkscreen).
- The connector arrangement and input/output circuits visibly match the *general style* of a MegaSquirt V3.0 mainboard.

## November 8, 2026 — underside photo and owner clarification

**New directly supplied evidence:** The owner provided an underside/solder-side photograph (`20261108_185619.jpg`) and explicitly identified the two custom output circuits as **connected to JS2 and JS3**. Treat this as an **owner-confirmed wiring fact**, not as a deduction from indistinct solder traces. The underside visibly contains point-to-point/jumper wiring around the processor-socket/proto area.

**Exact pad mapping now verified:** The V3.0 CPU schematic (https://www.megamanual.com/ms2/megasquirt_ShemV3.00.pdf, sheet 1) shows **JS2 wired directly to DIP-40 socket pin 36 (MS1 PTA3)** and **JS3 to pin 35 (MS1 PTA2)**. `029y4a/msns-extra.ini:1383,1389` explicitly identifies **Output 1 (X4/JS2)** and **Output 2 (X5/JS3)**. The owner's two added stages are connected to these pads and are unused. For an MS2 daughtercard those same pins have *different functions* (IAC2A/2B); MS1 has no internal motor-driver electronics. **Do not mistake socket-to-pad continuity for verified DB37 harness routing or transistor electrical suitability.**

**Owner update:** Both added JS2/JS3 output circuits are **unused**. They are directly driven from **PTA3/Output 1** and **PTA2/Output 2**, respectively, based on the confirmed PCB pad map. Owner subsequently identified **2N2222 NPN transistors** and **1 kΩ ±5% (brown–black–red–gold) resistors**. These MCU channels remain candidate IAC STEP/DIR outputs. **Still unresolved:** transistor emitter/base/collector wiring, whether each 1 kΩ resistor is in the base drive or elsewhere, external connector routing, output polarity and suitability as driver logic inputs.

The rear photograph and owner's clarification supersede the earlier request below for an underside picture.

## Explicitly NOT concluded from this photograph

- The two proto-area stages are **confirmed unused by the owner**. **Their components have now been identified by the owner as 2N2222 NPN transistors and gold–red–black–brown resistors (nominally 1 kΩ ±5% when read from brown end).** These values are owner-supplied/component-code interpreted, **not independently measured**. The one required fan output must be allocated independently.
- **One fan output** remains the owner's confirmed *requirement*, not proof of which physical circuit controls it.
- **Updated with schematic + firmware verification:** The two owner-added outputs connect to **JS2 (PTA3/X4/Output 1)** and **JS3 (PTA2/X5/Output 2)**. The **downstream circuitry and external-load connections** remain unverified.
- The small resistors on the proto area are not evidence of the owner's separate claimed injector-current-limiting resistors; that purpose and the resistor inventory remain unverified.
- The photo does not establish which 029-series firmware is actually installed or how the board is configured electrically.
- **This is MS1 silicon on a V3.0 mainboard:** an MS3/V3.0 hardware manual has **shared-board relevance**, but its MS3-specific CPU port mappings, daughtercard IAC driver outputs, and integrated stepper support **do not transfer** to MS1.

## Relevance to MS1.5 design

1. The **V3.0 mainboard revision is now physically confirmed**. Obtain the MS1/V3.0-specific mainboard schematic for exact trace and connector mapping.
2. The **two custom outputs are unused** per owner, and the source signals are **confirmed as PTA3/JS2 and PTA2/JS3**. Prefer repurposing them for STEP/DIR; only their transistor-stage electrical behavior and external routing remain to be traced.
3. **Preferred IAC signals are now JS2/PTA3=STEP and JS3/PTA2=DIR.** Firmware must stop existing Output 1/Output 2/boost-control writes. See [I/O allocation](IO-ALLOCATION-MS1-V30.md). Preserve one independent fan output.
4. **Next analysis:** Trace the **post-pad circuitry** from JS2/JS3 through the added transistors and connector paths; the **processor-side pad assignment no longer needs tracing**. The underside photograph is already supplied.

## Provenance note

The photograph was inspected in conversation and **has not been uploaded into this public repository**. This Markdown file records observations and confidence limits; preserve the original photo outside the repo unless the owner explicitly requests otherwise.
