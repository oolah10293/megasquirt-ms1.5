# MS1.5 I/O allocation — CURRENT working design

**Updated 2026-11-08.** This replaces historical pin-allocation proposals in this document. This is a **source-verified processor map** plus **a provisional engineering proposal**, not installed wiring or implemented firmware. No build/flash performed.

**Full verified JS-pad map:** [JS-PAD-MAP-MS1-V30.md](JS-PAD-MAP-MS1-V30.md). Source evidence: owner's `029y4a.zip` and [V3.0 schematic, sheet 1](https://www.megamanual.com/ms2/megasquirt_ShemV3.00.pdf).

## Owner-confirmed requirements

- GM 4.3 TBI, original MS1 processor on physical V3.0 mainboard.
- **No spark control by MS1**, but RPM/tach input is still required.
- Keep exactly **one cooling-fan output**.
- Reuse **one existing JS2 or JS3 2N2222 + nominal 1 kΩ switching stage** for that fan, and preferably **leave the other stage intact and spare**.
- External stepper driver for IAC controlled by MS1 firmware, with STEP/DIR if compatible.
- Retain injection, fuel pump, wideband O₂ and tuning functions.
- Installed firmware version, current physical loads and downstream wiring remain unverified.

## Preferred logical allocation (proposed, NOT yet owner-selected final pins)

| Function | Proposed MS1 signal | Evidence / conditions |
| --- | --- | --- |
| IAC **STEP** | **JS0 = PTA5 = X2 = DIP pin 38** | Verified digital output; remove/disable legacy water injection, stock X2 fan and tach-output writers |
| IAC **DIR** | **JS1 = PTA4 = X3 = DIP pin 37** | Verified digital output; remove/disable second water/nitrous injector and tach-output writers |
| **Fan relay** | **JS2 = PTA3 = X4 = DIP pin 36** with existing 2N2222 | Owner wants one existing transistor circuit retained for fan; **JS2 vs JS3 choice is only a proposal**; remap fan from X2/LED18 and disable Output1/boost writes |
| Spare switch | **JS3 = PTA2 = X5 = DIP pin 35** with other 2N2222 | Leave intact if JS2 is assigned fan |
| Injectors 1/2 | PTD4/PTD5 | Preserve original injector timing/current protection |
| Fuel pump | PTA0 | Preserve |
| Tach/RPM input | Existing tach interrupt/input hardware | Preserve; MS1 fuel-only does not eliminate need for tach |
| Wideband O₂ | PTB5/AD5 via wideband controller | Preserve/calibrate |
| Optional driver enable | FIDLE/PTA1 | Only if needed; verify output circuit and firmware owners |

**Directly verified:** `029y4a/src/msns-extra.h:19-80` and `msns-extra.ini:670,1383,1389`. Firmware initialization at `msns-extra.asm:898-900` sets all PTA pins as outputs. **Design choice:** repurposing JS0/JS1 for STEP/DIR. Whether the added fan transistor circuitry safely drives the actual relay coil still requires electrical verification.

### Other straightforward options if JS0/JS1 prove inconvenient

- **JS7 = PTC3 / DIP pin 10** and **JS8 = PTC4 / DIP pin 11**: both normally outputs; traditionally shift-light outputs, and JS8 can become second-trigger **input**. Their firmware owners/configuration must be cleared.
- LED17/PTC0 and LED19/PTC1: legitimate outputs but already used by Squirt/Accel LEDs and optional spark; additional routing and writer cleanup needed.
- **JS4/JS5** are AD7/AD6 analog-capable input pins: preserve for future second O₂ / pressure / EGT if possible, rather than automatically consuming them as outputs.
- **JS9–JS11** map to PTD1–PTD3, normally configured as **inputs** for nitrous/table switch, knock and launch; repurposing them requires deliberate DDR and feature changes. **JS9 has a specific 12-V damage hazard on MS1.**
- **JS6 is MCU RESET**: not available for IAC.

## Why JS0/JS1 currently beat LED17/LED19

JS0 and JS1 are raw, independent processor output pads already intended as accessible jumper points on the V3.0. The existing 029y4a firmware makes them digital outputs; the intended GM 4.3 application does not require their old water/nitrous functions. Their suitable DB37 routing, level conditioning and exclusive firmware ownership still need planning. **Using JS0/JS1 is a new candidate design, not yet approved as final.**

JS7/JS8 might be equally good if source call-path or external routing review favors them. The right choice is the pair with the fewest conflicting writes and simplest safe wiring. **No reason to sacrifice the unused JS3 2N2222 just to find enough IAC signals.**

## Mandatory source changes before future build authorization

1. Retarget existing fan on/off/hysteresis/cranking-off logic from `PTA5/JS0` or `LED18/PTC2` to whichever *retained* transistor output controls the fan (proposed `PTA3/JS2`). Stock 029y4a **does not natively run its fan routine on JS2**.
2. Give PTA5/JS0 and PTA4/JS1 **exclusive IAC ownership**. The existing fan, water-injection/nitrous and optional tach-output routines write these bits (`msns-extra.asm:4971-5009,5060+,9270+,10979-11000,13275+`). Gate or remove conflicting writes.
3. Disable generic Output1/boost code on PTA3 if JS2 is assigned to the fan, and define safe reset polarity for the 2N2222 stage.
4. Determine motor driver's STEP/DIR logic voltage, required pull-ups/pull-downs, default enable behavior and actual valve current/coil configuration.
5. Confirm how logic signals exit via connector/harness; no external pinout or relay current rating has yet been proven from owner photos.
6. Validate available RAM, flash and real-time injection timing by separate explicitly authorized compile/bench tests.

## Historical decisions

- Earlier proposal: JS2/JS3 for STEP/DIR, later replaced when the owner preferred keeping transistor stages for fan/spare.
- Second proposal: LED17/PTC0 and LED19/PTC1 for STEP/DIR. These remain alternatives, **not preferred** after confirming JS0/JS1 and JS7/JS8 availability.
- User never authorized a firmware build by asking for design, research or GitHub documentation.
