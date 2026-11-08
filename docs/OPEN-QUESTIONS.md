# Open questions and next investigations

The questions below are **research tasks**, not a request that the owner repeat things a source-code/schematic audit can establish.

## Source and board: investigate first

- [ ] Identify and retrieve the source for the exact candidate MS1 firmware baseline.
- [ ] Determine what fuel/AFR/idle/fan features already exist; avoid duplicating proven code.
- [ ] Map the processor ports, external pins and original circuitry from source and schematics.
- [ ] Identify which outputs can actually be repurposed when no spark is controlled.
- [ ] Verify RAM/flash headroom and real-time constraints for stepper updates and feedback.
- [ ] Determine whether tuning protocol/definition updates are needed.

## Physical details to confirm when necessary

- [ ] PCB revision and any hardware modifications already made to this MS1.
- [ ] Existing fan-output location and transistor/relay circuit.
- [ ] Intended GM TBI injector type/impedance and existing resistor values/application.
- [ ] Exact IAC stepper/connector and required driver electrical behavior.
- [ ] Wideband sensor/controller selection and controller analog-output calibration.
- [ ] Existing ignition source and available RPM signal (not asking MS1 to control ignition).

## Candidate implementation tests (future; not authorized to build)

- [ ] Design and review external stepper-driver circuit after electrical verification.
- [ ] Prototype idle target/position algorithm, homing and safeguards in a test environment.
- [ ] Prototype AFR-target control with sensor-valid gating and bounded trims.
- [ ] Verify one fan output and TBI injection still work under the final pin allocation.
- [ ] Design diagnostic/serial fields and tuning screens only after resource audit.
- [ ] Plan bench validation and rollback path **before any ECU flash**.

## Current next step

**Read actual firmware source and schematics; produce a verified pin/timing/feature inventory.** No compile, flashing, hardware rewiring or release is part of this documentation task.
