# MegaSquirt MS1.5

> **LATEST verified final fuel-only build (Nov 10 local / Nov 11 UTC, 2026):** [Windows CASM08Z run 42946540078](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42946540078) passed at assembly commit `6c1621e7`, from final source-only dev checkpoint `91c1defd`. Five upstream tests, nine integrated cleanup tests, both source/tuning checkers and CASM08Z original/final assemblies passed. Actual S19 checksum/vector and bootloader comparisons passed; matching final INI verified. See [final build/hashes/checklist](docs/FUEL-ONLY-FINAL-BUILD-2026-11-10.md). **BENCH IMAGE ONLY: NO FLASH, VEHICLE VALIDATION OR RELEASE.** Older S19 images below are superseded.


> **FINAL source-only fuel cleanup verification (November 10 local / November 11 UTC, 2026):** [Integrated source-only CI run 42944883755](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42944883755) PASS, **9 regression tests**, source/tuning checks, and exact allowance of six harmless historical ignition/racing-named runtime instructions. Additional fixes include clearing a stale VE3 table-selection flag, removing dead dwell aliases, preserving extra cranking fuel under a fuel-specific alias, and retiring incorrect spark/nitrous help. [Current authoritative handoff](docs/CURRENT-HANDOFF.md). **SOURCE ONLY — NO NEW BUILD, NO RELEASE, NO FLASH.** Historical S19 files predate this revision.


> **CURRENT source-only fuel cleanup checkpoint (2026-11-10):** The user requested removal of obsolete spark/launch/nitrous/knock/boost output paths while preserving all useful 029y4a fuel, AFR and closed-loop idle functionality. [Full integrated source-only CI run 42932812680](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42932812680) passed on source commit `d649aa297bd6c419ec5aa994a361b3bce25e9b82` with all three real integration patches, six regression tests, and existing source/tuning checkers. [Read final source cleanup and limits](docs/FUEL-ONLY-SOURCE-CLEANUP-2026-11-10.md). **SOURCE-VERIFIED ONLY: NOT ASSEMBLED, NOT FLASHED, NOT ENGINE-READY.** The older successful CASM08Z bench S19 below predates this cleanup and must not be mistaken for the current firmware. NO build, release or flash permission exists for this checkpoint.

> **NEWER fuel-only build checkpoint (2026-11-10):** The owner authorized building the dedicated **029y4a-based fuel-only** test firmware, preserving the original **12x12 VE, AFR targets and closed-loop fuel/idle**, and our STEP/DIR IAC and single fan. GitHub [CASM08Z run 42921957431](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42921957431) passed on commit `3e8e80e2`. Spark/dwell logic and ignition-configuration error path were removed, and paired S19/INI artifacts were produced for **bench investigation only**. **NOT FLASHED / NOT STIM-VALIDATED / NOT ENGINE-READY.** Read [the full build audit](docs/FUEL-ONLY-BUILD-2026-11-10.md). Older status paragraphs below describe earlier snapshots.

> **Active fuel-only source cleanup (2026-11-10, development branch):** The current goal is to **physically remove ignition-exclusive firmware**, not override `personality` at runtime. See [the source-verified ignition-removal audit](docs/IGNITION-REMOVAL-2026-11-10.md) and [current handoff](docs/CURRENT-HANDOFF.md). Stage one has a committed source transformation and original-source regression tests; it deletes the spark lookup and ignition-mode validation but **does not yet remove ignition ISR/output code**. This work is **unbuilt and not flashable**. The previous RAM-fix S19/INI are unmodified, verified existing artifacts. No new build/flash authorization exists.


> **Current handoff (2026-11-10):** Read [active engineering handoff](docs/CURRENT-HANDOFF.md) **before further changes**. It records the current Git checkpoints, the unresolved fuel-only spark-configuration restriction, the interrupted Work task, and the required incremental source-control workflow. Later owner-reported Stim testing is not yet fully reflected in the older status paragraphs below. No firmware change or build is authorized by this note.

Modernizing an existing **MegaSquirt MS1** to run a **GM 4.3L V6 with throttle-body injection (TBI)**, focusing on better idle control, useful wideband O₂ feedback, and a better tuning experience.

**Current checkpoint (2026-11-10):** The supplied screenshot shows TunerStudio online with the signature-corrected firmware and live gauges; the owner’s loader output reports 12.12 V. During subsequent closed-loop-only Stim testing, the owner reported JS0 pulsing continuously for approximately five minutes without seeing JS1 change. Source inspection found the ADC-history indexed store overwriting five stepper-state bytes. The integration patch now removes that obsolete copy while retaining ADC smoothing. Source checks pass and reject deliberate reintroductions of the conflicting write. **The owner authorized the build; CASM08Z assembly and image checks passed.** The corrected `MS15_2026-11-10.s19` and matching INI have been delivered. Flashing and Stim verification of this correction remain outstanding; the previously flashed image still contains the conflict. See [RAM ownership correction and next bench check](docs/IAC-RAM-OWNERSHIP-2026-11-10.md) and [signature correction and bench evidence](docs/SIGNATURE-COMPATIBILITY-2026-11-09.md).

**Existing test build:** The [tuning-integrated assembly report](docs/TEST-BUILD-TUNING-2026-11-09.md) records passing assembly/static checks for the custom 029y4a-based MS1.5 image. The [offline UI record](docs/TUNERSTUDIO-OFFLINE-UI-2026-11-09.md) records owner-reported custom-field and tune-file round-trip success. These do not establish live MS1.5 read/write/burn or safe runtime behavior. Resolution of the previously recorded AFR unit warnings was not recovered. **TEST ONLY — NOT ENGINE-READY.** Older “not authorized to flash” status notes predate the owner's later bench-flash go-ahead; engineering validation remains outstanding.

## Confirmed project requirements

These items come directly from the project owner's discussion on November 8, 2026:

- **Engine/application:** GM 4.3L TBI.
- **Controller:** Reuse the existing MegaSquirt MS1 if technically feasible.
- **Fueling:** Control the engine's TBI injection.
- **Ignition:** The MS1 **will not control spark** on this engine. Do not reserve ignition outputs without a reason.
- **Idle air:** Add active IAC control. The earlier MS1 installation was run without an IAC.
- **IAC architecture preference:** Keep the idle-control intelligence in the MS1 firmware; use an **external motor driver**, not a second ECU, if feasible.
- **Oxygen sensor:** Add wideband O₂-based AFR control.
- **Cooling fan:** **Exactly one fan-control output is needed.**
- **Resistors:** The owner already has resistors. Their intended application and values have **not yet been confirmed**.
- **Tuning:** Improve the available tuning and diagnostics compared with the old MS1 experience.

## Intended features (design goals, not implemented features)

1. Closed-loop idle-speed control using a stepper IAC and suitable external driver.
2. Tunable startup, warm-up, idle-target, dashpot and idle-recovery behavior.
3. Wideband-calibrated AFR readings and AFR-target-based closed-loop fuel correction.
4. Usable fuel/AFR tables, diagnostics and datalogging; reuse existing tuning protocols/tools where practical.
5. Preserve one cooling-fan control output and the injection functions.
6. Retain reliable fuel-control timing as the highest priority.

**Source-audit update (2026-11-08):** MS1/Extra 029y4a **already implements** fan control with separate on/off coolant thresholds, two 8×8 AFR-target tables with EGO fuel correction, and PWM closed-loop idle targeting with warm-up, dashpot and recovery. The missing major feature is **stepper-actuator output/control**, not the entirety of idle or AFR logic. These findings apply to the uploaded historical firmware, **not automatically to the owner-reported 029t installed in the physical ECU**. Real-time timing, flash/RAM, and board I/O feasibility remain unverified.

## Architecture preference

```text
 GM engine sensors ───────> MegaSquirt MS1 ──────> TBI injector outputs
        │                        │
        └─ RPM/TPS/CLT/etc.      ├───────────────> One cooling-fan output
                                 └─ IAC command ─> External stepper driver ─> IAC

 Wideband O₂ sensor ─> Wideband controller ─> Calibrated analog signal ─> MS1

 Ignition timing: managed outside the MS1 in this application.
```

The diagram is **conceptual**. Output assignments, driver interface, and signal availability are not yet validated.

## Firmware development — sources and existing test builds

- [Current WIP assembly stepper state machine](firmware/ms15_iac.inc)
- [WIP RAM alias map and temporary motor-travel constants](firmware/ms15_defs.inc)
- [Source integration patch for original 029y4a](patches/ms15-on-029y4a-wip.patch)
- [Firmware implementation record, source-only checks and blockers](docs/FIRMWARE-WIP-2026-11-08.md)
- [Passing Windows CASM08Z test build and remaining bench validation requirements](docs/TEST-BUILD-2026-11-09.md)
- [Repeatable non-building source checks](tools/check_ms15_source.py)
- [TunerStudio INI customization patch](patches/ms15-tuning-ini.patch)
- [Matching firmware signature and page-9 calibration patch](patches/ms15-tuning-firmware-addendum.patch)
- [Non-building tuning source/INI consistency checker](tools/check_ms15_tuning.py)
- [Tuning controls, offsets and limitations](docs/TUNERSTUDIO-WIP-2026-11-09.md)
- [Passing tuning-integrated CASM08Z test assembly, flash mapping, and verification](docs/TEST-BUILD-TUNING-2026-11-09.md)

## Project documents

- [Requirements and design decisions](docs/PROJECT-SPEC.md)
- [Research status and verification needs](docs/RESEARCH-NOTES.md)
- [Verified MS1/Extra 029y4a source audit with line references](docs/SOURCE-AUDIT-029Y4A.md)
- [Stepper IAC timing and memory feasibility plan](docs/STEPPER-FEASIBILITY-PLAN.md)
- [Current proposed MS1/V3.0 pin and output allocation](docs/IO-ALLOCATION-MS1-V30.md)
- [Complete MS1 V3.0 JS0–JS11 pin map](docs/JS-PAD-MAP-MS1-V30.md)
- [IAC STEP/DIR driver and firmware design](docs/IAC-STEPPER-DESIGN.md)
- [Source-measured RAM, flash and prospective CPU budget](docs/MS1-RESOURCE-BUDGET.md)
- [Scope warning for uploaded MS3/V3.0 hardware manual](docs/HARDWARE-MANUAL-SCOPE.md)
- [Actual MS1 V3.0 board photo identification](docs/BOARD-PHOTO-2026-11-08.md)
- [Open questions / investigation checklist](docs/OPEN-QUESTIONS.md)

## Engineering ground rules

- **Do not guess hardware revisions, connector pins, spare I/O, firmware variants, or electrical limits.** Verify them from the physical board, schematics, and source.
- **Do not confuse past installations with this engine.** Earlier MegaSquirt/Magnum/EDIS history does not establish the wiring of the GM 4.3 TBI project.
- **No build, installer, firmware release, or flash without explicit authorization.** Discussing or approving a design does not authorize a build.
- Bench-test injection, idle actuator, error handling and reset behavior before any on-engine use.
- Keep project facts, proposed designs, and unverified assumptions distinguishable in the repository.

*Initial planning notes: November 8, 2026.*
