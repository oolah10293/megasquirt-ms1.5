# Fuel-only MS1.5 bench-test assembly — 2026-11-10

**Status: ASSEMBLED and STATIC-CHECKED; not flashed, not tested on Stim, NOT ENGINE-VALIDATED.**
**Explicit owner authorization:** 2026-11-10, to *build* a dedicated fuel-only firmware using 029y4a's advanced fuel features; no authority to flash or publish a release.

## Source and exact build

- Base: independently SHA-matched original MS1/Extra 029y4a ZIP, with 3 existing MS1.5 integration / tuning patches. Original B&G 2.986 fuel-only source was reviewed as architecture reference; the modern feature-rich **029y4a remains the implementation basis**, not B&G.
- Source-only dev: `ms15-ignition-removal` branch, `tools/remove_ms15_ignition_full.py`, `tools/simplify_ms15_fuel_only_ini.py`, `tests/test_ms15_fuel_only_full.py`. The previous `ms15-fuel-only-config` personality override was **not used**.
- Reproducible assembly branch commit: **`3e8e80e2d96a9c7005d76107646cdce5a91ccf41`** on `ms15-test-build`. [GitHub Actions run 42921957431](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42921957431) **completed successfully** with CASM08Z; its artifact **MS15-FUEL-ONLY-UNVALIDATED-DO-NOT-FLASH** contains the S19, matching INI, source listing, assembler error logs, baseline S19 and REPORT.
- Two earlier assembly attempts failed for unsupported direct-address INC/MOV/DEC instructions on extended RAM variables in the new tach path. Corrected increment, 24-bit timestamp copies, and extended-RAM idle/staging counters and added regression assertions. Only the above final run passed.

## Source features and constraints

The transformation physically removes spark advance-table lookup, coil/dwell routines, SparkTime timer-compare ISR, ignition GPIO control and ignition-specific configuration validation. TIM2 channel 1 jump vector now targets the `Dummy` ISR (0xA3A4); the main tach IRQ and TIM2 channel 0 remain active. Direct source inspection and the assembler listing show no active instructions referencing `personality` or `check_msns`. Page-0 old ignition setting bytes remain in flash for tune ABI only, **not used by the fuel-only code**. TunerStudio ignition/unused racing menu entries are hidden; underlying calibration pages are not shifted.

Preserved fuel-related architecture: both existing **12x12 VE tables**, all existing AFR-target tables and closed-loop EGO feedback, closed-loop idle demand and MS1.5 STEP/DIR service, startup homing calibration, JS2 cooling-fan output, injection scheduling and injector PWM, warmup, TPS and MAP enrichment, the shared 24-bit RPM period calculation, serial tuning protocol and five new page-9 IAC parameters. The proven ADC-history/stepper RAM alias fix is included. Existing *unused* ignition calibration data and legacy RAM symbols have not been reclaimed; this keeps the data/page layout compatible. Not every historically named racing feature has been independently audited for removal.

## Build and independent artifact verification

Passing GitHub CI report:
- Official original CASM08Z compiled baseline memory byte-for-byte identical to shipped original 029y4a.
- **CASM08Z assembled both original and modified images with no errors.**
- Source-only five-test suite, existing MS1.5 source checker, tuning/source consistency checker all passed.
- Original calibration and bootloader memory unchanged, except exactly five new bytes at 0xE871–0xE875: `4,1,104,1,64` (4-ms step-low interval, 360-step homing, 320 max-step bench placeholders).
- MS1.5 signature and version 32-byte strings present; 17 original interrupt vector entries moved to new addresses.
- Original baseline code end `0xDB86`; dedicated fuel-only code end `0xADBA`.
- Reported change in occupied program memory: **-11,724 bytes versus original 029y4a baseline**, and 12,869 contiguous unused code bytes to DFFF. These are assembler/S19-reported numbers, *not* measured runtime performance. Note original MS1.5 grew above original baseline; compare like for like when calculating a size difference from prior custom image.

Independently parsed the downloaded image's S19 records, all checksums and address uniqueness, and confirmed `0xFAE5..0xFAE7` vector targets `0xA3A4` (Dummy), new calibration bytes, firmware signature at `0xACA6` and version at `0xAC86`.
- `MS15-FUEL-ONLY-BENCH-UNVALIDATED.s19` SHA-256: **`cf70cc258a4edf055cc442c579969788f6943e570c4fa5559a331507957277e7`**
- `MS15-FUEL-ONLY-BENCH-UNVALIDATED.ini` SHA-256: **`5976683910d0f8707836852454cf3c281943e991d2c30544187026e49d0791c5`**

**Not established:** correct real fuel pulse timing/jitter or RPM at bench frequencies, power-cycle after burn and TunerStudio reconnection, safe IAC direction/travel/homing, physical fan output, ignition outputs electrically inactive on the actual board, GUI behavior, and vehicle behavior. The former MSnS spark-output configuration error has been removed in source and is no longer set by the compiled firmware, but elimination of the user's earlier serial lockout still needs a controlled bench connection test.

**Do not flash, drive, release, or install on an engine based on assembly success.** No flash or release has been authorized. Next required step is a separate explicitly authorized Stim flash followed by injector/RPM/STEP/DIR/fan, burn/reboot/TunerStudio serial, and physical output checks.
