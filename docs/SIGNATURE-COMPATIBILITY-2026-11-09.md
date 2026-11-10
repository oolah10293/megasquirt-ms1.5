# MS1.5 signature compatibility correction — November 9, 2026

## Observed bench results

The owner supplied MS Download 1.10 output reporting 1769 lines / 27942 bytes sent, Complete, and the original custom MS1.5 signature. The owner then reported the ECU running again on the Stim. The loader reported 6.12 V and a low-voltage warning; actual supply voltage has not yet been verified.

The uploaded TunerStudioDebugPackage.zip records TunerStudio MS Lite 3.3.01 communicating on COM1 at 9600 baud. It repeatedly receives all 32 signature bytes for `MS1.5 format 001 ***************`, then logs `Unsupported Controller Firmware`. Protocol initialization also sends F and times out. The active projectCfg/mainController.ini is byte-for-byte identical to the owner's uploaded MS15_TunerStudio.ini. These observations establish readable identity responses, not successful live tuning.

## Evidence and interpretation

TunerStudio developer Phil Tobin states that connection requires a recognized firmware family and that custom identities can use a known beginning:
https://www.msextra.com/forums/viewtopic.php?p=325694&sid=3c1bfe61251815ff67a81048e8832c3c

The original 029y4a source and INI use `MS1/Extra format 029y3 *********`. The proposed interpretation is that replacing this family beginning with MS1.5 caused the rejection. The exact new candidate below has NOT been tested in TunerStudio.

## Source correction

Firmware integration addendum and INI patch now use the same 32-byte ASCII identity:

`MS1/Extra format MS15_001 ******`

This retains the MS1/Extra family prefix while keeping the modified calibration format distinct from stock 029y3. The human-readable version string remains `MS1.5 TEST rev 0.1 *************`.

Only the signature and related INI comment/checks changed. The source checker now also requires the family prefix, 32 ASCII bytes, and a non-stock identity. No motor logic, timing, page offsets, or calibration values changed.

## Validation and authorization

- Applied the integration, firmware addendum, and INI patches to the owner's original 029y4a ZIP using git apply --unidiff-zero.
- check_ms15_source.py: PASS.
- check_ms15_tuning.py: PASS.
- No assembler invocation, new S19, or hardware flash was performed for this correction.
- Owner authorized firmware and INI changes. A new build has not been explicitly authorized in this continuation.
- This source change does not alter the already flashed ECU or previously delivered artifacts. Do not install the changed INI against the old flashed signature and expect a connection.
- Next: explicitly authorize a test build, verify image changes and paired INI, then bench-test the new identity. TunerStudio acceptance and all live read/write/burn behavior remain unverified.

This record supersedes the earlier handoff's statement that no flash outcome had been recovered. Historical build hashes remain attached to the original, rejected-signature image.

## Authorized build completed; artifact verification November 10

The owner subsequently explicitly authorized building the matching S19 and INI for bench testing. [Run 42747085015](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42747085015) passed on build-branch commit d2bb67b01a54b30accb78b9f4bf809343ceb8c4e.

- Original CASM08Z assembled the stock baseline and modified firmware without errors; baseline matches shipped 029y4a.
- Compared parsed S19 memory maps against the previously flashed custom image (SHA-256 97bb79390aad12bf60c69f2a9267b2d48983850207053d4b6daed3c85820f8d5).
- Exactly 22 address bytes differ, all within the 32-byte signature starting at 0xDADB. All other addresses and bytes are identical.
- S19 checksums pass. New firmware and INI signatures match.
- MS15_SIGNATURE_FIX_BENCH.s19 SHA-256: 6e300637bfc822b258f5b163c0e6ba208f821fee1fb5bbf2319b49cc3659a6ec
- MS15_SIGNATURE_FIX_BENCH.ini SHA-256: fea3b5d8f114658cff589652a80f826bb1ab4d2521f26120c0afab3cb2c59e44
- Hardware flashing of this correction, TunerStudio acceptance, and live tuning remain unverified. Earlier source-only status above is historical.

## Hardware result — November 10, 2026

Owner flashed `MS15_SIGNATURE_FIX_BENCH.s19` using MS Download 1.10 on COM1. Loader output showed complete transfer (1769 lines, 27942 bytes), the new identity in two-line chunks (`MS1/Extra format MS15_001 ******`), and controller battery voltage 12.12 V.

Owner then loaded the matching INI into the existing TunerStudio MS Lite 3.3.01 project after the signature mismatch prompt. Screenshot confirms the project title contains `MS1.5 TEST rev 0.1`, status is **Online: MegaSquirt MS1.5**, and live gauges / port indicators are displaying data (e.g. 942 RPM, 72°F CLT, 95 kPa MAP, 0.45 V O2). This is the first confirmed live serial connection to the modified firmware.

The screenshot also shows `Modified - saving test 2026-11-09_17.23.49.msq`. It does not establish which tune bytes are modified or that any burn occurred. Page read/write/burn, motor timing, electrical output, injector safety, and engine readiness remain unverified. This image remains for Stim bench testing only.
