# MS1.5 IAC — static memory, code-space and timing budget

**Status:** Static arithmetic on the supplied **029y4a** source and distributed `.s19`, completed **2026-11-08**. **No source compiled, no test firmware built, no runtime or bench timing measured.** Amounts labeled 'estimated' are not verified allocations.

## 1. ROM/flash: measured from the distributed S-record

The `029y4a/msns-extra.s19` contains **1,761 Motorola S1 records** (plus termination); decoding addresses/data directly shows:

| Location | Occupied/address span | Verified interpretation |
| --- | --- | --- |
| `0x8128–0xDB86` | **23,135 bytes**, contiguous | Distributed main code/data area |
| `0xDB87–0xDFFF` | **1,145 bytes** absent from S19 | Contiguous gap before table region; **not guaranteed free relocatable flash** |
| `0xE000–0xE870` | Published calibration-page content interspersed with unpopulated addresses | Keep page organization intact |
| `0xF000+` and `0xFB00+` | Lookup tables / bootloader portions | Not general-purpose free program capacity |

`src/msns-extra.asm:13749` states `end_of_main` must not exceed `$DFFF`; `src/msns-extra.asm:13820,14319+` defines fixed flash data pages. The page/tune layout must be preserved or migrated deliberately.

**Capacity claim we can make:** there is a **1,145-address unoccupied region** at the end of the original main-program image. A modified program could grow into that region *if* the assembler/map and branch layout permit. No actual instruction/layout delta has been assembled.

## 2. RAM: static accounting from declarations (more useful than '512 bytes')

The downloaded `src/Gp32.equ:56-57` defines 512 RAM addresses `$0040–$023F`. The `src/msns-extra.asm:687-690` locates `msns-extra.h` declarations at `$0040`.

I counted **208 active DS declarations** (188 × 1 byte, 18 × 1T, 2 × 2T) through `ms_ram_end` in `msns-extra.h:108-529`. Here `T` marks decimal; that totals **210 bytes**. These are source allocations, not measurement of live variable use.

| Region | Source/bootloader basis | Addresses | Bytes |
| --- | --- | --- | ---: |
| MS1/Extra application variables | 210 DS bytes, starting `$0040` | `0x0040–0x0111` | **210** |
| Calibration/tuning RAM page | `msns-extra.h:537,648` reserves **200** bytes from `ms_rf_start` | `0x0112–0x01D9` | **200** |
| Between buffer end and stack init | `boot_r12.asm:108,189` `ram_exec=$01ED`, `init_stack=$01EC` | `0x01DA–0x01EC` | **19** |
| Interrupt scratch / flash-programming RAM alias | `msns-extra.h:656+` `int_ram=$01ED` (overlays flash burner area) | `0x01ED–0x01FC` | **16 (aliased; not free persistent RAM)** |
| Above above scratch through physical RAM end | `Gp32.equ:57` | `0x01FD–0x023F` | **67 addresses**, but potentially used by code copied to RAM for flash programming |

**Critical:** Stack grows downward from `0x01EC`, toward the 200-byte tuning buffer. The 19-address gap is **stack headroom, not extra application RAM**. Do **not** simply extend `ms_ram_end` or place stepper state there. The previous document mentioned a historical 13-byte comment at `msns-extra.asm:14309-14313`—that is **not** a current measured stack high-water mark.

The high-RAM flash-programming area must not be treated as unused without checking erase/program RAM routine footprints and operating modes; available RAM outside the 410 allocated bytes is **not 102 bytes freely allocatable**.

## 3. Candidate new persistent state — estimates only

**One practical low-RAM approach:** reuse the existing single-byte `idleDC` as **target valve position** rather than PWM duty, and add separate commanded/actual-position tracking.

| Proposed item | Estimated bytes | Notes |
| --- | ---: | --- |
| Actual position | 1–2 | 1 byte only if maximum operating travel fits 0–255 steps |
| Movement countdown | 1 | e.g. 1 ms units; max 255 ms |
| State flags / phase | 1 | Ready, DIR-settle, STEP-high, STEP-low, referencing/fault |
| Homing/reference countdown | 1–2 | Could require >255 steps; 2 bytes safer |
| Optional fault/current/idle state | 0–2 | Some may be encoded in flags or existing variables |
| **Preliminary net new state** | **4–8 bytes**, possibly more | **UNALLOCATED**; requires reclaiming verified unused variables, not shrinking stack gap |

Variable reclaiming must account for all reachable fuel-only code paths and serial field layouts. Some `SparkOnLeft*` / dwell delay fields look promising but are **not confirmed free** without a control-flow/alias audit. Do not treat 'ignition disabled' as an automatic RAM allocator.

## 4. CPU timing: source-backed scheduler and prospective budget

- `msns-extra.asm:916-943` initializes TIM2 channel 0 with 100-count advances and divide-by-8 prescale, annotated for an **8 MHz** CPU bus, yielding ~**100 µs** interrupt cadence.
- `TIMERROLL` at `msns-extra.asm:8811+` services the timebase and injector-related work; `MSEC` at `msns-extra.asm:9601-9650` runs each **10th tick** (nominally **1 ms**).
- The code has late-tick recovery logic around `msns-extra.asm:9817-9850`, demonstrating that worst-case interrupt execution time deserves direct measurement.
- The NXP MC68HC908GP32 datasheet confirms an **8 MHz-class CPU bus**; https://www.nxp.com/docs/en/data-sheet/MC68HC908GP32.pdf. At **8 MHz nominal**, one 100 µs period is **800 bus clocks** and one 1 ms period **8,000 bus clocks**. These are **arithmetic capacities**, **not available idle CPU time**.

**Proposed budget, NOT a measurement:**
- Avoid adding any busy waiting, stepping work, or per-step loops to injection critical sections.
- Attach a bounded IAC FSM to existing **1 ms MSEC** instead of every 100 µs interrupt.
- **Target** no more than **~40–100 additional bus cycles** along a step-service path (~5–12.5 µs at 8 MHz), and less on no-movement paths; these are design targets, **not demonstrated instruction counts**.
- At 100 cycles once per 1 ms, *average* cost would be 100/8,000 = **1.25% nominal CPU**, while a 100-cycle addition makes **12.5% of one 100-µs interrupt period** in its worst instant. Thus average CPU percentage alone **cannot** demonstrate acceptable injection jitter.
- Driver pulses can be **1 ms high**, with a new pulse after a configurable 5–10 ms interval. TI DRV8825 minimum STEP high/low is **1.9 µs** and DIR setup is **650 ns** (https://www.ti.com/lit/ds/symlink/drv8825.pdf). This eliminates any need for microsecond delay loops, subject to phase/driver-compatibility tests.
- The actual compiled FSM may require more than 100 cycles; if so, revise the algorithm or scheduling.

## 5. Program-growth estimate — explicitly not verified

**Rough engineering planning range:** a minimal step-state machine, startup reference and integration could need **a few hundred to about 1,000 bytes** of machine code, plus tuning changes. This is an **unassembled guess**, not a prediction. The original **1,145-byte gap** does not guarantee it will fit or that branch/jump placements will remain valid. Replacing the existing PWM actuator code can offset some growth; excising unused spark routines might create additional space but requires a disciplined source audit.

## 6. Measurable pass/fail criteria — future explicit build + bench approval needed

1. Correct assembler listing and S19 demonstrate that program remains within the intended flash regions, with flash pages and bootloader preserved.
2. Full symbol/RAM map shows no overlap among variables, the 200-byte tuning page, stack high-water requirement, and flash-RAM programmer.
3. Worst-case TIM2/serial/injector timing measured on a bench with simulated RPM/AFR/TPS/CLT, fan output and active IAC movement is **not materially degraded**. Set acceptable injection jitter and missed tick criteria **before** live test.
4. Driver timing and valve movement validated against the selected physical IAC, including direction, current, safe homing, startup, loss of reference and power-fault behavior.

**Current verdict:** Output assignment and 1 ms stepping are **plausible**, but no implementation/cycle count/stack safety is demonstrated. The RAM stack clearance is the primary concern. Do not claim the design 'fits' until the build and stress measurements exist.
