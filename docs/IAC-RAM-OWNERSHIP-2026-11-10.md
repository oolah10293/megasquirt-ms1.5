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
