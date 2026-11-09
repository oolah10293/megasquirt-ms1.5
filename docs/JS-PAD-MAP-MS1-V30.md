# V3.0 jumper pads JS0–JS11 with original MS1 processor

**Verified 2026-11-08:** Board is the owner's physically photographed **V3.0 mainboard** with an original MS1 MC68HC908GP32 in the DIP-40 socket. The following matches the original MegaSquirt V3.0 CPU schematic (page/sheet 1) to the **uploaded** `029y4a/src/msns-extra.h`, `msns-extra.asm` and `msns-extra.ini`.

**Sources:** Official V3.0 schematic: https://www.megamanual.com/ms2/megasquirt_ShemV3.00.pdf (page 1); V3.0 assembly guide: https://www.megamanual.com/ms2/V3assemble.htm; owner-uploaded ZIP `029y4a.zip` (source file/line refs below).

## Complete physical-to-software map

| Pad | DIP40 pin | MS1 CPU signal | Existing 029y4a use | Practical status for MS1.5 |
| --- | ---: | --- | --- | --- |
| **JS0** | **38** | **PTA5 / X2** | Cooling fan output, water injection and optional tach output | **Candidate digital output** if native fan/water/tach writes are assigned elsewhere or excluded |
| **JS1** | **37** | **PTA4 / X3** | Second water-injection/nitrous output, optional tach output | **Candidate digital output** if optional functions are excluded |
| **JS2** | **36** | **PTA3 / X4** | Output 1 / boost-control PWM | **Owner's existing 2N2222 stage; candidate for single fan-relay circuit** (pending electrical verification) |
| **JS3** | **35** | **PTA2 / X5** | Output 2 | **Owner's other 2N2222 stage; prefer leaving intact and spare** |
| **JS4** | **30** | **PTB7 / AD7 / X6** | Spare **analog input**, EGT | Preserve as analog-capable unless needed, digital output would require firmware/ADC setup changes |
| **JS5** | **29** | **PTB6 / AD6 / X7** | Spare **analog input**, 2nd O₂ / MAP / fuel pressure | Preserve as analog-capable if future sensors are desired |
| **JS6** | **6** | **RST** | MCU reset | **NOT a GPIO; do not use for IAC** |
| **JS7** | **10** | **PTC3 / Pin10** | Shift light, optional spark/other output | **Candidate digital output**, if unused features disabled |
| **JS8** | **11** | **PTC4 / Pin11** | Shift light OR second-trigger input | **Candidate digital output**, unless input/trigger mode required |
| **JS9** | **16** | **PTD1 / MISO** | Nitrous/table switch **input**, normally DDRD input | Only after deliberate DDR/feature changes; **never put +12 V on JS9 with MS1** |
| **JS10** | **17** | **PTD2 / MOSI** | Knock **input**, optional spark-F output | Could repurpose with deliberate direction/feature changes |
| **JS11** | **18** | **PTD3 / SPSCK** | Launch-control **input** | Could repurpose with deliberate direction/feature changes |

**Do not mix MS1 with MS2:** With an MS2 daughtercard, the same physical JS0–JS3 pads serve driver outputs for a four-wire IAC. That does **not** imply any stepper motor driver is built into this MS1 board. On MS1 they are the **PTA5/PTA4/PTA3/PTA2 logic output pins** listed here.

## Independent corroboration from uploaded 029y4a

- `src/msns-extra.h:19–52,62–80` — the original MS1 port functions, including X2/X3/X4/X5, ADC channels, PTC3/PTC4, and PTD1/PTD2/PTD3.
- `msns-extra.ini:670` — optional tach on X2(JS0), X3(JS1), X4(JS2), X5(JS3), etc.
- `msns-extra.ini:1383,1389` — Output 1 (X4/JS2), Output 2 (X5/JS3).
- `msns-extra.ini:2253` — shift light outputs PTC3/4 on JS7/JS8.
- `msns-extra.asm:878–914` — RAM/port initialization: **DDRA all output**, **DDRB all input**; **DDRC PTC3/4 normally output**, but PTC4 becomes input if second-trigger selected. **DDRD PTD1–PTD3 are inputs** in default configuration.
- `msns-extra.asm:4971–5009` — factory firmware's fan control drives **PTA5/JS0** or LED18, not JS2.
- `msns-extra.asm:5060–5100,9270–9360,13255–13296` — other water/nitrous paths write PTA4/JS1 and PTA5/JS0; these need to be disabled or guarded for exclusive STEP/DIR use.
- `msns-extra.asm:3815–3850` — shift light uses PTC3/JS7 and PTC4/JS8.
- `msns-extra.asm:887–896` — PTD2 direction is changed when spark F feature is enabled; PTD1/PTD3 normally inputs.

### Critical safety warning: JS9

The V3.0 assembly guide states that jumpering **S12C → JS9** supplies 12 V **only for MS2 stepper-driver circuitry** and expressly warns that doing so on non-MS2 applications destroys the processor. **Leave JS9 unconnected to 12 V on the owner's MS1.** The original MS1's JS9 is MCU **PTD1/MISO input**, not a 12-V power supply.

## Preferred revised MS1.5 pin proposal (not implemented)

The owner's stated desire is to **reuse one of the two 2N2222 auxiliary circuits for the single cooling fan** and **keep the other as an untouched spare**. Because the V3.0 offers more raw outputs, there is no technical reason at this stage to consume both JS2 and JS3 for stepper commands.

- **Fan:** JS2/PTA3 with existing 2N2222 stage — *proposed pad choice only, not yet electrically validated*; redirect the existing fan routine from PTA5/JS0 or LED18 to PTA3/JS2, and disable competing Output1/boost writes.
- **Spare:** JS3/PTA2 with the other existing 2N2222 stage — leave intact.
- **IAC STEP:** **JS0/PTA5**, proposed first choice.
- **IAC DIR:** **JS1/PTA4**, proposed first choice.
- **Alternates:** **JS7/PTC3 and JS8/PTC4** form another potentially usable pair; LED17/PTC0 and LED19/PTC1 remain further alternatives, but LED functions must be reassigned. **JS4/5 should preferably remain analog inputs** for future measurement needs.
- Configure software to give each selected bit **one writer only**, with safe startup output states. Confirm connector wiring and 5 V logic conditioning to the chosen STEP/DIR driver.
- The proposed fan transistor circuit is for switching a **relay coil**, not automatically the fan motor. Check transistor base current, coil draw and flyback diode.

**Design conclusion:** We do appear to have enough candidate processor I/O to meet the owner's preferred fan + spare output + STEP/DIR arrangement. This is a **pin availability finding**, not proof that stepper firmware timing, RAM, electrical conditioning, or the actual board's modification wiring have been validated. No build, hardware wiring or flashing authorized or performed.
