# Uploaded hardware manual — applicability review

**Analyzed:** 2026-11-08, from the owner's upload `MS3baseV30_Hardware-1.5.pdf`.

**File SHA-256:** `664bc4e938b6739b4d4a9207d2a45aa59b4e194a258ef951f7d4574348620fc4`. 222 pages.

## Important: This is **not** an MS1 manual

- **Page 1:** The title is **MS3(base)/V3.0 Hardware Guide**, MS3 firmware 1.5.x, dated **2018-07-06**.
- **Page 1 explicitly states it applies to MS3 on a V3.0 mainboard, without MS3X, and *does not apply* to other MegaSquirt products or firmware.**
- Therefore, this PDF does **not** establish the MS1 CPU port mapping, driver capability or actual wiring of the owner's unit. The original **MS1/Extra 029y4a source** is the authoritative source for its processor assignments; the physical board and an MS1-specific V3.0 schematic/manual must ultimately be checked.

## Useful shared-board / conceptual references (conditional)

These may assist if the physical unit is confirmed to contain a V3.0 mainboard, **but pin assignments are not yet validated for MS1**:

- **pp. 15–16:** Optional connections and MS3 card stepper outputs. JS0–JS3 are **MS3-specific signals** in this context. **Do not treat their CPU port designations or built-in motor-drive capability as present in MS1.**
- **p. 18:** Published **MS3/V3.0 DB37 pinout** includes O₂ (23), tach (24), idle terminals (25/27/29/31), FIDLE (30), injectors (32–35) and fuel pump (37). This is a useful *candidate connector reference*, not a verified MS1 wiring diagram.
- **pp. 42–44:** Shared-mainboard injection/fuel pump/idle circuit overview; MS3-specific idle drive and modification requirements. MS3's ability to drive a stepper **does not transfer** to the MS1 processor by assumption.
- **pp. 66–69:** General high- vs. low-impedance injector discussion and options (PWM, series resistors, external peak-and-hold). The published component values, output current ratings, and implementation refer to **MS3/V3.0**. Do not prescribe them for this unit without verifying its board and injector wiring.
- **p. 13:** Grounding guidance, including the importance of proper sensor-ground reference for accurate wideband analog signals.

## Main conclusion

**This PDF is secondary background material, not proof of the MS1's particular pins.** Source-derived MS1 I/O is documented in [SOURCE-AUDIT-029Y4A.md](SOURCE-AUDIT-029Y4A.md). Physical board inspection or the correct MS1 V3.0 schematic remains an open step.

No PDF edits or firmware builds were performed.
