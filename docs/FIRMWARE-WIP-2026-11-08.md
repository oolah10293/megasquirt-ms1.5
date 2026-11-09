# MS1.5 first firmware source draft — 2026-11-08

**Status: WIP SOURCE ONLY. NOT BUILT, ASSEMBLED, FLASHED, BENCH-TESTED OR RELEASED.** The owner authorized firmware *development work*, not a software/firmware build or release. This branch remains design/source work.

## Files now in repository

- [`../firmware/ms15_defs.inc`](../firmware/ms15_defs.inc): symbols, existing 029y4a RAM aliases, finite homing/position limits. **Temporary bench-only IAC calibration values.**
- [`../firmware/ms15_iac.inc`](../firmware/ms15_iac.inc): original **nonblocking** STEP/DIR finite-state controller.
- [`../patches/ms15-on-029y4a-wip.patch`](../patches/ms15-on-029y4a-wip.patch): integration changes against exactly the owner's uploaded **029y4a** `src/msns-extra.asm`; it has CRLF hunk lines, matching the original CRLF source and was verified locally with **GNU patch --binary --dry-run -p1**. The source itself is not copied to this public repository pending licensing review.
- [`../tools/check_ms15_source.py`](../tools/check_ms15_source.py): repeatable **source-only** RAM, output-write ownership and approximate branch-span checks, run against the patched source tree. This is **not** a compiler, link-map checker, emulator or timing test.

The patch inserts the two .inc files from this repo under the **`src/`** directory of the original source tree, calls initialization from the existing boot path, publishes a 1 ms tick from the timer interrupt, and **tail-jumps** to the IAC service at the main-loop end. It removes competing legacy GPIO writes rather than assuming disabled tuning options are sufficient.

## Actual I/O behavior in draft

| Purpose | Original MS1/V3.0 signal | Source behavior |
| --- | --- | --- |
| IAC STEP | **JS0 = PTA5/X2** | New module owns STEP pulses; legacy fan/water/tach/nitrous writes removed |
| IAC DIR | **JS1 = PTA4/X3** | New module owns DIR; legacy water2/tach/nitrous writes removed |
| One cooling fan | **JS2 = PTA3/X4** | Existing owner-built 2N2222 stage; original EfanOnTemp/EfanOffTemp and crank-off logic remapped here |
| Unused spare | **JS3 = PTA2/X5** | Circuit left physically and logically unmodified by new module |
| Injector 1/2, tach input, fuel pump, wideband analog input | Original functions | Retained; actual operational timing still untested |
| FIDLE/PTA1 | No longer PWM idle actuator | Held low in source draft; possible driver enable is *not* implemented |

**Intentional functional losses in MS1.5 draft:** old water/nitrous outputs on X2/X3 and Output1/boost control output on X4; historical PWM FIDLE actuator; stock X2/LED18 fan selection. Existing tune settings for those functions are **not yet migrated** to an MS1.5-specific INI. Do **not** load an old tune without a migration review. The fan stage is **not validated** for relay coil current, base drive or flyback protection.

## Timer and stack implementation

- `MSEC` executes inside the existing TIM2 timer interrupt path, which still handles 100 µs deadlines. The new interrupt work is **one `BSET`** instruction on a direct RAM address, setting bit `MS15_TICK`. The MC68HC908GP32 instruction-set table lists BSET direct as **4 bus cycles**, or **0.5 µs at an 8 MHz bus** (https://www.nxp.com/docs/en/data-sheet/MC68HC908GP32.pdf, §8.7). **This is added instructions only, not a measurement of overall interrupt headroom.**
- The actual state machine is processed at the existing main-loop tail, via a **JMP not JSR**, to avoid one extra nested return address on the tightly used 512-byte RAM/stack.
- One saturated **tick flag** coalesces missed timing events rather than causing a backlog of rapid step pulses. This intentionally favors *slower* movement under load instead of compromising injection timing.
- STEP high is held across at least two processed 1 ms events; a 4-event low delay is used before a new step. Direction changes require a separate wait period. **Real pulse lengths and execution times have NOT been measured.**
- Homing sends a **bounded** programmed number of closing steps, zeros a software position counter, and then tracks the target; it **cannot sense a physical stall or missed steps**.
- Reuses existing `idleDC` (0..255) as position demand, doubled and clamped to maximum steps; retains the original idle target, warm-up, cranking, dashpot and RPM feedback routines. **The duty-to-step mapping, motor direction and idle response need bench calibration.**

## RAM accounting and source-only validation

Original `029y4a/src/msns-extra.h` has application declarations **0x0040..0x0111** (210 bytes), followed by the existing 200-byte tuning buffer. The draft **adds no DS/RMB allocations**. It aliases **eight source-unreferenced direct-page bytes**, all individually checked:

| State symbol | Original alias | Address |
| --- | --- | --- |
| `MS15_STATE` | `idleph` | `0x74` |
| `MS15_POS_L` | `idlepl` | `0x75` |
| `MS15_POS_H` | `lmat` | `0x78` |
| `MS15_TARGET_L` | `lclt` | `0x79` |
| `MS15_TARGET_H` | `ltps` | `0x7A` |
| `MS15_HOME_L` | `lbatt` | `0x7B` |
| `MS15_HOME_H` | `lego` | `0x7C` |
| `MS15_WAIT` | `idleActClock` | `0xD3` |

**Important correction found during development:** `n2ohold` is at **0x010C** (above direct-page $FF), so it is **NOT valid** for the bit-addressing instructions used by the state byte. The checked-in state byte is `idleph` at `0x74`.

**Source-only checks performed locally**, without assembling:
- CRLF-native diff **applies cleanly to the owner's untouched uploaded 029y4a source** via `patch --binary --dry-run -p1`; the GitHub patch was checked byte-for-byte against this locally tested version.
- A Python source check confirmed **only two old-assembly PTA3/JS2 writes remain**, in the fan on/off code; no active original JS0/PTA5 or JS1/PTA4 writers remain; the original O₂-water-state test is removed so STEP pulses do not inhibit EGO.
- RAM aliases all resolve to eight **unique** existing direct-page addresses; old code no longer refers to those bytes.
- Rough instruction-form count: **79 MCU instructions, ~179 bytes for the new motor service**. This is a **manual/static size screen**, not an assembled listing, net ROM-growth measurement or a timing benchmark. Simple relative-branch span screening passed for the new service.
- No added subroutine call nesting; however **stack high-water and effective interrupt headroom are unverified**.

## Explicit blockers before anyone builds/flashes for a motor

1. **Motor electrical calibration:** identify exact GM IAC valve, coil pairs/resistance and step direction. The constants **320 max/360 homing steps** in the draft are *unverified temporary numbers*, **not permission to operate a valve**. Need safe driver current limit, supply transients and reset/sleep/enable electrical states.
2. **Fan protection:** prove the selected 2N2222 and resistor are appropriate for the actual fan *relay coil*, including flyback diode and supply. Do not connect the fan motor directly.
3. **Competing firmware features:** ensure the tune cannot re-enable water, boost, tach-output selection on IAC GPIO, historical LED/fan modes or other shared behaviours. Update `msns-extra.ini` and define a distinct firmware signature/tune migration before engine use.
4. **Assembler proof**, only after explicit owner build authorization: symbols/branch range, S19 flash/bootloader regions, memory map, vector safety and actual code growth.
5. **Scope bench testing**, only when separately authorized: TIM2 latency, injector pulse jitter, actual STEP/DIR timing, noisy supply, RPM/tach loss, reset during movement, startup homing, serial load, fan toggling and wideband error behaviour. Define pass/fail measurements before live engine use.

**Conclusion:** There is now an auditable **first firmware source draft** with a validated patch application and static RAM/I/O checks. It is **not yet a demonstrated working or safe ECU firmware**. No released firmware artifacts have been made.
