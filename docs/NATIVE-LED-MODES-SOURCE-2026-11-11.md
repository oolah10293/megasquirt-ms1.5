# Restore original MegaSquirt LED functions as selectable modes

**Status (2026-11-11): SOURCE IMPLEMENTED AND SOURCE-VERIFIED ONLY. NOT ASSEMBLED, RELEASED, FLASHED OR BENCH-VERIFIED.**

User approved restoring the missing normal MegaSquirt LED assignments without sacrificing the new independently configurable outputs. Work was performed on `ms15-ignition-removal` starting from `1ef56016c57fddcc26f0974c6d8da625b67e8eb5`.

## LED behavior

All three original onboard LED pins can independently select any of these functions:

- `5`: **Squirt / injector activity**, using the original fuel injector event edges.
- `6`: **Warmup enrichment**, using the existing `warmup,engine` state.
- `7`: **Acceleration enrichment**, using the existing `TPSAEN,engine` state.

The original four programmable modes, conditions, AND/OR logic, and hysteresis remain available. Mode `4` remains cooling fan exclusively on JS2; it is a reserved/invalid selection for LED pins. Other outputs are unchanged.

**Startup defaults:** LED17/PTC0 = `5` Squirt, LED18/PTC2 = `6` Warmup, LED19/PTC1 = `7` Acceleration, JS2/PTA3 = `4` fan, JS3 and FIDLE = `0` disabled. The six seven-byte records stay on page 9 offsets 118..159; no RAM or stored-calibration field layout changes.

The original 029y4a source/listing confirms that the Squirt LED turns on at `NEW_SQUIRT1`/`NEW_SQUIRT2` and off after both `firing1` and `firing2` are clear, before `CHK_RE_ENABLE`. `tools/finalize_ms15_fuel_only.py` now inserts a three-pin, mode-5-guarded LED fanout at those exact ISR event sites. No helper-call stack frame is added. This retains immediate injector-edge updates even if the injector pulse is much shorter than 100 ms. The periodic evaluator also reconciles the current injector firing state after a mode selection changes; the two other native states are updated from the established engine flags at its normal 100 ms cadence. **Interrupt latency and electrical behavior still require bench measurement.**

TunerStudio LED menus each list all three native modes. The output's mode field remains three bits. A new **`MS15_003`** 32-character firmware/INI signature is required so the new INI cannot silently select functions that the older `MS15_002` firmware cannot implement.

## Verification

[GitHub source-only run 43036683554](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/43036683554) **PASS**. The run reproduced the SHA-verified original 029y4a source, applied all integrated MS1.5 patches and transformations, and passed the source-only pin/RAM/branch checks, INI/flash layout checker, and **11 regression tests**, including a new test checking the exact mode-gated injector ON/ON/OFF paths and native default assignments. No assembler or S19 generation was invoked. The `ms15-test-build` branch and its old successful `MS15_002` S19 and INI remain unchanged.

**Next gate: separately authorized official CASM08Z assembly and matching `MS15_003` INI generation, with exact branch span, code-size, calibration, and vector auditing.** An actual TunerStudio GUI check and owner-controlled Stim test would follow separately. No previous built S19 includes this correction.
