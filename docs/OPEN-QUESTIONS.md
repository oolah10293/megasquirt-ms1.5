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

## Firmware/board feasibility — work left to do

- [ ] Obtain **MS1-specific** PCB/connector/schematic references and confirm board revision.
- [ ] Trace physical output modifications already made; locate existing fan output (only one needed).
- [x] Draft **logical candidates** PTC0/LED17=STEP and PTC1/LED19=DIR; optional FIDLE=driver enable, preserve one fan; **owner-confirmed JS2/JS3 outputs are unused and candidates for IAC reuse**. **Proposal only**: see [I/O allocation](IO-ALLOCATION-MS1-V30.md).
- [ ] Verify these CPU outputs' physical routes through driver/connector circuits; ensure no remaining LED/ignition writes interfere.
- [ ] Determine a feasible IAC stepper driver interface from the actual valve's electrical requirements.
- [x] Identify the 100 µs TIM2 timebase and existing **1 ms MSEC** service as the candidate IAC state-machine insertion point; see [firmware design](IAC-STEPPER-DESIGN.md).
- [ ] Determine real worst-case execution time and injector jitter once a separate **test build is explicitly authorized**; static sources alone cannot prove this.
- [x] Calculate **current source-defined RAM layout** (210 application bytes + 200 calibration buffer + 19-address pre-stack gap) and **distributed S19** main-code limit (1,145-address gap). See [static resource budget](MS1-RESOURCE-BUDGET.md).
- [ ] Establish actual reusable RAM/stack high-water and assembled flash growth; historical `mem_map.txt` is for **029h**, not 029y4a.
- [ ] Plan any protocol, INI, and diagnostics extensions only when resource costs are known.

## Physical specifics (confirm only what code/schematics cannot establish)

- [x] Confirm mainboard revision: physical photo shows **MegaSquirt V3.0 MB** and socketed MS1 processor, **no daughtercard**. See [board photo review](BOARD-PHOTO-2026-11-08.md).
- [x] Owner confirms the **two custom output circuits connect to JS2 and JS3 and are unused**; underside photograph supplied (see [board photo review](BOARD-PHOTO-2026-11-08.md)).
- [ ] Identify the **CPU/control source**, electrical polarity, and connector routing of the **unused** JS2/JS3 output circuits; determine whether to bypass/rework them for IAC STEP/DIR. Confirm the **one fan output separately**; do not assume it uses these unused circuits.
- [ ] Available tach/RPM signal from ignition equipment (MS1 ignition-output control is not needed).
- [ ] Target GM 4.3 TBI injectors' impedance; confirm existing resistor value/wattage and intended use.
- [ ] GM stepper IAC pinout, coil impedance/current, compatible driver topology.
- [ ] Wideband O₂ controller model and calibrated analog output transfer function.

## Later development/test tasks — NOT yet authorized to build

- [x] Draft source-located, **unimplemented** STEP/DIR state-machine design using existing idle algorithm and 1 ms service; see [IAC firmware design](IAC-STEPPER-DESIGN.md).
- [ ] Validate every original LED/spark/fault write to PTC0 and PTC1 before claiming exclusive control.
- [ ] Develop bounded position tracking/homing, startup and idle-error behavior.
- [ ] Design validated wideband scaling, sensor-invalid fallback and corrections; **start from existing** 029y4a code.
- [ ] Preserve one cooling-fan output and TBI injector timing.
- [ ] Add needed tuning/status fields with protocol compatibility review.
- [ ] Define bench simulator, test matrix and rollback plan before any physical flash.

## Immediate next engineering task

**The initial I/O allocation, stepper firmware concept, and static memory budget are drafted and linked above.** Next verify remaining physical signal routing and the source call paths that write PTC0/PTC1, then estimate the exact step service instruction cost. Actual fit/jitter requires an **explicitly authorized test build and subsequent bench measurement**.
