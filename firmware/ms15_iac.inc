; AI/AGENT HANDOFF: Before editing or interpreting this firmware, read
; docs/CURRENT-HANDOFF.md and AGENTS.md and inspect latest Git commits.
; Commit source-only progress frequently; NEVER build/flash without explicit
; owner authorization. Older comments below may describe prior checkpoints.
;
; --------------------------------------------------------------------------
; MS1.5 (WIP, UNBUILT) - stepper service, main-loop tail-jump entry.
; Copyright 2026 original MS1.5 implementation. NOT road/engine validated.
;
; Call via `jmp MS15_IAC_SERVICE` at end of existing main loop.
; NOT a subroutine: no extra JSR stack frame, all exits jump to
; CalcRunningParameters. MSEC only sets one event bit in MS15_STATE.
; This service never disables interrupts and contains no busy delay.
;
; NOTE: Physical opening/closing polarity, driver reset/enable and coil
; current must be bench validated. Homing drives to a stop for a bounded
; number of pulses; it is NOT safe to flash this uncalibrated example.
; --------------------------------------------------------------------------

MS15_IAC_SERVICE:
        jmp     MS15_OUTPUT_SERVICE  ; output work at <=10 Hz, no new stack frame
MS15_IAC_CONTINUE:
; Reload startup homing count once at power-on from new page-9 calibration.
; Saturate corrupt/oversize values at 510 (actual safe valve count unknown).
        brset   MS15_INIT_DONE,MS15_STATE,MS15_INIT_FINISHED
        lda     ms15_home_hi_f
        sta     MS15_HOME_H
        lda     ms15_home_lo_f
        sta     MS15_HOME_L
        lda     MS15_HOME_H
        cmp     #$01
        bhi     MS15_HOME_CLAMP
        blo     MS15_HOME_CHECK_ZERO
        lda     MS15_HOME_L
        cmp     #$FE
        bls     MS15_HOME_CHECK_ZERO
MS15_HOME_CLAMP:
        mov     #$01,MS15_HOME_H
        mov     #$FE,MS15_HOME_L
MS15_HOME_CHECK_ZERO:
        lda     MS15_HOME_H
        ora     MS15_HOME_L
        bne     MS15_HOME_INIT_OK
        mov     #1T,MS15_HOME_L
MS15_HOME_INIT_OK:
        bset    MS15_INIT_DONE,MS15_STATE
MS15_INIT_FINISHED:
        brset   MS15_TICK,MS15_STATE,MS15_TICK_PRESENT
        jmp     CalcRunningParameters
MS15_TICK_PRESENT:
        bclr    MS15_TICK,MS15_STATE
        brset   MS15_STEP_HIGH,MS15_STATE,MS15_HIGH_PHASE

; STEP is currently low. One wait-count is processed per *new* 1 ms
; event. Missed events collapse rather than producing a burst of pulses.
MS15_LOW_PHASE:
        lda     MS15_WAIT
        beq     MS15_SELECT_MOVE
        dec     MS15_WAIT
        jmp     CalcRunningParameters

; Handle STEP HIGH for at least two separate 1 ms events, so crossing
; an interrupt boundary immediately after asserting STEP cannot make a
; sub-microsecond high pulse. This is intentionally conservative.
MS15_HIGH_PHASE:
        lda     MS15_WAIT
        beq     MS15_DROP_STEP
        dec     MS15_WAIT
        jmp     CalcRunningParameters
MS15_DROP_STEP:
        bclr    water,porta
        bclr    MS15_STEP_HIGH,MS15_STATE
        lda     ms15_step_low_f  ; configurable page-9 low interval, ms
        cmp     #2T
        bhs     MS15_STEP_LOW_VALID
        lda     #2T             ; enforce minimum even on corrupt flash
MS15_STEP_LOW_VALID:
        sta     MS15_WAIT
        jmp     CalcRunningParameters

MS15_SELECT_MOVE:
        brset   MS15_HOMING,MS15_STATE,MS15_NEED_CLOSE

; The historical closed-loop idle logic supplies idleDC (0..255). Map
; each unit to two FULL STEPS (0..510), then cap by the new flash
; page-9 maximum. Actual IAC travel must be measured and calibrated.
        lda     idleDC
        lsla
        sta     MS15_TARGET_L
        lda     #$00            ; LDA does not change the carry bit
        rola
        sta     MS15_TARGET_H
        lda     MS15_TARGET_H
        cmp     ms15_max_hi_f
        bhi     MS15_CAP_TARGET
        blo     MS15_COMPARE
        lda     MS15_TARGET_L
        cmp     ms15_max_lo_f
        bls     MS15_COMPARE
MS15_CAP_TARGET:
        lda     ms15_max_hi_f
        sta     MS15_TARGET_H
        lda     ms15_max_lo_f
        sta     MS15_TARGET_L

MS15_COMPARE:
        lda     MS15_POS_H
        cmp     MS15_TARGET_H
        bhi     MS15_NEED_CLOSE
        blo     MS15_NEED_OPEN
        lda     MS15_POS_L
        cmp     MS15_TARGET_L
        bhi     MS15_NEED_CLOSE
        blo     MS15_NEED_OPEN
        jmp     CalcRunningParameters

; Opening requires DIR=1. A changed DIR is followed by at least one
; independent wait tick before any rising STEP edge.
MS15_NEED_OPEN:
        brset   MS15_DIR_OPEN,MS15_STATE,MS15_OPEN_PULSE
        bset    water2,porta
        bset    MS15_DIR_OPEN,MS15_STATE
        mov     #1T,MS15_WAIT
        jmp     CalcRunningParameters
MS15_OPEN_PULSE:
        bset    water,porta      ; STEP high, driver advances exactly 1 step
        bset    MS15_STEP_HIGH,MS15_STATE
        mov     #MS15_HIGH_DELAY,MS15_WAIT
        inc     MS15_POS_L
        bne     MS15_OPEN_DONE
        inc     MS15_POS_H
MS15_OPEN_DONE:
        jmp     CalcRunningParameters

; Closing requires DIR=0. During homing position is not yet trusted,
; so count a finite number of pulses instead of decrementing position.
MS15_NEED_CLOSE:
        brclr   MS15_DIR_OPEN,MS15_STATE,MS15_CLOSE_PULSE
        bclr    water2,porta
        bclr    MS15_DIR_OPEN,MS15_STATE
        mov     #1T,MS15_WAIT
        jmp     CalcRunningParameters
MS15_CLOSE_PULSE:
        bset    water,porta
        bset    MS15_STEP_HIGH,MS15_STATE
        mov     #MS15_HIGH_DELAY,MS15_WAIT
        brset   MS15_HOMING,MS15_STATE,MS15_HOME_ADVANCE

; Closing from a previously referenced position; caller guarantees >0.
        lda     MS15_POS_L
        bne     MS15_POS_DEC_LOW
        dec     MS15_POS_H
MS15_POS_DEC_LOW:
        dec     MS15_POS_L
        jmp     CalcRunningParameters

MS15_HOME_ADVANCE:
        lda     MS15_HOME_L
        bne     MS15_HOME_DEC_LOW
        dec     MS15_HOME_H
MS15_HOME_DEC_LOW:
        dec     MS15_HOME_L
        lda     MS15_HOME_L
        bne     MS15_HOME_NOT_DONE
        lda     MS15_HOME_H
        bne     MS15_HOME_NOT_DONE
; We have sent the programmed number of closing pulses. This assumes
; the valve physically reached its seat: MOTOR FEEDBACK IS NOT PRESENT.
        clr     MS15_POS_L
        clr     MS15_POS_H
        bclr    MS15_HOMING,MS15_STATE
MS15_HOME_NOT_DONE:
        jmp     CalcRunningParameters

; Integrated configurable output service. Each pass returns to
; MS15_IAC_CONTINUE, preserving the original stepper timing state machine.
        include "ms15_outputs.inc"
