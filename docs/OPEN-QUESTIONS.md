# Open questions and next investigations

**Updated 2026-11-08 after direct firmware source inspection.** Completed checks below are evidenced in [SOURCE-AUDIT-029Y4A.md](SOURCE-AUDIT-029Y4A.md).

## Initial source identification / feature audit

- [x] Inspect the uploaded **MS1/Extra 029y4a** assembly source, MCU header and tuning INI.
- [x] Identify existing fan logic and its MCU pins.
- [x] Identify existing PWM idle control logic and actuator output.
- [x] Identify existing 8x8 AFR-target lookup and EGO correction logic.
- [x] Identify existing 12x12 fuel VE tables and serial/tuning definitions.
- [x] Classify supplied MS3/V3.0 PDF as **not authoritative for MS1 CPU/stepper capabilities**.
- [ ] Check whether this 029y4a baseline matches the firmware on the physical ECU; otherwise choose and document a replacement baseline.
- [ ] Establish source licensing and appropriate attribution before adding third-party firmware source files to this public repository.

## Current preferred I/O partition (updated by owner, November 8, 2026)

- [x] Owner wants **one existing 2N2222 stage retained for fan relay**, and the other left intact where possible.
- [x] Preferred provisional pin allocation: **fan=JS2/PTA3** (choice of stage still reversible), **JS3/PTA2 spare**, **IAC STEP=LED17/PTC0**, **IAC DIR=LED19/PTC1**.
- [ ] Verify fan relay coil current, transistor base drive, supply and clamp/flyback protection; **don't assume 2N2222 switches a motor load**.
- [ ] Reassign native fan routine from X2/PTA5 or LED18/PTC2 to the selected JS2 or JS3 output; audit conflicting Output 1/boost or Output 2 code.
- [ ] Audit all LED17/LED19 squirt/acceleration/ignition/stall writes before granting PTC0/PTC1 to STEP/DIR, and verify real external logic routing.
- [ ] Confirm whether physical wiring makes JS3 preferable for fan; leave the other 2N2222 stage untouched.

**Prior JS2=STEP/JS3=DIR checklist findings below are historical and superseded by this preference.**

## Firmware/board feasibility — work left to do

- [ ] Obtain **MS1-specific** PCB/connector/schematic references and confirm board revision.
- [ ] Trace physical output modifications already made; locate existing fan output (only one needed).
- [x] **Verified actual V3.0 pad-to-CPU mapping:** **JS2→PTA3/X4/Output 1**; **JS3→PTA2/X5/Output 2** (official schematic, supplied 029y4a header and `msns-extra.ini:1383,1389`). Owner confirms both custom circuits unused. **Preferred allocation is now JS2=STEP, JS3=DIR**, with electrical stages to be validated. See [I/O allocation](IO-ALLOCATION-MS1-V30.md).
- [x] Owner identified **2N2222 NPNs** and **gold–red–black–brown resistors** (nominally **1 kΩ ±5%**) in the two unused JS2/JS3 driver stages.
- [ ] Verify the **2N2222 emitter/base/collector connections**, resistor placement, output polarity, external conductor/connector routing, and compatible STEP/DIR logic levels; eliminate competing **Output 1/Output 2/boost** writes. The original MCU socket-to-JS-pad mapping is already established.
- [ ] Determine a feasible IAC stepper driver interface from the actual valve's electrical requirements.
- [x] Identify the 100 µs TIM2 timebase and existing **1 ms MSEC** service as the candidate IAC state-machine insertion point; see [firmware design](IAC-STEPPER-DESIGN.md).
- [ ] Determine real worst-case execution time and injector jitter once a separate **test build is explicitly authorized**; static sources alone cannot prove this.
- [x] Calculate **current source-defined RAM layout** (210 application bytes + 200 calibration buffer + 19-address pre-stack gap) and **distributed S19** main-code limit (1,145-address gap). See [static resource budget](MS1-RESOURCE-BUDGET.md).
- [ ] Establish actual reusable RAM/stack high-water and assembled flash growth; historical `mem_map.txt` is for **029h**, not 029y4a.
- [ ] Plan any protocol, INI, and diagnostics extensions only when resource costs are known.

## Physical specifics (confirm only what code/schematics cannot establish)

- [x] Confirm mainboard revision: physical photo shows **MegaSquirt V3.0 MB** and socketed MS1 processor, **no daughtercard**. See [board photo review](BOARD-PHOTO-2026-11-08.md).
- [x] Owner confirms the **two custom output circuits connect to JS2 and JS3 and are unused**; underside photograph supplied (see [board photo review](BOARD-PHOTO-2026-11-08.md)).
- [x] **Determine CPU/control source** of unused JS2/JS3: PTA3 and PTA2 respectively. Source and INI confirm X4 Output 1 and X5 Output 2.
- [ ] Verify the existing **output-stage** electrical polarity/levels, motor-driver compatibility, and downstream DB37/harness route; choose bypass/rework as needed. Confirm **one fan output separately**.
- [ ] Available tach/RPM signal from ignition equipment (MS1 ignition-output control is not needed).
- [ ] Target GM 4.3 TBI injectors' impedance; confirm existing resistor value/wattage and intended use.
- [ ] GM stepper IAC pinout, coil impedance/current, compatible driver topology.
- [ ] Wideband O₂ controller model and calibrated analog output transfer function.

## Later development/test tasks — NOT yet authorized to build

- [x] Draft source-located, **unimplemented** STEP/DIR state-machine design using existing idle algorithm and 1 ms service; see [IAC firmware design](IAC-STEPPER-DESIGN.md).
- [ ] Audit and disable/rework every original **Output 1, Output 2 and boost-control write** to PTA3/PTA2 before allocating them exclusively to IAC STEP/DIR. Only audit PTC0/PTC1 LED/spark writers if these fallback pins become necessary.
- [ ] Develop bounded position tracking/homing, startup and idle-error behavior.
- [ ] Design validated wideband scaling, sensor-invalid fallback and corrections; **start from existing** 029y4a code.
- [ ] Preserve one cooling-fan output and TBI injector timing.
- [ ] Add needed tuning/status fields with protocol compatibility review.
- [ ] Define bench simulator, test matrix and rollback plan before any physical flash.

## Immediate next engineering task

**The exact JS2/JS3 processor mapping is established**, and the preferred STEP/DIR assignment now uses these unused outputs directly. Next verify added transistor/output electrical behavior and external connector routing; isolate PTA3/PTA2 from legacy output/boost code and estimate step service cycles. Actual fit/jitter requires an **explicitly authorized test build and subsequent bench measurement**.
