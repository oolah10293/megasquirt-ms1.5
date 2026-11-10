# Independent verification of the assembled MS1.5 fuel-only artifact — 2026-11-10

**Provenance:** GitHub Actions run [42921957431](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42921957431), successful at source commit `3e8e80e2d96a9c7005d76107646cdce5a91ccf41` on `ms15-test-build`. This independent check used the **downloaded zip artifact** `MS15-FUEL-ONLY-UNVALIDATED-DO-NOT-FLASH`, rather than relying solely on the previously committed build-status narrative. The same artifact ZIP was already present in the local working directory; its SHA-256 matches the newly downloaded artifact byte-for-byte. No additional assembler run was initiated because this exact already-completed, successful run covers the requested source commit.

## Direct build-log evidence

- Job `130198754902`: completed, conclusion success.
- Official original archive SHA-256 `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`.
- Five `test_ms15_fuel_only_full.py` source tests: all OK; current MS1.5 static checker: PASS; tuning/INI checker: PASS.
- Both original and fuel-only CASM08Z error files: **"Successful assembly - No errors."**
- New artifact ZIP SHA-256: `676d9bff29110c5b3c75a9f79bab2f6bc5a77e5b6d7603337b25dc6a6ff62bd9`.
- New S19 SHA-256 `cf70cc258a4edf055cc442c579969788f6943e570c4fa5559a331507957277e7`.
- New INI SHA-256 `5976683910d0f8707836852454cf3c281943e991d2c30544187026e49d0791c5`.

## Independent S19 decoding and memory accounting

Parsed the raw S1 records, independently checking **every checksum**, record length, and uniqueness of each memory address. 1,029 S1 records yielded 16,113 mapped bytes in the new firmware (including bootloader, vectors and calibration). For comparison, the upstream baseline has 1,761 S1 records, 27,832 mapped bytes; the earlier owner's `MS15_2026-11-10.s19` has 1,768 S1 records, 27,938 mapped bytes.

| Code only (`0x8128..0xDFFF`) | Occupied address bytes | Highest address |
| --- | ---: | --- |
| Original 029y4a | 23,135 | `0xDB86` |
| Previous custom MS1.5 with ADC RAM fix | 23,236 | `0xDBEB` |
| **New fuel-only MS1.5** | **11,411** | **`0xADBA`** |

The new build contains **11,825 fewer occupied program bytes than the previous custom MS1.5** (and 11,724 fewer than original unmodified 029y4a). The contiguous unoccupied region through `0xDFFF` after code is 12,869 bytes. These are S19 address occupancy numbers, not instruction-cycle timing, measured RAM savings or hardware validation.

Checked all 18 application JMP-vector stubs at `0xFACA..0xFAFF`: each opcode was `0xCC`, each target is mapped application code. In particular:
- TIM2 channel 1 formerly used for spark now jumps to `Dummy` at `0xA3A4`, whose first opcode is `0x80` (`RTI`).
- TIM2 channel 0 (0.1ms fuel/injector timing) remains active at `0x9C05` (`TIMERROLL`).
- Main tach IRQ remains active at `0x9F03` (`DOSQUIRT`).
- Reset vector points to `0x8128`, unchanged from upstream.
- All protected bootloader bytes `0xFB00..0xFDFF` match upstream; every high-memory byte outside vector target addresses and the five intended new page-9 offsets matches upstream.

The page-9 `0xE871..0xE875` bytes are exactly `04 01 68 01 40`, the bench-only stepper presets (4ms, 360 homing pulses, 320 maximum). **Actual travel limits are not verified.**

## Fuel code and TunerStudio

Confirmed source-listing **machine-code sites**, rather than only text matches:
- `CalcRPM` around `0x8506`, VE1 lookup around `0x85BA`, VE2 lookup around `0x8D57`.
- `INJ_FIRE_CTL` at `0x9C3C`, `squirtCheck1` at `0x9FAA`, the main tach ISR at `0x9F03`.
- AFR1 targets around `0xA718` and AFR2 targets around `0xA7D5`.
- MS15 STEP/DIR IAC service at `0xACCE`.
- Fan controller at `0x92E3`, with actual assembled `bclr output1,porta` at `0x92F4` and `bset output1,porta` at `0x92F8`.

These sites prove code inclusion and valid assembly, **not that fuel pulse width and interrupts behave correctly on the Stim**.

Independently compared the new INI against the earlier `MS15_2026-11-10.ini`: its complete `[Constants]` through `[Menu]` predecessor data region is byte-identical; its `MS1/Extra format MS15_001 ******` signature is present, as is the same 32-byte signature in firmware. Active menu entry points include VE1/VE2, AFR1/AFR2, idle IAC, fan and rev limiter; spark menu entry points are commented out. No actual TunerStudio GUI, saved MSQ migration or serial read/burn was tested.

The source transform, INI transform, regression tests and two upstream patches are blob-identical between the development and assembled branches. The `ms15_iac.inc` version differs by a **five-line handoff comment only**: all 126 non-comment, nonblank instructions/labels are identical.

## Outstanding concerns found during audit

- **Important:** Removing all ignition-mode configuration checks also removed the source's original *non-ignition* configuration-error setters. Both boot and flash-burn paths clear `config_error`, and the assembled listing contains **no active `bset config_error,feature2`**. This eliminates the MSnS spark-output lockout but is broader than the original requested ignition-only exemption; relevant nonignition conflict safeguards should be reviewed before hardware use.
- Not every active, historically spark-named feature was removed. The listing still contains `sparkCut` state in shared fuel rev-limit/launch/traction logic and `REUSE_LED17` checks in the injector LED-display path, plus knock/output option paths. None of these observations proves an active ignition pulse, and the actual spark-timing ISR is eliminated. They *do* prevent claiming all obsolete ignition/racing logic has been physically cleaned up.
- No bench run verified RPM accuracy, injection staging, actual timing/jitter, temperature fan transitions, IAC electrical safety, old-settings burn/restart/reconnect, or the absence of any hazardous output transients.
- **No flash, road-use, package release or production deployment is authorized.** The build is a **bench-only, unvalidated image**. Treat the above as assembly/static results, not an engine-ready approval.
