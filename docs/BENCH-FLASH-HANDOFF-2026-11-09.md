# Bench-flash handoff — November 9, 2026

## Current checkpoint

The previous conversation, **Assess Research Claim**, reached the owner's explicit readiness to flash, then filled up. This handoff combines retrieved conversation statements with existing repository records. It is not a record of a completed flash.

**Owner-reported progress recovered from the conversation:**

- The physical ECU is running **029t**, not 029y4a. The owner explicitly corrected that distinction.
- The owner has a copy of the original **029t firmware** for recovery.
- The existing tune was preserved. Its exact filename/path was not recovered.
- Bench communication and live Stim readings were reported at **9600 baud, 8N1**. The COM-port number was not recovered.
- The owner reported expected Stim/RPM/injector behavior. The pots were dirty; one front LED might be doing something other than its original function. The owner believed the hardware was otherwise good. This is a functional baseline report, not independently measured timing validation.
- The owner said **“yep, i'm ready to flash it.”** The subsequent continuation explicitly authorized recovering the context and updating this repository.

These statements are recovered user reports, not fresh observations of the ECU. The original screenshots and PC files were not reinspected for this handoff. Do not ask the owner to repeat the completed baseline solely because the conversation changed.

## Authorization versus validation

The recovered context identifies the next intended activity as a **controlled MS1.5 bench flash and 029t recovery procedure**. The owner's go-ahead supersedes older documentation's statement that bench flashing had not yet been authorized. It does not establish runtime safety, authorize engine use, or authorize a new build, installer, or release.

The existing image remains an **unvalidated test image**. No successful flash or post-flash result was recovered. Earlier “DO NOT FLASH” labels record the status when those artifacts were created; preserve their test-only provenance while distinguishing it from the later owner authorization.

## Existing build evidence

The [tuning-integrated build report](TEST-BUILD-TUNING-2026-11-09.md) records:

- Source base: **029y4a**. This is distinct from the ECU's owner-reported installed **029t**.
- Build branch: `ms15-test-build`.
- Build commit: `b40a66e2b0c5cecdf7a38c2ebcd1cfb52d1fcbd0`.
- Passing run: [42666625242](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42666625242).
- Recorded S19 SHA-256: `97bb79390aad12bf60c69f2a9267b2d48983850207053d4b6daed3c85820f8d5`.
- Signature: `MS1.5 format 001 ***************`.
- Test version: `MS1.5 TEST rev 0.1 *************`.
- Page-9 motor defaults: 4 ms low delay, 360 closing steps, 320 maximum opening steps. These are test defaults, not validated valve travel limits.

This handoff verifies what the report says; it does **not** newly hash the owner's current S19 or establish that a similarly named file is identical. The matching custom INI is required by the recorded tuning design. Do not silently substitute the earlier unconfigured test image or the stock 029y4a INI.

The [offline UI record](TUNERSTUDIO-OFFLINE-UI-2026-11-09.md) documents owner-reported IAC/fan field display and tune save/reopen success. Those offline results do not establish live MS1.5 serial reads, writes, or burns. Working communication with original 029t is a separate, later checkpoint.

## Remaining retrieval gaps

The exact final flashing instructions were **not recovered**. Do not describe a newly prepared procedure as a verbatim recovered plan.

Not established by the recovered material:

- Selected local S19 filename/path and current file hash.
- Flash-loader executable/version, its exact prompts, command line, and boot-entry/recovery sequence.
- COM-port number and local backup paths.
- Exact Stim model.
- Whether the two previously documented AFR-table unit warnings were subsequently resolved, or which wideband calibration was selected.
- Any actual flash, MS1.5 connection, read/burn test, motor test, or injector timing measurement.

The [board-photo record](BOARD-PHOTO-2026-11-08.md) already records the V3.0 mainboard identification. Do not reopen that as an entirely unknown board revision.

## Proposed continuation — not yet executed

1. Verify the selected existing S19 and matching INI against their recorded provenance; establish the loader and COM port from available files/evidence.
2. Verify the exact loader's MS1/Extra flashing and 029t recovery instructions before giving executable commands or jumper instructions. Keep the preserved tune and original 029t available.
3. Carry out the already-authorized controlled Stim/bench flash, recording loader output and outcome.
4. Check the returned firmware signature/version and live sensor/RPM behavior with the matching MS1.5 project. Read ECU settings before deciding what to write; do not assume an old 029t tune can be imported unchanged.
5. Record actual read/write/burn and restart results, then proceed to the remaining IAC/fan/injector timing validation as separately scoped bench work.

Steps 1–5 are a proposed reconstruction of how to resume, not evidence they happened. Detailed electrical setup and loader operations still require source verification.

## Handoff maintenance

This document supersedes older status statements about unknown installed firmware, missing baseline communication, and absent bench-flash authorization. Historical build and UI reports retain their original test limits. Update this checkpoint with the actual flash outcome before describing MS1.5 as running on the ECU.
