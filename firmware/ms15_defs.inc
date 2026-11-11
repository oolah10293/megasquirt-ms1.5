; AI/AGENT HANDOFF: Before editing or interpreting this firmware, read
; docs/CURRENT-HANDOFF.md and AGENTS.md and inspect latest Git commits.
; Commit source-only progress frequently; NEVER build/flash without explicit
; owner authorization. Verify the latest source/bench state, not just comments.
;
; --------------------------------------------------------------------------
; MS1.5 (WIP, UNBUILT) - original stepper controller definitions
; Target: original MS1 HC908GP32, 029y4a, V3.0 mainboard.
; STEP=JS0/PTA5, DIR=JS1/PTA4, fan=JS2/PTA3, JS3/PTA2 unused.
;
; Ownership is enforced by the integration patch and source checker.
; idleph/idlepl have no legacy references. lmat..lego are reclaimed from
; the obsolete ADC-history copy: remove BOTH lda map,x / sta lmap,x at
; Normal_ADSEL before using these aliases. Absence of named references
; alone is NOT evidence that a RAM byte is unused.
; idleActClock is reclaimed after removing the original FIDLE PWM writer.
; No new RAM is allocated; the existing page buffer and stack stay in place.
; Real-time/protocol/stack impact still requires separate testing.
; --------------------------------------------------------------------------
; All below are in 0x00..0xFF. The tempting n2ohold address is
; 0x010C, which is NOT addressable by direct bit instructions.
MS15_STATE          equ idleph       ; 0x74: direct-page bit operations
MS15_POS_L          equ idlepl       ; 0x75
MS15_POS_H          equ lmat         ; 0x78
MS15_TARGET_L       equ lclt         ; 0x79
MS15_TARGET_H       equ ltps         ; 0x7A
MS15_HOME_L         equ lbatt        ; 0x7B
MS15_HOME_H         equ lego         ; 0x7C
MS15_WAIT           equ idleActClock ; 0xD3, freed by FIDLE PWM removal

MS15_HOMING         equ 0  ; reference count in progress
MS15_STEP_HIGH      equ 1  ; STEP asserted on PTA5
MS15_DIR_OPEN       equ 2  ; PTA4 is in the opening direction
MS15_TICK           equ 3  ; 1 ms interrupt published a new tick
MS15_INIT_DONE      equ 4  ; new page-9 homing value loaded once after boot

; *** BENCH ONLY; actual valve limits unverified. ***
; Page-9 flash fields now define step-low delay, homing steps and max travel.
; First service pass reloads homing from flash, overriding the old boot
; placeholders that remain in the original integration patch.
MS15_HOME_H_INIT    equ $01   ; old boot placeholder, then overwritten
MS15_HOME_L_INIT    equ $68
MS15_BOOT_DELAY     equ 2T
MS15_HIGH_DELAY     equ 1T    ; held high through >=2 serviced ticks

; Configurable-output persistent state and main-loop scratch. These aliases
; reuse locations left unreferenced after the physically removed ignition,
; dwell and racing code. The integrated-source liveness tests must prove that
; no other live instruction accesses the old owners before assembly.
MS15_OUT_CLOCK      equ Out3Timer      ; 0xE5, 1 ms modulo counter
MS15_OUT_STATE_A    equ SparkDelayH    ; 0xB1, six independent A latches
MS15_OUT_STATE_B    equ SparkDelayL    ; 0xB2, six independent B latches
MS15_OUT_OFS        equ SparkOnLeftah ; 0xB3, 0,7,...,35
MS15_OUT_INDEX      equ SparkOnLeftal ; 0xB4, 0..5
MS15_OUT_MASK       equ SparkOnLeftbh ; 0xB5, 1,2,4,8,16,32
MS15_OUT_MODE       equ SparkOnLeftbl ; 0xB6
MS15_OUT_SRC        equ SparkOnLeftch ; 0xB7
MS15_OUT_ON         equ SparkOnLeftcl ; 0xB8
MS15_OUT_OFF        equ SparkOnLeftdh ; 0xB9
MS15_OUT_VALUE      equ SparkOnLeftdl ; 0xBA
MS15_OUT_LATCH      equ SparkOnLefteh ; 0xBB
MS15_OUT_PHASE      equ SparkOnLeftel ; 0xBC
MS15_OUT_A_RESULT   equ SparkOnLeftfh ; 0xBD
MS15_OUT_B_RESULT   equ SparkOnLeftfl ; 0xBE
MS15_OUT_RESULT     equ SparkTempH    ; 0xC1
