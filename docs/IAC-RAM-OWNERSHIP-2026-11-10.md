# Stepper RAM ownership correction — 2026-11-10

## Observed bench state

The supplied screenshot shows TunerStudio online after the signature correction. The owner's loader output reports 12.12 V. The owner subsequently selected Warmup/closed-loop with Closed loop only and reported JS0 continuously pulsing for approximately five minutes, with no observed JS1 direction change. These are owner observations, not captured electrical waveforms. A settings burn was not confirmed.

## Verified source defect

In the original uploaded 029y4a source, `Normal_ADSEL` contains `lda map,x` followed by `sta lmap,x` (msns-extra.asm lines 12118–12119). The normal ADC channel index spans 0–5. The old history array spans lmap at 0x77 through lego at 0x7C.

The stepper aliases reuse five of those bytes:

| Address | Old symbol | Stepper alias |
| --- | --- | --- |
| 0x78 | lmat | MS15_POS_H |
| 0x79 | lclt | MS15_TARGET_L |
| 0x7A | ltps | MS15_TARGET_H |
| 0x7B | lbatt | MS15_HOME_L |
| 0x7C | lego | MS15_HOME_H |

Consequently, checking only for direct references to the five legacy names missed the indexed overwrite. The ADC routine corrupts the homing counter and position/target state. This is a plausible explanation for the continuous pulsing, but a corrected-image bench test is required to establish that it resolves the reported behavior.

## Source correction

Remove the obsolete `lda map,x` / `sta lmap,x` history copy in the integration patch. The inspected application source does not read that history. Keep the live ADC smoothing sequence `lda adr; add map,x; rora; sta map,x` unchanged. Keep the direct `sta lmap` elsewhere: it touches only 0x77, which is not a stepper alias.

No RAM allocation, alias address, calibration offset, signature, or INI mapping changes. Definition comments document the ownership requirement. The source checker now checks history-array references and screens indexed application writers rather than relying solely on direct symbol searches. This is a targeted guard, not a complete assembly dataflow proof.

## Validation completed

- Applied the integration, tuning firmware, and tuning INI patches to a fresh extraction of the uploaded original 029y4a archive.
- Source checker passed: pin writers, RAM alias layout, indexed-write guards, preserved ADC smoothing, and estimated relative branch spans.
- Tuning checker passed: signature, page-9 allocation, UI mapping, and source symbols.
- Three negative regression checks passed: the checker rejected the original `sta lmap,x`, an offset `sta lmap+1,x`, and a numeric `sta $78,x` writer.

No assembler, firmware build, flash, or hardware validation was performed for this correction. The source checks do not establish timing, stack margin, electrical outputs, or engine readiness.

## Next authorized boundary

The owner authorized this source correction. Obtain explicit build authorization before generating a replacement S19. Do not update the automatic-build branch as part of this source-only change. After an authorized build and flash, verify finite startup homing and STEP stopping at a stationary target; then test movement and DIR reversal on the Stim. Keep the valve disconnected until travel limits and output behavior are verified. The previously flashed signature-corrected image still contains this RAM conflict.

## Authorized build completed

The owner explicitly authorized building after the source correction. GitHub Actions [run 42834771965](https://github.com/oolah10293/megasquirt-ms1.5/actions/runs/42834771965) completed successfully from build commit `5c132f04c6d48fabdaac9ca0227ba46acb267d68`, incorporating source commit `0dafc05d888ea59b577d46f5a95e244f12d6720f`.

Verified results:
- Original CASM08Z assembled baseline and corrected image without errors.
- Rebuilt baseline matches shipped 029y4a memory byte-for-byte.
- Assembled listing and S19 at 0xCDF0 contain `97 B6 3D EB 44 46 E7 44`: TAX followed directly by the retained ADC smoothing sequence, with the history copy absent.
- Against the previous signature-corrected custom image, calibration and bootloader memory are unchanged; interrupt-vector relocation addresses were excluded from that comparison.
- Matching INI is byte-identical to the previous signature-corrected INI.
- Main application ends at 0xDBEB, with 1044 contiguous bytes remaining before 0xE000.
- S19 record checksums and unique address mapping passed.

Delivered files:
| File | SHA256 |
| --- | --- |
| MS15_2026-11-10.s19 | 471231adeee8e109adc9496c8925c00e5cbdfd96005cb19f198ba07baaa8bd68 |
| MS15_2026-11-10.ini | fea3b5d8f114658cff589652a80f826bb1ab4d2521f26120c0afab3cb2c59e44 |

This supersedes the earlier unbuilt/build-authorization checkpoint for this correction. No flash or Stim result for the corrected image has yet been reported. Resolution of continuous pulsing remains unverified. Intended next check: finite startup homing, stopping at a stationary target, then direction reversal. Existing matching TunerStudio ECU definition can be retained.
