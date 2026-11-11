# MS1.5 native LED modes — authorized CASM08Z assembly (2026-11-11 UTC)

**Status: ASSEMBLED + STATIC/ARTIFACT-VERIFIED; NOT FLASHED, NOT TESTED IN TUNERSTUDIO GUI, NOT STIM OR VEHICLE VERIFIED. NO RELEASE/INSTALLER/DEPLOYMENT.**

## Permission and exact source

The owner explicitly requested: “Assemble the updated `MS15_003` firmware and matching INI.” This authorized this firmware assembly and matching INI generation only, **not** a flash or deployment.

- Development source: `ms15-ignition-removal` commit **`ffe44fb5614c9f8cdae2ccc45bf91ac2049aa3b9`**, [successful integrated source-only verification run 43039859553](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/43039859553).
- Authorized Windows build branch: `ms15-test-build` commit **`05bbb4c0cf84d7f250c59aa4b512ccaf0987a684`**.
- [**Successful Windows CASM08Z assembly run 43040000309**](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/43040000309), job `130588920823`; [GitHub artifact 13864103480](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/43040000309/artifacts/13864103480). The workflow artifact is retained for seven days by its current settings.
- Historical 029y4a source ZIP verified SHA-256: `212ebf0a795973146e993571cc421ad89f4bfc541a62bb4cd12de0fff8ca7790`. CASM08Z baseline output byte-identical to shipped source S19.

## Pair of verified files

| File | Size | SHA-256 |
| --- | ---: | --- |
| `MS15_003.s19` | 36,296 bytes | `02d01305d3a23e440c74702b121b6804d49e0b798015fdede3ec83e1e1f5bfc7` |
| `MS15_003.ini` | 167,987 bytes | `d822647fe1a7ee505bd1babe5ca6aca75933d61f57bbeea2224edf25b986044a` |

Signature in both: `MS1/Extra format MS15_003 ******` (32 bytes). **Do not use the `MS15_003` INI with an older `MS15_002` ECU image or vice versa.**

## What the assembled source includes

- All six previously implemented configurable outputs retained. The three original front LEDs again offer native `Squirt` (injector activity), `Warmup Enrichment`, and `Acceleration Enrichment` choices, independently selectable on each LED, alongside condition-based output modes.
- Defaults after initial calibration: **LED17 = Squirt mode 5, LED18 = Warmup mode 6, LED19 = Acceleration mode 7, JS2 = native cooling fan mode 4, JS3 and FIDLE disabled**. Every page-9 output record remains seven bytes. Total newly added calibration region is 47 bytes at `0xE871–0xE89F` (IAC first five, six outputs next 42).
- To avoid widening the original injector ISR conditional branches beyond HC08's relative range, the native Squirt LED events now use three absolute `JMP` hooks to **out-of-line mode-5-gated handlers**, each returning via a distinct absolute `JMP`. The handlers save and restore A and CCR with `PSHA/TPA/PSHA` and `PULA/TAP/PULA`. This uses **two transient stack bytes**, but no `JSR/RTS` stack frame; actual total stack high-water and timing remain unmeasured. Actual injector event edges, rather than 100ms polling, still drive native Squirt selection.
- The WUE and acceleration LED functions read the existing engine flags in the 100ms output service. Their physical behavior was not bench-tested.

## Verified checks

- Windows CASM08Z V3.14 reported `Successful assembly - No errors.` on baseline and updated MS1.5 image.
- Five historical regression tests and **eleven integrated regression tests** passed, as did static source and tuning/INI schema checks.
- Build-script S19 audit passed: all calibration and bootloader bytes protected except intended 47 added calibration bytes and relocated interrupt-vector targets. All 18 JMP vector entries were validated, with 17 changed targets.
- Independently downloaded the resulting workflow ZIP and verified SHA-256 for both files; parsed **840 S1 records**, confirmed S-record counts/checksums and no overlapping memory writes, verified new 47-byte defaults and unique `MS15_003` ROM signature and matching INI menu entries.
- Main application code region ends at `0xA1CD`; **15,922** contiguous program addresses remain before `0xE000`. This says nothing about ISR timing or stack usage.

## Assembly issues resolved on the development branch

The first attempted build failed at `brset firing2,squirt,CHK_DONE_2JMP` (out-of-range relative branch); converting that branch to a nearby inverse-branch plus absolute JMP exposed a second out-of-range relative branch at `brset crank,engine,INJF3`. Rather than continuing to enlarge the IRQ code and chase its branches, the LED fanout was moved into the out-of-line handlers described above. The revised integrated source-only workflow passed before promotion; the final Windows assembler also passed.

**No flashing, software release, installer, or physical ECU/STIM/vehicle verification was performed.** The existing hardware status is not updated by this assembly; the owner must separately authorize any ECU flashing.
