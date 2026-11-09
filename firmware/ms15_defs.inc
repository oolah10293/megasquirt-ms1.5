; --------------------------------------------------------------------------
; MS1.5 (WIP, UNBUILT) - original stepper controller definitions
; Target: original MS1 HC908GP32, 029y4a, V3.0 mainboard.
; STEP=JS0/PTA5, DIR=JS1/PTA4, fan=JS2/PTA3, JS3/PTA2 unused.
;
; All mapped RAM addresses are from 029y4a DS declarations shown to have
; NO active references in the source set. idleActClock is reclaimed ONLY
; after the original FIDLE PWM actuator is disconnected in the patch.
; Realtime/protocol/stack impact still requires separate testing.
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

; *** BENCH CALIBRATION VALUES ONLY. NOT APPROVED FOR A VALVE. ***
; Full-step driver, 2 motor steps for each unit of the old idleDC demand.
; These numbers require actual GM IAC valve testing before connecting hardware.
MS15_MAX_H          equ $01   ; 0x0140=320 steps, TEMPORARY
MS15_MAX_L          equ $40
MS15_HOME_H_INIT    equ $01   ; 0x0168=360 closing pulses, TEMPORARY
MS15_HOME_L_INIT    equ $68
MS15_BOOT_DELAY     equ 2T    ; 1 ms tick phases, initially inhibited
MS15_LOW_DELAY      equ 4T    ; >=4 published low phases between pulses
MS15_HIGH_DELAY     equ 1T    ; >=2 tick events before STEP drops
