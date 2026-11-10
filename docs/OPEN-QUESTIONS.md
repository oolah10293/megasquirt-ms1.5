# Open questions and next investigations

**Updated 2026-11-08 after direct firmware source inspection.** Completed checks below are evidenced in [SOURCE-AUDIT-029Y4A.md](SOURCE-AUDIT-029Y4A.md).

## TunerStudio offline GUI smoke test — 2026-11-09

- [x] Owner loaded the custom INI in **TunerStudio MS Lite 3.3.01** and opened the **MegaSquirt MS1.5** project; dashboard displayed **Not Connected** and custom JS0/JS1/JS2/JS3 labels.
- [x] **MS1.5 Stepper IAC** and **MS1.5 Fan Relay (JS2 / PTA3)** dialogs opened and rendered their intended sections/controls.
- [x] **Offline calibration display restored:** after loading a test tune adapted from the original 029y4a `default-degF.msq`, the owner reported IAC **4 ms / 360 closing / 320 max opening** and fan **194°F ON / 145°F OFF**. All five match the expected offline test values. The initially absurd values occurred in a project with no tune loaded; this supports (but does not prove) missing calibration data as the cause.
- [x] The owner closed/reopened TunerStudio and reported the same settings remained visible. The owner also confirmed a separate **Save Tune As → Open Tune (`.msq`)** round-trip succeeded with those settings intact. This was reported by the owner, not independently inspected from the saved file.
- [ ] **Two AFR-unit mismatch warnings** appeared when importing the offline test tune: `afrBins1` and `afrBins2` expected **Volts** in the active narrowband-project configuration but contained **AFR** units in the MSQ. No unit conversion occurred. Select and verify appropriate wideband configuration and preserve tables safely before engine use.
- [ ] Test other TunerStudio settings, protocol/ECU serial read-back and writing on a safe bench; offline GUI success alone does not validate firmware operation.
- [ ] Remove obsolete UI/status remnants (e.g., Launch On, NOS/Tables On, spark gauge) as a separate noncritical cleanup.
- [ ] No serial communication/read/write, physical ECU connection, burn, or on-engine test has been verified; **do not flash current test image**.

See [observations and limits](TUNERSTUDIO-OFFLINE-UI-2026-11-09.md).

## TunerStudio tuning-integrated test assembly — 2026-11-09

- [x] CASM08Z assembled matching new MS1.5 firmware without errors; calibration defaults at `E871–E875` and unique signature verified in S19.
- [x] Verified previous original source baseline byte-for-byte; protected pages and bootloader unchanged, vector relocation valid, main code ends `DBEF`.
- [x] Initial TunerStudio **project and two-dialog rendering** smoke test passed offline; see [UI observations](TUNERSTUDIO-OFFLINE-UI-2026-11-09.md).
- [x] **Selected offline calibration values and separate MSQ save/reopen round-trip** confirmed by owner report: 4, 360, 320, 194°F, 145°F.
- [ ] **Remaining dialogs, AFR unit handling and actual ECU serial read/write** still require validation; don't confuse offline GUI results with ECU compatibility.
- [ ] Bench RPM/injector timing and motor/relay electrical protection; **do not flash or use current test image on vehicle**.

## Historical tuning source draft — 2026-11-09

- [x] Custom 32-character firmware/INI matching signature and future test-version string drafted. **Requires a NEW build**; previously passing S19 has old signature.
- [x] Draft new page-9 IAC motor parameters: low interval, startup homing count and maximum step travel; source/INI offsets 113..117 verified free.
- [x] Preserve idle algorithm tuning, redefine old PWM `idlefreq` byte as current source's demand cap, and relabel position/idle-control fields. Separate fan JS2 dialog and hide conflicting old output menus.
- [x] CRLF INI/source addendum patch dry-run checks completed against original 029y4a; static offset checks passed.
- [x] INI loaded and the IAC and fan dialogs rendered in TunerStudio MS Lite; see [offline GUI observations](TUNERSTUDIO-OFFLINE-UI-2026-11-09.md).
- [x] Loading the adapted offline 029y4a test tune resolved the reported nonsense values for the five checked settings; separate tune file save/load also succeeded per owner.
- [ ] Resolve the two AFR unit-mismatch warnings; test other existing-tune migration and hidden legacy feature bits.
- [x] Owner separately authorized **the tuned test build**, which passed using CASM08Z (signature, CAL page and flash checks). **Runtime timing remains untested.** See [tuning build report](TEST-BUILD-TUNING-2026-11-09.md).

See [the source-only tuning record](TUNERSTUDIO-WIP-2026-11-09.md).

## Windows test build completed — 2026-11-09

- [x] **Original 029y4a baseline and MS1.5 source both assembled with CASM08Z v3.14, no errors.** See [test report](TEST-BUILD-2026-11-09.md).
- [x] Verify byte-for-byte baseline with shipped S19 and unchanged bootloader/calibration pages; 17 relocated interrupt vectors valid, net code growth **47 bytes**, **1,098** remaining address slots before DFFF.
- [ ] Actual bench injector/timer jitter and stack high-water validation; verify fan coil and IAC electrical safety, travel and fault recovery.
- [ ] Update the TunerStudio INI, firmware signature and idle-position tuning semantics before flashing to hardware.

## Latest source work — 2026-11-08

- [x] Write original, **unbuilt** MS1.5 stepper assembly routine, direct-page variable aliases and 029y4a integration patch; [source work record](FIRMWARE-WIP-2026-11-08.md).
- [x] Source-only check: JS0/JS1 have exclusive motor writers after integration patch; JS2 has only the fan on/off writes; JS3 is not reassigned.
- [x] Source-only check: all eight aliased RAM state bytes are within direct page (including correction: `n2ohold` **is not**, at 0x010C), no new DS allocations, and simple new routine branch-span estimate passed.
- [x] The committed CRLF-native patch was confirmed byte-for-byte identical to the locally dry-run patch against the actual user-uploaded original source.
- [ ] Update and validate tuning INI, signature, invalid-feature handling, idle units and serial diagnostics before any live use.
- [ ] Confirm IAC valve coil wiring, driver power/enable/reset circuitry, allowable motor travel and position direction; current **320/360 steps** are unverified bench placeholders.
- [ ] Establish actual fan relay current/base drive/flyback diode suitability with the owner-built 2N2222 circuit.
- [ ] **Only after explicit build authorization:** assemble, review ROM/stack/timer maps, and bench test with injector/tach/serial/fan activity. No build yet.

The older discussion below includes superseded pin-allocation proposals; the [current pin map](IO-ALLOCATION-MS1-V30.md) and [source implementation log](FIRMWARE-WIP-2026-11-08.md) control.

## Initial source identification / feature audit

- [x] Inspect the uploaded **MS1/Extra 029y4a** assembly source, MCU header and tuning INI.
- [x] Identify existing fan logic and its MCU pins.
- [x] Identify existing PWM idle control logic and actuator output.
- [x] Identify existing 8x8 AFR-target lookup and EGO correction logic.
- [x] Identify existing 12x12 fuel VE tables and serial/tuning definitions.
- [x] Classify supplied MS3/V3.0 PDF as **not authoritative for MS1 CPU/stepper capabilities**.
- [ ] Check whether this 029y4a baseline matches the firmware on the physical ECU; otherwise choose and document a replacement baseline.
- [ ] Establish source licensing and appropriate attribution before adding third-party firmware source files to this public repository.

## Complete JS-pad verification and current I/O proposal

- [x] [Map JS0–JS11](JS-PAD-MAP-MS1-V30.md) to the MS1 MCU using physical V3.0 schematic and owner-uploaded 029y4a source.
- [x] Confirm **JS0/PTA5 and JS1/PTA4 are digital outputs**, and **JS7/PTC3 and JS8/PTC4** are other output candidates. JS4/JS5 are analog-capable; JS6 is reset; JS9-11 generally inputs by default.
- [x] Update candidate plan to **JS0=IAC STEP, JS1=IAC DIR, JS2=fan via one existing 2N2222, JS3=untouched spare** (fan pad choice remains provisional).
- [ ] Select JS0/JS1 versus JS7/JS8 from detailed firmware write-path and external routing analysis.
- [ ] Gate legacy water/nitrous/fan/tach writers to JS0/JS1; remap fan logic to JS2 or JS3.
- [ ] Verify physical driver interface and actual fan relay current/flyback protection; confirm target IAC valve electrical characteristics.

### Historical earlier preferred I/O partition (superseded)

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

**Current:** MS1.5 signature and TunerStudio tuning source draft is committed, but has **not** been reassembled, connected to TunerStudio, or bench-tested. Next review a representative tune, verify physical IAC/relay wiring, and request explicit new test-build authorization before compiling the changes. See [tuning draft](TUNERSTUDIO-WIP-2026-11-09.md).
