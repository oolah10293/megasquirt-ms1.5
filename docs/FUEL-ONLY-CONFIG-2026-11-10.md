# Fuel-only configuration source checkpoint — November 10, 2026

Baseline: main at 067987733b96a52ba918f285a7bb0a9904acc9b8.
Development branch: ms15-fuel-only-config.
Status: SOURCE EDITED AND FIXTURE-TESTED ONLY. NOT APPLIED TO THE FULL ORIGINAL ZIP; NOT ASSEMBLED, FLASHED, BENCH-VERIFIED OR ENGINE-VERIFIED.

## Recovery evidence

- GitHub main held the ADC-history RAM conflict correction and project handoff. The independent ms15-test-build branch ended at 5c132f04c6d48fabdaac9ca0227ba46acb267d68, recording a previously authorized and successful assembly, not a new spark fix.
- The historical November 9 assembler listing, MS15_TEST_ASSEMBLER_LISTING_2026-11-09.lst, contains original source lines 1977–1985: when runtime personality is zero, the firmware explicitly proceeds to conflict checking as fuel-only.
- Lines 2003–2010: check_msns emits error #3 when MSNS is selected without FIDLE or LED17 designated as spark output. This is a real ignition-setting inconsistency rather than an unconditional fuel-only requirement.
- Lines 2012–2171 contain additional configuration checks, including idle/output conflicts and an invalid count of ignition modes. These must remain.
- Lines 1744–1745 and 16175–16176 load saved flash personality into runtime personality at boot and after a page-0 burn.
- Lines 4917–4927 (spark_lookup) and 6889–6896 (nospkoff/misc_spark) directly read the flash personality, bypassing the RAM copy. Clearing runtime personality alone would not stop these two ignition paths.
- The original flash page-0 default, at line 20527, sets MSNS bit zero to 1 and explicitly comments that personality zero means fuel-only.
- Recent Stim results (JS0/JS1 operation and the post-power-cycle error/connection refusal) remain owner reports, not independently re-measured or verified for any new source.

## Narrow source-only correction prepared

The checked-in tools/apply_ms15_fuel_only.py is designed to run AFTER all existing integration/tuning patches on a disposable extraction of the exact original 029y4a source.

1. Replace both startup and page-0-burn flash-to-RAM personality copies with CLR personality. This makes runtime ignition selection zero even when an old saved tune contains MSNS.
2. Change the two direct ignition readers in spark_lookup and nospkoff to read the zero RAM personality instead of personality_f.
3. Preserve the existing check_msns, check3 and all later conflict checks. They now operate on effective fuel-only runtime mode. Do not simply delete error #3.
4. Leave saved flash configuration bytes, INI signature, page offsets, stepper, fan and ADC RAM ownership untouched. Do not alter the protected bootloader.

The transformation requires exactly four original live personality_f loads, two copies directly after outputpins loading, and the named spark reader labels. It fails rather than silently applying an incomplete edit. It preserves existing source line endings.

## Evidence and remaining limits

Four local source-only Python fixture tests passed, including both normal and CRLF input, a missing page-0-burn path rejection, and rejection of an unexpected fifth flash reader. The fixture was reconstructed from the historical listing; this does NOT prove clean application to the full source archive, valid assembly, or correct hardware behavior.

Run these checks without building:
    python -m unittest discover -s tests -p "test_ms15_fuel_only.py"

After applying the three existing patches to the original extracted tree, a future source-only integration check can use:
    python tools/apply_ms15_fuel_only.py /path/to/patched/029y4a/src/msns-extra.asm
    python tools/check_ms15_source.py /path/to/patched/029y4a/src
    python tools/check_ms15_tuning.py /path/to/patched/029y4a

Open concerns: inspect all other potential ignition output/interrupt writers before claiming fuel-only hardware safety. Stored flash and TunerStudio can still show an ignition mode selected while the dedicated MS1.5 runtime ignores it; that discrepancy should be resolved separately without risking tuning compatibility. The connection refusal after the error is not proven to be caused by the error check itself.

The existing ms15-test-build workflow has NOT been updated or triggered. A future authorized assembly must integrate this source transformation into the test build script after the existing patches and before checking/assembling. No build, package, release, or flash is authorized here. Keep the main branch and automatic-build branch untouched until the new source has been fully reviewed.
