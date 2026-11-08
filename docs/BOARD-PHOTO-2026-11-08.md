# Physical MS1 board photo — initial identification

**Reviewed:** 2026-11-08. **Source:** owner's front-side photograph `20261108_184902.jpg` posted in conversation. **Status:** Visual inspection only; no electrical tracing, continuity measurements, or reverse-side view.

## Directly visible / established by the photograph

- **Board revision marked on PCB silkscreen:** `MegaSquirt V3.0 MB` (right board edge in supplied orientation). This establishes the *mainboard* revision from the actual hardware, not an assumption based on a downloaded manual.
- **Processor:** Large, directly mounted/socketed 40-pin Motorola/Freescale device; the package marking appears to begin `MC68HC908GP32`, consistent with MS1. The remaining package suffix is faint. **No MS2/MS3-style processor daughtercard is present.**
- **Visible rework/custom additions:** The lower-right `Proto Area` has two small black three-lead packages (likely transistors, but specific parts not identified) and two vertically mounted axial resistors, with **red and white wires** attached. The wires run along the right side towards the upper connector area.
- Some additional hand-soldered/jumper work is visible near the central `U7` / `R44` area. Its electrical function is **not established** from the photograph.
- The original board edge has three LED indicators (`D14`, `D15`, `D16` nearby silkscreen).
- The connector arrangement and input/output circuits visibly match the *general style* of a MegaSquirt V3.0 mainboard.

## November 8, 2026 — underside photo and owner clarification

**New directly supplied evidence:** The owner provided an underside/solder-side photograph (`20261108_185619.jpg`) and explicitly identified the two custom output circuits as **connected to JS2 and JS3**. Treat this as an **owner-confirmed wiring fact**, not as a deduction from indistinct solder traces. The underside visibly contains point-to-point/jumper wiring around the processor-socket/proto area.

**Important pad distinction:** The V3.0 mainboard's **JS2/JS3 solder pads** are not inherently the same thing as the **original MS1 MCU's port pins**. The MegaSquirt V3.0 assembly guide documents JS2 and JS3 as the **MS2** stepper-channel 2A/2B interface, optionally jumpered to DB37 pins **29 and 31**, respectively (https://www.megamanual.com/ms2/V3assemble.htm). That published MS2 routing **does not demonstrate** that this MS1 PCB has active MS2-style stepper drivers or that the user's two added circuits use those DB37 pins. We must distinguish what **feeds** those custom circuits from what pad or connector they **terminate** at.

**Still unresolved:** Which existing software outputs command the two circuits; what external signals/loads each controls (including the requested single fan); exact component part numbers; whether they can be retained when assigning stepper STEP/DIR signals. Do not count JS2 and JS3 as proven spare MCU outputs or as ready-to-drive IAC motor connections without tracing.

The rear photograph and owner's clarification supersede the earlier request below for an underside picture.

## Explicitly NOT concluded from this photograph

- The two proto-area stages are **not identified as fan outputs**. They may be relevant to the owner's earlier output additions, but their functions, transistor part numbers and resistor values cannot be verified from the front image alone.
- **One fan output** remains the owner's confirmed *requirement*, not proof of which physical circuit controls it.
- **Updated by owner:** The two added outputs connect to **JS2 and JS3**. Their originating MCU/control signals and downstream external-load connections remain unverified by a complete trace.
- The small resistors on the proto area are not evidence of the owner's separate claimed injector-current-limiting resistors; that purpose and the resistor inventory remain unverified.
- The photo does not establish which 029-series firmware is actually installed or how the board is configured electrically.
- **This is MS1 silicon on a V3.0 mainboard:** an MS3/V3.0 hardware manual has **shared-board relevance**, but its MS3-specific CPU port mappings, daughtercard IAC driver outputs, and integrated stepper support **do not transfer** to MS1.

## Relevance to MS1.5 design

1. The **V3.0 mainboard revision is now physically confirmed**. Obtain the MS1/V3.0-specific mainboard schematic for exact trace and connector mapping.
2. The **two custom outputs terminate at JS2 and JS3**, per owner. The remaining unknown is which MCU/control signals feed these circuits, where they leave the board, and which load each serves.
3. Candidate fan/IAC outputs should be selected only after tracing these custom connections and the original MS1 port assignments from the 029y4a source (`docs/SOURCE-AUDIT-029Y4A.md`).
4. **Next analysis:** Trace these output circuits from the processor-side signal source through the driver transistors to JS2/JS3 and/or external connector. The underside photograph is now supplied; no additional photo should be requested merely to establish that it exists.

## Provenance note

The photograph was inspected in conversation and **has not been uploaded into this public repository**. This Markdown file records observations and confidence limits; preserve the original photo outside the repo unless the owner explicitly requests otherwise.
