# Stepper IAC feasibility: how we will prove timing and memory fit

**Status 2026-11-08:** Static inspection only. **No firmware compiled, modified, flashed or bench-tested.** This is a verification plan, not a claim that stepper support fits.

## Directly verified from uploaded 029y4a firmware source and shipped S19

1. **512-byte hardware RAM address range:** `src/Gp32.equ:56-57` defines `ram_start=$0040`, `ram_last=$023F` (512 addresses). Not all is available to the application.
2. **The stack is already tightly shared:** `src/boot_r12.asm:189` sets `init_stack=ram_exec-1` with `ram_exec=$01ED` in `boot_r12.asm:108`; `msns-extra.h:~528-529` warns not to add more allocated variables lest flash-table RAM copies collide with stack. `msns-extra.asm:14309-14313` has a **historical** estimate of 13 bytes of remaining stack clearance for an earlier layout. This **does not establish current 029y4a safe stack headroom**.
3. **100-microsecond interrupt is a critical constraint:** `msns-extra.asm:916-943` initializes TIM2 CH0 in 100-tick/100-µs increments; `TIMERROLL` at `msns-extra.asm:8811+` re-arms this timebase and handles time-critical work. The main loop has a late-tick check/recovery at `msns-extra.asm:6065-6086`; interrupt-tail logic has a similar missed-deadline workaround at `msns-extra.asm:9830-9855`. New synchronous stepper delays inside this path are inadvisable.
4. **Available contiguous main-code address space:** Decoding the distributed `msns-extra.s19` (Motorola S1 address/data records) shows a contiguous populated code region **0x8128–0xDB86** (23,135 bytes), followed by a gap **0xDB87–0xDFFF** (1,145 addresses) before flash calibration table 0 begins at 0xE000. Source `msns-extra.asm:13749` states `end_of_main` must not exceed `$DFFF`. These 1,145 addresses are only an **upper bound on a contiguous gap** in the existing image, *not* guaranteed usable free program capacity or proof a modification will link.
5. **Other timer uses:** `msns-extra.asm:946+` configures TIM1 for injector current-limiting PWM; TIM2 CH1 is configured for spark at `msns-extra.asm:930-940` and has handler `SPARKTIME` at `msns-extra.asm:9863+`. Since spark is not required in this application, some code/I/O may be reusable, but its interrupt and state dependencies must be audited before removing anything.
6. **Existing idle logic:** `msns-extra.asm:5391-5546` computes a PWM idle demand `idleDC` from temperature/RPM/startup/dashpot behavior. `msns-extra.asm:9370-9406` turns that value into PWM at FIDLE. Source inspection does **not** establish stepper support.

## Proposed proof in stages

### Stage 1: Static capacity and timing audit — no build

- Map each RAM allocation, calibration-table copy, communications buffer, shared scratch area and the interrupt stack; inspect transitive interrupt/call nesting. Avoid treating the full 512 bytes as free.
- Identify available outputs after preserving injectors, **one** fan, RPM input, fuel pump and serial communications. Mark board-dependent assignments **unverified** until physical circuitry is mapped.
- Define what a **specific external stepper driver** requires: inputs, pulse width/spacing, enable, voltage levels, current/coil interface, step count, homing and fault handling. Selecting a STEP/DIR IC does not by itself guarantee compatibility with a GM 4-wire IAC.
- Trace the worst-case paths through TIM2's 100-µs handler, fuel injection logic, serial interrupts and main loop. Obtain instruction-cycle estimates from MCU timing documentation; establish how much worst-case slack is available before placing stepper work.
- Prefer a **nonblocking step scheduler** whose actuator pulse generation does minimal work at a timer tick or in bounded main-loop service. Never intentionally block fuel/sensor timing while moving a motor.
- Estimate new persistent state (position, target, direction, intervals, homing/error flags) and temporary/stack bytes. Reuse existing variables only if safe at all call sites.

### Stage 2: Source-level design — no build required to draft

- Make a pin- and timing-budget proposal with absolute and relative priorities.
- Identify code that could be removed due to no spark requirement, but **do not assume** disabling a setting frees its compiled code or resources.
- Specify safety fallback for lost reference or driver faults; bound output position, movement and idle correction.
- Compare two implementation alternatives: lightweight hardware-timed pulse/dir control vs. a small driver-command state machine. Prefer the lower timing/RAM cost only after driver capability is known.

### Stage 3: Compile and measure — **requires a separate explicit build authorization**

- Build an instrumented test **only when authorized**, using an appropriate assembler and the verified source revision.
- Inspect the assembler map/listing and resulting S19: actual code addresses, page limit, RAM allocations, symbol placements, and stack safety.
- Measure worst-case interrupt service time and pulse timing on a bench emulator/test ECU with simulated RPM, coolant/TPS/load, fan operation, serial traffic and AFR feedback.
- Use a scope or logic analyzer to measure injector event jitter and 100-µs scheduler overruns **with and without** stepper movement.
- Stress cold start, high RPM, warmup, throttle transitions and serial traffic; verify resets, power loss and actuator faults leave outputs safe.

### Pass/fail gate

**Pass only if** actual code fits the memory map without stack/data overlap, all interrupt deadlines and injector jitter remain within explicitly documented limits, and the valve can move at required rates without blocking fuel control.

**Fail / redesign** if the new code needs unproven stack margin, misses timing deadlines or consumes output pins reserved for mandatory functions. Then reduce features/reuse code, change driver interface, or consider a separate intelligent actuator controller rather than asserting success.

## Limitation

The firmware archive alone can expose serious resource risks and support a strong feasibility **hypothesis**, but cannot prove safe real-time operation on the owner's modified physical ECU. Compilation (after authorization), measured timing and hardware-specific validation are necessary.
