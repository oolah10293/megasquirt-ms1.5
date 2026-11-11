; MS1.5 configurable output evaluator -- SOURCE ONLY, UNASSEMBLED.
; Included after ms15_iac.inc, executed via a main-loop tail jump.
; No interrupts disabled, no busy wait, no stack frame, no fuel timing writes.
;
; Six outputs in fixed order: 0 LED17/PTC0, 1 LED18/PTC2,
; 2 LED19/PTC1, 3 JS2/PTA3, 4 JS3/PTA2, 5 FIDLE/PTA1.
; Each has a 7-byte page-9 record:
; MODE, SRC_A, ON_A, OFF_A, SRC_B, ON_B, OFF_B.
; MODE 0=disabled, 1=A, 2=A AND B, 3=A OR B, 4=fan (JS2 only).
; Sources 0=none, 1/2=RPM above/below (100 rpm units),
; 3/4=CLT above/below (degrees F +40), 5/6=TPS above/below (ADC),
; 7/8=MAP above/below (kPa), 9/10=battery above/below (raw ADC),
; 11=engine running, 12=cranking.
; Above: ON >= ON threshold, remain on while value > OFF threshold.
; Below: ON <= ON threshold, remain on while value < OFF threshold.
; Invalid source/threshold ordering turns a condition OFF.
; The active-state masks are separate for A and B.
; GPIO pin polarity follows the processor output register; driver inversion
; and attached relay electrical behavior are NOT demonstrated here.

MS15_OUTPUT_SERVICE:
        lda     MS15_OUT_CLOCK
        cmp     #100T
        bhs     MS15_OUTPUT_DUE
        jmp     MS15_IAC_CONTINUE
MS15_OUTPUT_DUE:
        clrh    ; indexed page-9 table accesses require HX high byte = 0
        clr     MS15_OUT_CLOCK
        clr     MS15_OUT_OFS
        clr     MS15_OUT_INDEX
        mov     #1T,MS15_OUT_MASK

MS15_OUT_NEXT:
        ldx     MS15_OUT_OFS
        lda     ms15_out0_mode_f,x
        sta     MS15_OUT_MODE
        bne     MS15_OUT_MODE_CHECK
        jmp     MS15_OUT_DISABLED

MS15_OUT_MODE_CHECK:
        cmp     #4T
        bne     MS15_OUT_MODE_NORMAL
        lda     MS15_OUT_INDEX
        cmp     #3T
        bne     MS15_OUT_BAD_FAN
        jmp     MS15_OUT_ADVANCE   ; native fan handler owns JS2 in mode 4
MS15_OUT_BAD_FAN:
        jmp     MS15_OUT_DISABLED
MS15_OUT_MODE_NORMAL:
        lda     MS15_OUT_MODE
        cmp     #4T
        blo     MS15_OUT_START_A
        jmp     MS15_OUT_DISABLED

MS15_OUT_START_A:
        lda     MS15_OUT_STATE_A
        sta     MS15_OUT_LATCH
        lda     ms15_out0_src_a_f,x
        sta     MS15_OUT_SRC
        lda     ms15_out0_on_a_f,x
        sta     MS15_OUT_ON
        lda     ms15_out0_off_a_f,x
        sta     MS15_OUT_OFF
        clr     MS15_OUT_PHASE
        jmp     MS15_OUT_EVAL

MS15_OUT_AFTER_A:
        lda     MS15_OUT_LATCH
        sta     MS15_OUT_STATE_A
        and     MS15_OUT_MASK
        sta     MS15_OUT_A_RESULT
        lda     MS15_OUT_MODE
        cmp     #1T
        bne     MS15_OUT_START_B
        lda     MS15_OUT_A_RESULT
        sta     MS15_OUT_RESULT
        jmp     MS15_OUT_WRITE

MS15_OUT_START_B:
        ldx     MS15_OUT_OFS
        lda     MS15_OUT_STATE_B
        sta     MS15_OUT_LATCH
        lda     ms15_out0_src_b_f,x
        sta     MS15_OUT_SRC
        lda     ms15_out0_on_b_f,x
        sta     MS15_OUT_ON
        lda     ms15_out0_off_b_f,x
        sta     MS15_OUT_OFF
        mov     #1T,MS15_OUT_PHASE
        jmp     MS15_OUT_EVAL

MS15_OUT_AFTER_B:
        lda     MS15_OUT_LATCH
        sta     MS15_OUT_STATE_B
        and     MS15_OUT_MASK
        sta     MS15_OUT_B_RESULT
        lda     MS15_OUT_MODE
        cmp     #2T
        bne     MS15_OUT_OR
        lda     MS15_OUT_A_RESULT
        and     MS15_OUT_B_RESULT
        sta     MS15_OUT_RESULT
        jmp     MS15_OUT_WRITE
MS15_OUT_OR:
        lda     MS15_OUT_A_RESULT
        ora     MS15_OUT_B_RESULT
        sta     MS15_OUT_RESULT
        jmp     MS15_OUT_WRITE

MS15_OUT_DISABLED:
        ; Clear stale threshold latches and force disabled output low.
        lda     MS15_OUT_MASK
        coma
        and     MS15_OUT_STATE_A
        sta     MS15_OUT_STATE_A
        lda     MS15_OUT_MASK
        coma
        and     MS15_OUT_STATE_B
        sta     MS15_OUT_STATE_B
        clr     MS15_OUT_RESULT
        jmp     MS15_OUT_WRITE

; Single GPIO writer per programmable pin. JS2 in fan mode is excluded.
MS15_OUT_WRITE:
        lda     MS15_OUT_INDEX
        bne     MS15_OUT_PIN_1
        lda     MS15_OUT_RESULT
        beq     MS15_OUT_LED17_OFF
        bset    sled,portc
        jmp     MS15_OUT_ADVANCE
MS15_OUT_LED17_OFF:
        bclr    sled,portc
        jmp     MS15_OUT_ADVANCE
MS15_OUT_PIN_1:
        cmp     #1T
        bne     MS15_OUT_PIN_2
        lda     MS15_OUT_RESULT
        beq     MS15_OUT_LED18_OFF
        bset    wled,portc
        jmp     MS15_OUT_ADVANCE
MS15_OUT_LED18_OFF:
        bclr    wled,portc
        jmp     MS15_OUT_ADVANCE
MS15_OUT_PIN_2:
        cmp     #2T
        bne     MS15_OUT_PIN_3
        lda     MS15_OUT_RESULT
        beq     MS15_OUT_LED19_OFF
        bset    aled,portc
        jmp     MS15_OUT_ADVANCE
MS15_OUT_LED19_OFF:
        bclr    aled,portc
        jmp     MS15_OUT_ADVANCE
MS15_OUT_PIN_3:
        cmp     #3T
        bne     MS15_OUT_PIN_4
        lda     MS15_OUT_RESULT
        beq     MS15_OUT_JS2_OFF
        bset    output1,porta
        jmp     MS15_OUT_ADVANCE
MS15_OUT_JS2_OFF:
        bclr    output1,porta
        jmp     MS15_OUT_ADVANCE
MS15_OUT_PIN_4:
        cmp     #4T
        bne     MS15_OUT_PIN_5
        lda     MS15_OUT_RESULT
        beq     MS15_OUT_JS3_OFF
        bset    output2,porta
        jmp     MS15_OUT_ADVANCE
MS15_OUT_JS3_OFF:
        bclr    output2,porta
        jmp     MS15_OUT_ADVANCE
MS15_OUT_PIN_5:
        lda     MS15_OUT_RESULT
        beq     MS15_OUT_FIDLE_OFF
        bset    iasc,porta
        jmp     MS15_OUT_ADVANCE
MS15_OUT_FIDLE_OFF:
        bclr    iasc,porta

MS15_OUT_ADVANCE:
        inc     MS15_OUT_INDEX
        lda     MS15_OUT_INDEX
        cmp     #6T
        blo     MS15_OUT_MORE
        jmp     MS15_IAC_CONTINUE
MS15_OUT_MORE:
        lda     MS15_OUT_OFS
        add     #7T
        sta     MS15_OUT_OFS
        lda     MS15_OUT_MASK
        lsla
        sta     MS15_OUT_MASK
        jmp     MS15_OUT_NEXT

; Reusable condition evaluator. MS15_OUT_PHASE determines whether the
; condition latch belongs to A or B; no JSR/RTS stack frame is needed.
MS15_OUT_EVAL:
        lda     MS15_OUT_SRC
        bne     MS15_OUT_SRC_VALID_START
        jmp     MS15_OUT_FALSE
MS15_OUT_SRC_VALID_START:
        cmp     #13T
        blo     MS15_OUT_SRC_IN_RANGE
        jmp     MS15_OUT_FALSE
MS15_OUT_SRC_IN_RANGE:
        cmp     #11T
        blo     MS15_OUT_ANALOG_SRC
        beq     MS15_OUT_RUNNING
        brclr   crank,engine,MS15_OUT_NOT_CRANKING
        jmp     MS15_OUT_TRUE
MS15_OUT_NOT_CRANKING:
        jmp     MS15_OUT_FALSE
MS15_OUT_RUNNING:
        brclr   running,engine,MS15_OUT_NOT_RUNNING
        jmp     MS15_OUT_TRUE
MS15_OUT_NOT_RUNNING:
        jmp     MS15_OUT_FALSE

MS15_OUT_ANALOG_SRC:
        cmp     #3T
        blo     MS15_OUT_GET_RPM
        cmp     #5T
        blo     MS15_OUT_GET_CLT
        cmp     #7T
        blo     MS15_OUT_GET_TPS
        cmp     #9T
        blo     MS15_OUT_GET_MAP
        lda     batADC
        sta     MS15_OUT_VALUE
        jmp     MS15_OUT_THRESH_CHECK
MS15_OUT_GET_RPM:
        lda     rpm
        sta     MS15_OUT_VALUE
        jmp     MS15_OUT_THRESH_CHECK
MS15_OUT_GET_CLT:
        lda     coolant
        sta     MS15_OUT_VALUE
        jmp     MS15_OUT_THRESH_CHECK
MS15_OUT_GET_TPS:
        lda     tpsADC
        sta     MS15_OUT_VALUE
        jmp     MS15_OUT_THRESH_CHECK
MS15_OUT_GET_MAP:
        lda     kpa
        sta     MS15_OUT_VALUE

MS15_OUT_THRESH_CHECK:
        lda     MS15_OUT_SRC
        bit     #1T
        beq     MS15_OUT_BELOW
        ; Above threshold: OFF <= ON or reject bad threshold ordering.
        lda     MS15_OUT_OFF
        cmp     MS15_OUT_ON
        bls     MS15_OUT_ABOVE_ORDER_OK
        jmp     MS15_OUT_FALSE
MS15_OUT_ABOVE_ORDER_OK:
        lda     MS15_OUT_LATCH
        and     MS15_OUT_MASK
        bne     MS15_OUT_ABOVE_WAS_ON
        lda     MS15_OUT_VALUE
        cmp     MS15_OUT_ON
        bhs     MS15_OUT_ABOVE_SWITCH_ON
        jmp     MS15_OUT_FALSE
MS15_OUT_ABOVE_SWITCH_ON:
        jmp     MS15_OUT_TRUE
MS15_OUT_ABOVE_WAS_ON:
        lda     MS15_OUT_VALUE
        cmp     MS15_OUT_OFF
        bhi     O15_ABOVE_KEEP
        jmp     MS15_OUT_FALSE
O15_ABOVE_KEEP:
        jmp     MS15_OUT_TRUE

MS15_OUT_BELOW:
        ; Below threshold: ON <= OFF or reject bad threshold ordering.
        lda     MS15_OUT_ON
        cmp     MS15_OUT_OFF
        bls     MS15_OUT_BELOW_ORDER_OK
        jmp     MS15_OUT_FALSE
MS15_OUT_BELOW_ORDER_OK:
        lda     MS15_OUT_LATCH
        and     MS15_OUT_MASK
        bne     MS15_OUT_BELOW_WAS_ON
        lda     MS15_OUT_VALUE
        cmp     MS15_OUT_ON
        bls     MS15_OUT_BELOW_SWITCH_ON
        jmp     MS15_OUT_FALSE
MS15_OUT_BELOW_SWITCH_ON:
        jmp     MS15_OUT_TRUE
MS15_OUT_BELOW_WAS_ON:
        lda     MS15_OUT_VALUE
        cmp     MS15_OUT_OFF
        blo     O15_BELOW_KEEP
        jmp     MS15_OUT_FALSE
O15_BELOW_KEEP:
        jmp     MS15_OUT_TRUE

MS15_OUT_TRUE:
        lda     MS15_OUT_LATCH
        ora     MS15_OUT_MASK
        sta     MS15_OUT_LATCH
        jmp     MS15_OUT_EVAL_RETURN

MS15_OUT_FALSE:
        lda     MS15_OUT_MASK
        coma
        and     MS15_OUT_LATCH
        sta     MS15_OUT_LATCH
MS15_OUT_EVAL_RETURN:
        lda     MS15_OUT_PHASE
        bne     O15_EVAL_RET_B
        jmp     MS15_OUT_AFTER_A
O15_EVAL_RET_B:
        jmp     MS15_OUT_AFTER_B
