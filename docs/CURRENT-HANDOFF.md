# Active engineering handoff — MegaSquirt MS1.5

Updated: 2026-11-10. This is a **documentation-only checkpoint**. It does not authorize modifying firmware, building, releasing, or flashing anything.

**Read this file, the current Git history, and relevant code before proceeding. Do not rely on conversation memory for the project state.**

## ACTIVE SOURCE-ONLY IGNITION-REMOVAL CHECKPOINT (November 10, 2026)

**Read [the new fuel-only removal audit](IGNITION-REMOVAL-2026-11-10.md) before editing.** The project's objective is now explicitly to **remove ignition-exclusive firmware**, not to force a zero runtime ignition-personality setting. This supersedes the earlier narrow workaround design below.

The active development branch is `ms15-ignition-removal`, created from `main` at exact baseline `067987733b96a52ba918f285a7bb0a9904acc9b8`. Preserve `ms15-fuel-only-config` at `703c8090f926f0836fd1f48873daa5b7f0007a01` as historical evidence, **do not build on its personality-override approach**, and do not touch `ms15-test-build` because that branch has a push-triggered assembly workflow.

The newly uploaded 029y4a repack contains byte-for-byte matches of all four original source/S19 files recorded in the audit. The supplied November 10 S19/INI matches hashes of the *previously* built RAM-correction artifacts. The original assembler is now available for source inspection, but **no new build has been authorized**.

**New source-only commits:** `24f24bd14c95699ed305a9d1693d07f9cd689aa6` adds a guarded stage-one transformation physically deleting the original spark-table lookup and ignition-output configuration-check block, redirecting three previously fuel-to-spark transitions to `CheckSoftLimit`, and keeping nonignition conflict errors 5/6. Commits `fd562742330f59a9a42d5a15ab11f44cfa17f435` and `1d2feea520ed04551b5d194a444f6442de5a8437` add/tighten source-only tests. Five local tests on original 029y4a source passed. **No full patched-source integration, assembly, firmware image, flash, or new hardware verification exists for stage one.** The spark ISR, output writes, spark-specific portions of the shared IRQ path, configuration strings and TunerStudio menus remain. This is *incomplete firmware*, not engine-safe.

The latest source-only audit documents essential shared paths: TIM2 channel 1 has multiple spark producers; preserve TIM2 channel 0, main tach IRQ, RPM tracking, fuel injection, IAC and fan. Preserve flash calibration offsets/signature until a conscious tune compatibility migration.

**Next source task:** trace and physically remove remaining spark output scheduling/ISR and dwell paths without breaking IRQ fuel injection timing or RPM data. Then remove obsolete tuning UI and prove all remaining symbol references/port writers are intentional. Do not claim ROM/RAM savings from a source-text line count. **Never build, package, release or flash without separate explicit owner authorization.**

## Confirmed requirements

- GM 4.3L TBI, using existing MegaSquirt MS1 (MC68HC908GP32); MegaSquirt controls **fuel only**, not spark.
- Add stepper idle-air control with external STEP/DIR motor driver, wideband AFR tuning, and a single cooling-fan output.
- Current I/O plan in repo: JS0 = STEP, JS1 = DIR, JS2 = cooling fan. Verify physical outputs before vehicle use.
- Preserve existing working features, tuning settings, and signature compatibility. **Do not introduce a requirement to configure an ignition output for a fuel-only setup.**

## Source-of-truth rule (for the assistant)

1. **Before editing:** inspect current branch, recent commits, actual files and tests; use a development branch and record baseline SHA. Do not guess based on prior chat output.
2. **During a coding task:** commit coherent, *unbuilt* source changes and updated diagnostics to the development branch as early as practical, with clear status. Do not save every change solely inside a Work/chat workspace.
3. **After each meaningful checkpoint:** record what changed, exact commit SHA, evidence, known failures, and next action here or in a dated companion document. Clearly label **proposed / source-only / compiled / bench-flashed / bench-verified / engine-verified** as separate states.
4. **Do not build, package, release, or flash** without the owner's explicit authorization. Approval of a design or a generic “sounds good” is not build authorization.
5. When credits/conversation run out, inspect GitHub first. If an unfinished patch was never committed, **say it is missing**. Do not claim to have recovered the Work workspace.

## Verified GitHub state at this handoff (2026-11-10)

Repository: https://github.com/oolah10293/megasquirt-ms1.5

- `main` most recent inspected commit **`97f0197877c992074597ad79b3e4473837158d1b`** — “Record successful RAM correction build and pending Stim validation” (committed 2026-11-10 14:32 UTC).
- `ms15-test-build` most recent inspected commit **`5c132f04c6d48fabdaac9ca0227ba46acb267d68`** — “Build authorized MS1.5 ADC RAM ownership correction” (committed 2026-11-10 14:30 UTC).
- Inspected both histories: **no committed removal of the unwanted MSnS spark-output configuration requirement was found** by this checkpoint.
- Main repository retains `firmware/ms15_iac.inc`, `firmware/ms15_defs.inc`, `patches/ms15-on-029y4a-wip.patch`, tuning patches, and build tooling. Most authoritative detailed state before this handoff: [IAC RAM correction](IAC-RAM-OWNERSHIP-2026-11-10.md).
- Prior authorized build successfully produced `MS15_2026-11-10.s19` and matching `MS15_2026-11-10.ini`. See SHA256 hashes and status in [IAC RAM correction](IAC-RAM-OWNERSHIP-2026-11-10.md). Do not assume newer artifacts exist without finding them.

## Progress reported in later conversation (NOT yet confirmed in repo)

- The owner reports the corrected firmware was exercised on the Stim and the stepper was responding. The exact evidence, limits, complete travel, and direction reversal status need to be recovered or rechecked rather than inferred.
- The owner then encountered a **configuration error after burning a setting and cycling power**; TunerStudio refused to reconnect. Cause of the communication refusal is **not established** by the configuration-error source alone.
- The owner does not need spark. Most recent request in the locked Work session: remove the **unnecessary spark-output requirement**.
- The Work session exhausted its allowance **mid-change**. It is **unknown** whether the unfinished Work workspace contains uncommitted source edits. Neither examined GitHub branch had the completed change.

## Specific configuration-check target, source evidence

The uploaded November 9 assembler listing, `MS15_TEST_ASSEMBLER_LISTING_2026-11-09.lst`, shows this block in `msns-extra.asm`, source lines **2003–2010**:

```asm
check_msns:
    brclr   MSNS,personality,check3
    brset   REUSE_FIDLE,outputpins,check3
    brset   REUSE_LED17,outputpins,check3
    mov     #3,tmp4
    bset    config_error,feature2
    jmp     done_checks
```

The corresponding error string states: `If MSnS mode is set you must set LED17 or FIDLE as spark output`.

This is **verified in the November 9 historical listing**, not yet verified at the same source location in the latest integration patch. Do not blindly remove all spark checks: analyze the fuel-only mode/path and preserve real output-conflict checks and future spark-mode protections. This logic explains a specific configuration-error condition, **not by itself** the reported serial reconnection failure.

## Next steps — inspection, not an authorization

1. Inspect live source on GitHub (`main`, `ms15-test-build`) plus the actual S19/INI if available; recover any newer artifact or commit before editing. Check if an unfinished Work change was ever exported.
2. Trace the MSnS personality/output-check logic and determine how a fuel-only setup should bypass its spurious requirement **without breaking actual ignition modes or hiding legitimate conflicts**.
3. Commit a narrowly scoped *source-only* fix, tests/checks, and status to the development branch. The assistant should mark it **unbuilt**.
4. Only after explicit build authorization, assemble a matching S19/INI and validate checksums, vectors, firmware signature, protected addresses, and size. Only after separate explicit permission, bench flash and verify settings burn, power-cycle reconnection, STEP/DIR, and fault recovery.

## Caution about historical docs

Some project docs still describe earlier stages as “no flash yet,” “test only,” or “pending Stim” because they were authored before later hands-on tests. Do **not** treat an older note as a current runtime verdict; reconcile with latest commits and user-reported test evidence. Conversely, do not invent passing tests based on a successful assembly or a conversation summary.
