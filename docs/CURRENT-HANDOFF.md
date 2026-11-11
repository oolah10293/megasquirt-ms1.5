# Active engineering handoff — MegaSquirt MS1.5

Updated: 2026-11-10. This is a **documentation-only checkpoint**. It does not authorize modifying firmware, building, releasing, or flashing anything.

**Read this file, the current Git history, and relevant code before proceeding. Do not rely on conversation memory for the project state.**

## FINAL SOURCE-ONLY REFINEMENTS, VERIFIED AGAINST FULL INTEGRATION (2026-11-10 local / 2026-11-11 UTC)

**Most recent source/test commit:** `a692d559259aabbbd8856651a4ef38f74d065f91` on `ms15-ignition-removal`. **Source-only CI run [42944883755](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42944883755) passed:** upstream archive pinned by SHA, all three real integration patches, two ignition/racing source cleanup transforms, two INI transforms, original source/tuning checkers, and **9 actual integrated-source regression tests**. This was a Linux source-only workflow; it did NOT invoke an assembler, generate an S19/INI image artifact, flash, or deploy anything.

Additional corrections beyond the prior six-test cleanup:
- `538f783`: when VE3 fuel-table selection is turned off in configuration, explicitly clear the previously latched `UseVE3` flag. Prevents stale VE3 fueling/AFR targeting; the optional input and fuel-table switch remain supported.
- `93ae240`, `2837ffd`: retire misleading ignition, NOS, launch, hard-cut-type and wheel help topics and update the retained fuel-table and fuel rev-limit help. Keep all [Constants] offsets, page sizes, signatures and useful UI.
- `a69792a`: physically delete unused source-level dwell/spark temp aliases (no RAM reallocation). Rename the original fuel-only extra-cranking-fuel bit reference to `MS15_ExtraCrankGate`, preserving its original `NosDcOk` bit number/semantics.
- `0eef97c`, `0b9d8b1`, `a692d55`: add strict tests for VE3 latch reset, legacy help, extra-cranking fuel and exact allowlist of surviving instructions carrying historical spark/racing identifiers. Inspect `tools/verify_integrated_source_only.py` logs for the full 53-line residual-name audit; almost all are calibration DB/EQU fields intentionally retained for old tune ABI.

**Runtime legacy-name allowlist is exactly six instructions:** pullup and read of the optional VE3 fuel-table input (old `NosIn` pin), the TIM2 channel-1 ignition timer disable and interrupt disable, and zero initialization of the `SparkAngle`/`KnockAngle` serial telemetry placeholders. No coil firing, dwell scheduling, spark table runtime, ignition output validation, nitrous/launch/traction/boost output routine or serial-blocking configuration loop remains. The fan hysteresis order validation still sets a **nonblocking** diagnostic flag and fails fan ON; water/NOS conflicts are obsolete because those output modules are removed. The six-instruction allowlist is now a regression **failure gate**, not just printed diagnostics.

**Do not use prior assembled bench S19 as this revision.** It predates all later fuel-only cleanup. This revision is SOURCE-CHECKED ONLY, not CASM08Z-assembled, Stim-tested or engine-ready. Current user authorization expressly prohibits a build, release, packaging, flash or deployment. The `ms15-test-build` auto-build branch was not modified. A future assembly and bench checks require **separate explicit permission**.

## CURRENT: COMPLETE SOURCE-ONLY FUEL CLEANUP (2026-11-10)

**The latest source state supersedes the older assembled bench-test snapshot.** Read [completed source-only cleanup record](FUEL-ONLY-SOURCE-CLEANUP-2026-11-10.md). Development branch `ms15-ignition-removal`, latest source code/test checkpoint `d649aa297bd6c419ec5aa994a361b3bce25e9b82`. Source-only GitHub Actions [run 42932812680](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42932812680) **PASSED** against full patched 029y4a: 3 actual MS1.5 patches, both transformations, six regression tests, existing source and tuning/INI checkers. No CASM08Z invocation and no new S19/INI firmware build was performed. **Do not flash the old previously assembled S19 as if it contained this work.**

The finalizer physically removes residual launch, traction, nitrous/staged-fuel adders, water injection, knock, spark/dwell, boost-actuator, generic output and spark-timer paths, preserving real fuel and RPM calculation, dual 12x12 VE, AFR, closed-loop STEP/DIR IAC, VE3 table delay, single fan and old tune page layout. An active *nonblocking* invalid-fan-hysteresis check sets the old config-error status bit for telemetry and forces fan on, but never halts the injector or tuning serial protocol. Original nonignition X2-water and nitrous-water conflict errors are intentionally obsolete since those actuators were removed. Legacy spark/knock serial fields are held at zero; deprecated flash bytes remain in place for ABI/tune migration.

**User explicitly permitted source edits, reviews and nonbuilding tests only. No authorization for assembly, packaging, a release, flashing or deployment exists for this revision.** Next phase requires separate explicit authorization and validation on actual hardware. Treat the old successful CASM08Z bench image below as historical, not current.

## LATEST INDEPENDENT ARTIFACT AUDIT (2026-11-10)

The exact CASM08Z success and bench-only artifact from Actions run `42921957431` were independently verified by downloading and decoding the original CI ZIP. See [independent S19/vector/fuel/INI audit](FUEL-ONLY-INDEPENDENT-ARTIFACT-AUDIT-2026-11-10.md), commit `3f44596e0b81db4d2386c082ce48bd95b3e38b36`. All S19 checksums and 18 vector targets were checked; TIM2 Ch1 points to `Dummy`, while IRQ and TIM2 Ch0 remain active. The compiled fuel/AFR, fan, and IAC code sites and matching INI were checked; net code memory saving is 11,825 occupied bytes relative to the previous custom MS1.5 image.

**Outstanding source issue:** the full cleanup removes unrelated configuration-error setters along with ignition-only checks; several spark-named rev-limit/knock/LED paths still exist. Do not describe the firmware as fully cleaned up, bench validated or engine safe. The user authorized assembly and analysis but **not flashing, packaging a release, or deployment**. The build and dev branches remain separate; assembled source scripts are identical to dev, while the IAC include differs only by documentation comments.

## NEWER: AUTHORIZED FUEL-ONLY TEST ASSEMBLY SUCCEEDED (2026-11-10)

The user **explicitly authorized building** the 029y4a-based dedicated fuel-only firmware while preserving the original 12x12 fuel/AFR features; this overrides older statements below that no build was authorized. It does **not** authorize flashing, packaging a release, or vehicle use.

**Verified latest test build:** GitHub Actions [run 42921957431](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42921957431), branch `ms15-test-build` at exact source commit `3e8e80e2d96a9c7005d76107646cdce5a91ccf41`, PASS. [Build audit, SHA-256 hashes, preserved features and limitations](FUEL-ONLY-BUILD-2026-11-10.md). The three prior source-change builds failed on unsupported extended-address syntax and were corrected before this successful run.

**Results:** original and new CASM08Z assembly passed with no errors, both static source/tuning checkers passed, new five-test fuel-only regression suite passed, original calibration/bootloader unchanged except 5 new IAC bytes, spark IRQ vector points to Dummy, ignition-only runtime and spark-output configuration check removed. Occupied program-code change was -11,724 bytes versus **original 029y4a**; never mistake that for a runtime test. Two downloaded artifacts (S19 and INI) are **unvalidated bench images only**; no flash has occurred.

The project should continue from the **full physical removal** script `tools/remove_ms15_ignition_full.py`, not earlier stage-one or personality isolation. The new build is a development/bench baseline, not a final release. Retain advanced fuel features and current RAM, fan, STEP/DIR decisions. Next authorization boundary is flash/Stim testing, which has **not** been given.

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
