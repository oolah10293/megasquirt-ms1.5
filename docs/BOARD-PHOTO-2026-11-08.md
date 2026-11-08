# Physical MS1 board photo — initial identification

**Reviewed:** 2026-11-08. **Source:** owner's front-side photograph `20261108_184902.jpg` posted in conversation. **Status:** Visual inspection only; no electrical tracing, continuity measurements, or reverse-side view.

## Directly visible / established by the photograph

- **Board revision marked on PCB silkscreen:** `MegaSquirt V3.0 MB` (right board edge in supplied orientation). This establishes the *mainboard* revision from the actual hardware, not an assumption based on a downloaded manual.
- **Processor:** Large, directly mounted/socketed 40-pin Motorola/Freescale device; the package marking appears to begin `MC68HC908GP32`, consistent with MS1. The remaining package suffix is faint. **No MS2/MS3-style processor daughtercard is present.**
- **Visible rework/custom additions:** The lower-right `Proto Area` has two small black three-lead packages (likely transistors, but specific parts not identified) and two vertically mounted axial resistors, with **red and white wires** attached. The wires run along the right side towards the upper connector area.
- Some additional hand-soldered/jumper work is visible near the central `U7` / `R44` area. Its electrical function is **not established** from the photograph.
- The original board edge has three LED indicators (`D14`, `D15`, `D16` nearby silkscreen).
- The connector arrangement and input/output circuits visibly match the *general style* of a MegaSquirt V3.0 mainboard.

## Explicitly NOT concluded from this photograph

- The two proto-area stages are **not identified as fan outputs**. They may be relevant to the owner's earlier output additions, but their functions, transistor part numbers and resistor values cannot be verified from the front image alone.
- **One fan output** remains the owner's confirmed *requirement*, not proof of which physical circuit controls it.
- The red/white wires' destinations at the connector, their ECU processor source signals, and what the underside tracks connect to **cannot be traced conclusively** from a top-only view.
- The small resistors on the proto area are not evidence of the owner's separate claimed injector-current-limiting resistors; that purpose and the resistor inventory remain unverified.
- The photo does not establish which 029-series firmware is actually installed or how the board is configured electrically.
- **This is MS1 silicon on a V3.0 mainboard:** an MS3/V3.0 hardware manual has **shared-board relevance**, but its MS3-specific CPU port mappings, daughtercard IAC driver outputs, and integrated stepper support **do not transfer** to MS1.

## Relevance to MS1.5 design

1. The **V3.0 mainboard revision is now physically confirmed**. Obtain the MS1/V3.0-specific mainboard schematic for exact trace and connector mapping.
2. The relevant unknown is now **how the existing custom proto-area circuits and added wiring are connected**, not whether there is a daughtercard.
3. Candidate fan/IAC outputs should be selected only after tracing these custom connections and the original MS1 port assignments from the 029y4a source (`docs/SOURCE-AUDIT-029Y4A.md`).
4. **Most useful next physical evidence:** One reasonably sharp **photo of the solder/underside of this same PCB**, with the lower-right proto area and DB37 connector-side pads visible. No disassembly beyond normal board access, wiring changes, or firmware builds authorized or needed.

## Provenance note

The photograph was inspected in conversation and **has not been uploaded into this public repository**. This Markdown file records observations and confidence limits; preserve the original photo outside the repo unless the owner explicitly requests otherwise.
