# MS1.5 Windows test build — 2026-11-09

**RESULT: PASS for assembly and flash-layout/static checks only. NOT a bench validation, field firmware release or authorization to flash.**

## Reproducible source & tools

- **Original input:** Owner-uploaded public MS1/Extra 029y4a ZIP. SHA-256 `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`; downloaded identical bytes from a firmware archive mirror during CI.
- **Assembler:** Original `CASM08Z.EXE` from the matching ZIP, reporting **CASM08 v3.14**. Windows GitHub Actions runner needed to send Enter to close its GUI after assembly. Both runs reported **“Successful assembly - No errors.”**
- **Changes:** [`firmware/ms15_defs.inc`](../firmware/ms15_defs.inc), [`firmware/ms15_iac.inc`](../firmware/ms15_iac.inc), [source patch](../patches/ms15-on-029y4a-wip.patch).
- **Source-only checker:** [`tools/check_ms15_source.py`](../tools/check_ms15_source.py) passed RAM aliases, no unintended JS0/JS1 original writers and estimated branch spans.
- **Passing Windows workflow:** [GitHub Actions run #42567192414](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42567192414), on branch `ms15-test-build`, with a **test-only artifact retained for 7 days**. The workflow script is [`tools/windows-test-build.ps1`](https://github.com/oolah10293/megasquirt-ms1.5/blob/ms15-test-build/tools/windows-test-build.ps1). This is not a GitHub Release.

## Assembler and ROM measurements

| Check | Observed result |
| --- | --- |
| Baseline original S19 matches official supplied prebuilt 029y4a | **Byte-for-byte identical** |
| Baseline S1 records / occupied bytes | 1,761 / 27,832 |
| MS1.5 S1 records / occupied bytes | 1,764 / 27,879 |
| Baseline main-program last byte | `0xDB86` |
| MS1.5 main-program last byte | `0xDBB5` |
| Net program occupied-byte growth | **47 bytes** |
| Remaining main-code space through `0xDFFF` | **1,098 address slots** |
| Calibration / lookup bytes `E000–FAC2` | **Unchanged** |
| Actual bootloader `FB00–FFFF` | **Unchanged** |
| Boot-vector preamble, JMP opcodes | **Unchanged** |
| Relocated vector targets | **17**, with 32 changed operand bytes confined to the `FACA–FAFF` jump-vector region; all 18 resulting vectors target application code |
| Source RAM state | 8 reused pre-existing direct-page bytes; no new RAM DS allocations |
| CASM08Z error files | Both report success, 0 errors |

**Why early validation failed:** The first flash-image checker compared **all addresses above E000** byte-for-byte and therefore rejected legitimate changes to the **interrupt jump-vector target addresses**. A targeted image comparison established that the only differences above E000 are the vector operands. The revised, passing workflow checks every vector opcode/target, actual protected tables, and bootloader separately.

The passing test image's **SHA-256** is:
`4ebac21fc198ba323f8c2e5e6ce64eb8ad30957f915f2dacd18cb3c980188c6d`.

## Explicit limitations / blockers before firmware flashing

1. **No actual runtime timing tests.** TIM2 interrupt latency, injector pulse jitter and RPM/serial concurrency must be tested on a bench.
2. **Stack margin is not proven.** No DS allocation was added and the IAC routine uses a tail jump, but compiled size alone does not prove worst-case stack high-water safety.
3. **IAC electrical and mechanical calibration is not complete.** The 320-step max and 360-step homing constants in the prototype are **placeholders**. Do not drive an actual valve with unvalidated settings; check coil impedance, direction, current limit, driver reset/enable and overvoltage protection.
4. **Fan stage is untested.** Verify the relay coil current, 2N2222 base drive and flyback diode.
5. **Tuning configuration is incomplete.** The original `msns-extra.ini` and firmware signature have **not been migrated** to MS1.5 output/idle-control semantics. The prior PWM idle tuning fields must be redesigned or safely adapted.
6. No thermal cycling, noise/reset, driver failure, stuck motor, stall, or on-engine test has been done.

**Bottom line:** This passes a genuine assembler test build and a static ROM/vector inspection. It is **not yet safe to flash into the owner's car/truck ECU**.
