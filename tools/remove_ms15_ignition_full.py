#!/usr/bin/env python3
"""Remove ignition execution from an MS1/Extra 029y4a-based MS1.5 source tree.

Not a firmware file itself. Physically eliminates spark lookup, scheduling,
EDIS/Neon/wheel ignition, dwell, spark timer IRQ, spark configuration tests,
replacing the tach IRQ with a fuel-only period and injector scheduler.

The original RAM/flash calibration layout is intentionally preserved for tune
compatibility. Additional fuel-only feature removal is intentionally deferred.
"""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remove_ms15_ignition_stage1 import transform as first_pass


def transform(original):
    source = first_pass(original)
    eol = '\r\n' if '\r\n' in source else '\n'
    lines = source.splitlines(keepends=True)

    def label(name):
        hits = [i for i,l in enumerate(lines) if re.match('^' + re.escape(name) + ':',l,re.I)]
        assert len(hits) == 1, (name, hits)
        return hits[0]
    def marker(pat):
        hits = [i for i,l in enumerate(lines) if re.match(pat,l,re.I)]
        assert len(hits) == 1, (pat, hits)
        return hits[0]
    replacements = []
    def rep(i,j,body,desc):
        assert i < j, (desc,i,j)
        replacements.append((i,j,body.replace('\n',eol) if body else '',desc))

    # Force stale legacy config error flags inactive, with ignition validation
    # physically absent. Do not let a stored former spark option lock out fuel.
    for j,line in enumerate(lines):
        if re.match(r'^\s*sta\s+feature2\s*$',line,re.I):
            # Startup copy only; page 0 burn is rewritten independently.
            rep(j,j+1,'''        sta     feature2
        bclr    config_error,feature2
''','clear stale config status')
            break
    else:
        raise AssertionError('Missing boot-time feature2 copy')

    # Existing extra spark/pin-mode enabling is no longer needed.
    rep(marker(r'^\s*lda\s+feature8_f\s*; using spark F'),
        marker(r'^\s*sta\s+ddrd\s*; Outputs for injector'),
        '''        ; B&G fuel-only precedent: injector ports, no spark-F channel.\n        lda     #%11110000\n''', 'injector port mode')
    rep(marker(r'^\s*;is PTC4 an input\?'),[i for i,l in enumerate(lines[:1500]) if re.match(r'^\s*sta\s+ddrc\s*; Outputs for LED',l,re.I)][0],
        '''        ; PTC LEDs remain usable; no secondary ignition trigger.\n        lda     #%00011111\n''','LED port mode')
    rep(marker(r'^\s*mov\s+#\$00,T2CH1H'),[i for i,l in enumerate(lines[:1500]) if re.match(r'^\s*bclr\s+TOIE,T2SC1',l,re.I)][0]+1,
        '''        ; Dedicated fuel-only: TIM2 channel 1 never fires ignition.\n        mov     #%00010000,T2SC1\n        bclr    TOIE,T2SC1\n''','disable spark compare')

    # Discard ignition RAM initialization and various ignition-specific modes,
    # but preserve runtime flags required by injection/idle/SCI.
    rep(marker(r'^\s*sta\s+SparkCutCnt\s*; Spark Cut counter'),label('chk_out'),
        '''        ; Preserve staged-fuel and idle state setup.\n        sta     pw_staged\n        sta     pw_staged2\n        sta     stgTransitionCnt\n        clr     RevLimBits\n        clr     EnhancedBits\n        clr     EnhancedBits2\n        clr     EnhancedBits4\n        clr     EnhancedBits5\n        clr     EnhancedBits6\n        bset    mv_mode,EnhancedBits2\n''', 'remove ignition init')

    # All original ignition validation removed; no spark-output lockouts.
    rep(label('chk_out'),label('start_adc'),
        '''chk_out:\n        ; Fuel-only MS1.5 has no ignition mode or spark-output requirements.\n''','remove ignition checks')

    # Source-only spark subsystem: macros, dwell, rotor, and EDIS2. Original
    # boost fuel calculations return immediately before this block.
    rep(marker(r'^\$MACRO\s+TurnAllSpkOff'),label('TIMERROLL'),'', 'remove dwell and spark macros')
    # Avoid obsolete calls after spark subroutines removed.
    rep(marker(r'^\s*brset\s+running,engine,nospkoff'),
        marker(r'^No_misc_Spark:'),
        '''        ; No spark output to shut down or dwell to compute.\n''', 'remove main-loop spark call')

    # TIM2 0.1ms: eliminate wheel/EDIS/spark output control. Injector work
    # after INJ_FIRE_CTL remains, including injector PWM and 1ms IAC tick.
    rep(marker(r'^\s*brset\s+TFI,personality,j_tfi_spk'),label('INJ_FIRE_CTL'),
        '''        jmp     INJ_FIRE_CTL\nerror_exit:\n        pulh\n        rti\n''', 'remove 0.1ms spark scheduler')

    # On stall preserve pump, injector and RPM safety; do not execute spark
    # state reset or configure spark hold/angles.
    rep([i for i,l in enumerate(lines) if re.match(r'^\s*TurnAllSpkOff\s*; macro to turn off all spark outputs',l,re.I) and i<label('ENABLE_THE_IRQ')][0],
        label('ENABLE_THE_IRQ'),'', 'remove stall spark reset')

    # Entire spark timer interrupt and its ignition-only helper aliases;
    # retained T2Curr* for the fuel-only RPM period capture below.
    rep(label('INT_SPARK_OFFa'),label('DOSQUIRT'),
        '''; Fuel-only tach trigger timestamp temporaries.\nT2CurrX:   equ     itmp15\nT2CurrH:   equ     itmp16\nT2CurrL:   equ     itmp17\n\n''', 'remove spark channel 1 IRQ')

    # Crucial: 029y4a RPM computation uses iTimeX:H:L and the prior period,
    # not just rpmch:rpmcl. Retain a 24-bit free-running timebase delta at
    # every tach IRQ, with the existing rollover correction. Reuse 029y4a's
    # full injection scheduling block beginning squirtCheck1.
    rep(label('DOSQUIRT'),label('squirtCheck1'),
        '''DOSQUIRT:\n        pshh\n        ; Capture free-running TIM2 time for RPM and EGO/idle scheduling.\n        lda     T2CNTL\n        ldx     T2CNTH\n        stx     T2CurrH\n        lda     T2CNTL\n        sta     T2CurrL\n        lda     T2CNTX\n        cpx     #0\n        bne     MS15_NO_ROLL_CORR\n        brclr   roll2,EnhancedBits4,MS15_NO_ROLL_CORR\n        inca\nMS15_NO_ROLL_CORR:\n        sta     T2CurrX\n        mov     iTimeX,iTimepX\n        mov     iTimeH,iTimepH\n        mov     iTimeL,iTimepL\n        lda     T2CurrL\n        sub     T2LastL\n        sta     iTimeL\n        lda     T2CurrH\n        sbc     T2LastH\n        sta     iTimeH\n        lda     T2CurrX\n        sbc     T2LastX\n        sta     iTimeX\n        brclr   7,iTimeX,MS15_RPM_DELTA_OK\n        lda     T2CurrX\n        add     #1\n        sta     T2CurrX\n        clr     iTimeX\nMS15_RPM_DELTA_OK:\n        mov     T2CurrX,T2LastX\n        mov     T2CurrH,T2LastH\n        mov     T2CurrL,T2LastL\n\n        ; Retain idle settling, staging, afterstart, TPSdot and EGO counts.\n        inc     idleCtlClock\n        lda     idleDelayClock\n        beq     MS15_IDLE_DELAY_DONE\n        dec     idleDelayClock\nMS15_IDLE_DELAY_DONE:\n        brclr   REStaging,EnhancedBits,MS15_INC_FUEL_COUNTERS\n        brset   StgTransDone,EnhancedBits6,MS15_INC_FUEL_COUNTERS\n        inc     stgTransitionCnt\nMS15_INC_FUEL_COUNTERS:\n        lda     igncount1\n        bne     MS15_TPS_COUNTER\n        lda     feature10_f5\n        bit     #ASEIgnCountb\n        bne     MS15_TPS_COUNTER\n        inc     asecount\nMS15_TPS_COUNTER:\n        brclr   taeIgnCount,feature1,MS15_EGO_COUNT\n        inc     tpsaclk\n        lda     feature4_f\n        bit     #KpaDotSetb\n        beq     MS15_TPS_DOT\n        lda     kpa\n        bra     MS15_DOT_SAVE\nMS15_TPS_DOT:\n        lda     tps\nMS15_DOT_SAVE:\n        sta     TPSlast\nMS15_EGO_COUNT:\n        lda     feature14_f1\n        bit     #egoIgnCountb\n        beq     MS15_EGO_DONE\n        inc     egocount\nMS15_EGO_DONE:\n        mov     rpmch,rpmph\n        mov     rpmcl,rpmpl\n        clr     rpmch\n        clr     rpmcl\n        bset    fuelp,porta\n        bset    running,engine\n        jmp     squirtCheck1\n\n''','fuel-only tach IRQ')

    # Burn handling must not reconfigure ignition GPIO, calculate trigger angles
    # or activate spark modes. All page offsets remain stable for old tunes.
    rep(marker(r'^\s*beq\s+ck_page0'),label('DONE_B'),
        '''        beq     ck_page0
        bra     DONE_B
ck_page0:
        lda     feature1_f
        sta     feature1
        lda     feature2_f
        sta     feature2
        bclr    config_error,feature2
        lda     feature7_f
        sta     feature7
        lda     outputpins_f
        sta     outputpins
        ; Always set LED ports as GPIO; never second spark trigger.
        mov     #%00011111,ddrc
''' , 'remove post-burn spark setup')

    # The serial bootloader entry sequence must never toggle spark outputs.
    rep(marker(r'^\s*TurnAllSpkOff\s*; macro to turn off all spark outputs') if False else
        [i for i,l in enumerate(lines) if re.match(r'^\s*TurnAllSpkOff\s*; macro to turn off all spark outputs',l,re.I) and i>label('DOSQUIRT')][0],
        [i for i,l in enumerate(lines) if re.match(r'^\s*TurnAllSpkOff\s*; macro to turn off all spark outputs',l,re.I) and i>label('DOSQUIRT')][0]+1,
        '''        ; Dedicated fuel-only firmware: no ignition output exists.
''','no spark call in bootloader entry')

    # Spark mode selector no longer influences tach rearming or ADC timing.
    for pat in (r'^\s*brset\s+MSNEON,personality,INCRPMER',
                r'^\s*brset\s+WHEEL,personality,INCRPMER',
                r'^\s*brset\s+MSNEON,personality,FIRE_ADC',
                r'^\s*brset\s+WHEEL,personality,FIRE_ADC',
                r'^\s*brset\s+MSNEON,personality,IRQ_EXIT2',
                r'^\s*brset\s+WHEEL,personality,IRQ_EXIT2'):
        i=marker(pat)
        rep(i,i+1,'','no legacy spark-mode control of fuel IRQ')
    # Retain a page-0 byte for old tune-file offset stability, but do not
    # interpret it as a live configuration controlling GPIO or timing.
    i=[k for k,l in enumerate(lines[:1500]) if re.match(r'^\s*lda\s+personality_f\s*$',l,re.I)][0]
    assert re.match(r'^\s*sta\s+personality\b', lines[i+1], re.I)
    rep(i,i+2,'','no runtime ignition personality')

    # No ignition IRQ, even if a stale settings bit is present in EEPROM.
    idx=marker(r'^\s*dw\s+SPARKTIME\s*; TIM2 Ch1')
    rep(idx,idx+1, '        dw      Dummy           ; TIM2 Ch1 ignition interrupt removed\n', 'vector to dummy')

    # Apply guarded replacements descending order to avoid line offset drift.
    replacements.sort(reverse=True)
    for n,(a,b,body,desc) in enumerate(replacements):
        if n and b>replacements[n-1][0]:
            raise AssertionError('Overlapping source edits: '+desc)
        lines[a:b]=[body] if body else []
    output=''.join(lines)
    for forbidden in ('SPARKTIME:','misc_spark:','spark_lookup:','check_msns:',
                      '$MACRO TurnAllSpkOff','CYCLE_CALC:','COILNEG','COILPOS'):
        assert not re.search(r'(?mi)^'+re.escape(forbidden)+r'$',output), forbidden
    for retained in ('CalcRPM:', 'INJ_FIRE_CTL:', 'squirtCheck1:', 'AFR1_Targets:',
                     'AFR2_Targets:', 'TIMERROLL:', 'DOSQUIRT:', 'MS15_IAC_SERVICE'):
        if retained != 'MS15_IAC_SERVICE':
            assert retained.lower() in output.lower(), retained
    return output


def main():
    p=Path(sys.argv[1]); raw=p.read_bytes();out=transform(raw.decode('latin1'))
    assert out.encode('latin1')!=raw
    p.write_bytes(out.encode('latin1'))
    print('Fuel-only source physically stripped: NOT proof of valid assembly or hardware safety')

if __name__=='__main__':main()