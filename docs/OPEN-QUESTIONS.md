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
- [ ] Identify candidate freed ignition/generic outputs and their availability at case connector pins with correct signal protection.
- [ ] Determine a feasible IAC stepper driver interface from the actual valve's electrical requirements.
- [ ] Audit timing/interrupt scheduling for injection, RPM capture, idle movement and serial updates.
- [ ] Establish real RAM/flash allocation/headroom from correct source/link map; provided `mem_map.txt` says **029h**, not 029y4a.
- [ ] Plan any protocol, INI, and diagnostics extensions only when resource costs are known.

## Physical specifics (confirm only what code/schematics cannot establish)

- [x] Confirm mainboard revision: physical photo shows **MegaSquirt V3.0 MB** and socketed MS1 processor, **no daughtercard**. See [board photo review](BOARD-PHOTO-2026-11-08.md).
- [x] Owner confirms the **two custom output circuits connect to JS2 and JS3**; underside photograph supplied (see [board photo review](BOARD-PHOTO-2026-11-08.md)).
- [ ] Identify the **CPU/control source**, driver circuitry and external load/connector destination of each JS2/JS3 custom output; determine which one is used for the single required fan, if either.
- [ ] Available tach/RPM signal from ignition equipment (MS1 ignition-output control is not needed).
- [ ] Target GM 4.3 TBI injectors' impedance; confirm existing resistor value/wattage and intended use.
- [ ] GM stepper IAC pinout, coil impedance/current, compatible driver topology.
- [ ] Wideband O₂ controller model and calibrated analog output transfer function.

## Later development/test tasks — NOT yet authorized to build

- [ ] Produce a source-level, auditable stepper-output design reusing appropriate idle-control routines.
- [ ] Develop bounded position tracking/homing, startup and idle-error behavior.
- [ ] Design validated wideband scaling, sensor-invalid fallback and corrections; **start from existing** 029y4a code.
- [ ] Preserve one cooling-fan output and TBI injector timing.
- [ ] Add needed tuning/status fields with protocol compatibility review.
- [ ] Define bench simulator, test matrix and rollback plan before any physical flash.

## Immediate next engineering task

**Verify the physical MS1 board and output modifications, then perform a detailed I/O + real-time timing feasibility audit against the 029y4a baseline.** The source package is now available and inspected; do not ask the owner to speculate about features the code already establishes.
