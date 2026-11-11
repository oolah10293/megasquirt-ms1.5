#!/usr/bin/env python3
"""Source-only final cleanup of integrated MS1.5 fuel-only firmware.

Run after existing integration patches and the full ignition-removal pass.
No assembler, firmware generation, deployment or flashing.
"""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remove_ms15_ignition_full import transform as initial_fuel_only


def transform_integrated(source: str) -> str:
    eol = '\r\n' if '\r\n' in source else '\n'
    lines = source.splitlines(keepends=True)
    changes = []

    def find(name: str) -> int:
        found = [i for i, line in enumerate(lines) if re.match(r'^' + re.escape(name) + r':', line, re.I)]
        assert len(found) == 1, (name, found)
        return found[0]

    def matchline(pat: str) -> int:
        found = [i for i, line in enumerate(lines) if re.match(pat, line, re.I)]
        assert len(found) == 1, (pat, found)
        return found[0]

    def replace(start: int, end: int, body: str, note: str):
        assert 0 <= start < end <= len(lines), (note, start, end)
        changes.append((start, end, body.replace('\n', eol), note))

    def block(a: str, b: str, body: str = '', note: str = ''):
        replace(find(a), find(b), body, note or a)

    # Original dwell/spark-time temporary aliases are definitions, not RAM
    # reservations. With all their computation removed, delete the dead
    # names instead of retaining misleading active-looking spark symbols.
    replace(matchline(r'^\s*;misc_spark uses these'),
            matchline(r'^\s*SparkdltL\s+equ\s+tmp4')+1,
            '', 'remove dead dwell/spark calculation temp aliases')

    # No launch/shift switch pullups. Retain optional VE3 table selector input
    # (historical NOS input pin); it's now fuel table selection only.
    replace(matchline(r'^\s*bset\s+launch,ptdpue'),
            matchline(r'^\s*bset\s+launch,ptdpue') + 1, '', 'launch input pullup')

    # Strip the last startup spark-output3 GPIO and obsolete state writes.
    # Fuel RAM, all fuel-derived clocks, and alternating-injector counters
    # remain initialized by the original source.
    replace(matchline(r'^\s*brset\s+out3sparkd,feature2,w_no3'),
            find('w_no3')+1,'','delete last spark-only output3 initializer')
    obsolete_boot = ('splitdelH','splitdelL','KnockAngleRet','KnockAdv',
        'KnockTimLft','TCAngle','KnockBoost',
        'N2Olaunchdel','NitrousAngle','NosPW')
    for symbol in obsolete_boot:
        found=[i for i,l in enumerate(lines[:find('chk_out')])
               if re.match(r'^\s*sta\s+'+symbol+r'\s*(?:;.*)?$',l,re.I)]
        assert len(found)==1,(symbol,found)
        replace(found[0],found[0]+1,'','remove unused startup '+symbol)
    # Existing serial schema contains three former ignition-display bytes;
    # keep clearing the old KnockAngle/CltIatAngle fields at startup, and
    # initialize SparkAngle to zero so no stale uninitialized telemetry leaks.
    c=matchline(r'^\s*sta\s+iTimepL\s*$')
    replace(c,c+1,lines[c]+'        sta     SparkAngle    ; legacy serial placeholder'+eol,
            'zero obsolete spark display field without any ignition control')
    for n in range(1,7):
        i=matchline(r'^\s*sthx\s+dwelldelay'+str(n)+r'\s*$')
        replace(i,i+1,'','delete unused ignition dwell RAM init')
    # The old dynamic N2O pulse width was added in three separate stages
    # of the *real* staged fuel calculation. Removing it leaves all injector
    # and staged-fuel calculations but no hidden nitrous fuel adder.
    nos_add=[i for i,l in enumerate(lines) if re.match(r'^\s*add\s+NosPW\s*$',l,re.I)]
    assert len(nos_add)==3,nos_add
    for i in nos_add: replace(i,i+1,'','remove nitrous PW from staged fuel')
    # Former spark-table-2 delay has no consumers after ignition removal;
    # in contrast VE3Timer is an active, useful fuel-table selection delay.
    replace(matchline(r'^\s*lda\s+Spark2Delay_f\s*$'),
            matchline(r'^\s*sta\s+ST2Timer\s*; Set delay timer for ST2')+1,
            '', 'no spark-2 timer at boot')
    replace(matchline(r'^\s*lda\s+ST2Timer\s*$'),
            matchline(r'^\s*lda\s+VE3Timer\s*; VE Table3 delay timer'),
            '', 'no spark timer at 0.1s tick')
    replace(matchline(r'^\s*brclr\s+NosIn,portd,No_St2Delay'),
            matchline(r'^\s*brset\s+taeIgnCount,feature1,No_TPSCount'),
            '', 'remove spark-table switch delay only; keep VE3 timer')
    i=matchline(r'^\s*inc\s+Out3Timer\s*$')
    replace(i,i+1,'','remove dead general-output timer')

    # No shift LEDs/secondary-ignition outputs. Keep three standard panel LEDs.
    i = matchline(r'^\s*lda\s+#%00011111\s*$')
    replace(i, i+1, '        lda     #%00000111\n', 'only standard fuel status LEDs')
    # If boot-time feature2 previously has stale spark bits, the existing full
    # removal clears config_error; no obsolete lockout will be recreated.

    # Eliminate stale-settings EGO gating from deleted water/NOS hardware.
    # Both ordinary closed-loop EGO correction and AFR targets are retained;
    # overrun/decel exclusions below remain active.
    replace(find('EGO_CALC'), matchline(r'^\s*brset\s+OverRun,EnhancedBits,SKIP_ALL_O2'),
            'EGO_CALC:\n', 'no water/nitrous EGO disable bits')
    i=matchline(r'^\s*brset\s+Traction,EnhancedBits2,Skip_ALL_O2')
    replace(i,i+1,'','no traction inhibition of AFR feedback')

    # Legacy config errors were entirely ignition/water/NOS-specific. With
    # those modules removed, the original fatal config-error branch and
    # infinite pump/serial-error loop are hazardous dead code. Remove them
    # physically, never let a stale old settings bit block tuning or fuel.
    i=matchline(r'^\s*brset\s+config_error,feature2,config_er1JMP')
    replace(i,i+1,'','never enter old configuration dead-end')
    block('config_er1JMP','PumpPrime','','delete obsolete jump')
    block('config_error1','CalcRunningParameters','',
          'delete infinite lockout and obsolete serial error transmitter')
    block('error_vector','WWURANGE','',
          'delete 15 dead spark/water/nitrous error messages')

    # Restore a REAL non-ignition configuration check: invalid fan on/off
    # hysteresis is reported through the existing config_error status bit.
    # Crucially, it NEVER blocks fuel, serial communication, or runtime:
    # fail-safe engages the fan. The old water/fan & nitrous/water errors
    # were conflicts between functions we have now physically deleted.
    replace(find('DO_FAN_Check'), find('FAN_OFF'), '''DO_FAN_Check:
        ; Fan hysteresis is exclusively active for JS2 mode 4.
        ; Other modes are owned by the programmable-output writer.
        lda     ms15_out3_mode_f
        cmp     #4T
        beq     MS15_FAN_ACTIVE
        bclr    config_error,feature2
        jmp     FAN_DONE
MS15_FAN_ACTIVE:
        lda     EfanOnTemp_f
        cmp     EfanOffTemp_f
        bhi     MS15_FAN_LIMITS_OK
        bset    config_error,feature2  ; nonblocking diagnostic, not lockout
        jmp     FAN_ON          ; invalid/reversed threshold: cool engine
MS15_FAN_LIMITS_OK:
        bclr    config_error,feature2
        brset   crank,engine,FAN_OFF
        lda     coolant
        cmp     EfanOnTemp_f
        bhi     FAN_ON
        cmp     EfanOffTemp_f
        blo     FAN_OFF
        bra     FAN_DONE

''', 'valid single-fan hysteresis and nonblocking fail-safe')

    # Replace the whole launch/spark/traction/nitrous fuel-cut mix with a
    # single deterministic hard fuel cut and delayed soft fuel cut, retaining
    # staged-injector PW and deceleration fuel cut. No legacy cut-mode bits.
    block('checkRPMsettings', 'CheckOutputs', '''checkRPMsettings:
        ; Hard rev limiting always cuts FUEL, never spark. Zero = disabled.
        lda     RevLimit_f
        beq     MS15_REV_HARD_OK
        cmp     rpm
        blo     MS15_CUT_FUEL
MS15_REV_HARD_OK:
        brset   RevLimHSoft,RevLimBits,MS15_CUT_FUEL
        brset   OverRun,EnhancedBits,MS15_CUT_FUEL
        ; Preserve staged injection and independent second VE/fuel table.
        lda     feature5_f
        bit     #stagedeither
        beq     MS15_SAVE_FUEL
        brclr   REStaging,EnhancedBits,MS15_UNSTAGED
        lda     pw_staged
        sta     tmp1
        lda     pw_staged2
        sta     tmp2
        bra     MS15_SAVE_FUEL
MS15_UNSTAGED:
        clr     tmp2
MS15_SAVE_FUEL:
        mov     tmp1,pwcalc1
        mov     tmp2,pwcalc2
        jmp     CheckSoftLimit
MS15_CUT_FUEL:
        clr     pwcalc1
        clr     pwcalc2
        jmp     CheckSoftLimit

CheckSoftLimit:
        ; Delayed soft limiter is a fuel-only protection, not spark retard.
        lda     SRevLimRPM
        beq     MS15_SOFT_RESET
        cmp     rpm
        blo     MS15_SOFT_ACTIVE
        bhi     MS15_SOFT_RESET
        brset   RevLimSoft,RevLimBits,MS15_SOFT_ACTIVE
MS15_SOFT_RESET:
        bclr    RevLimSoft,RevLimBits
        bclr    RevLimHSoft,RevLimBits
        clr     SRevLimTimeLeft
        jmp     CheckOutputs
MS15_SOFT_ACTIVE:
        bset    RevLimSoft,RevLimBits
        lda     SRevLimTimeLeft
        bne     MS15_SOFT_DONE
        brset   RevLimHSoft,RevLimBits,MS15_SOFT_DONE
        lda     SRevLimHTime
        bne     MS15_SOFT_DELAY
        bset    RevLimHSoft,RevLimBits
        clr     pwcalc1
        clr     pwcalc2
        bra     MS15_SOFT_DONE
MS15_SOFT_DELAY:
        sta     SRevLimTimeLeft
MS15_SOFT_DONE:
        jmp     CheckOutputs

''', 'fuel-only RPM protection, staging, decel')

    # General-purpose output controllers were capable of overriding STEP,
    # DIR and FAN reserved lines, depending on stale page-0 settings. Keep
    # only the project-specific fan actuator and injector outputs.
    block('CheckOutputs', 'DO_FAN_Check', '''CheckOutputs:
        ; All legacy general outputs, shift lamps and racing outputs removed.
        ; Continue directly to reserved JS2 fan controller.

''', 'remove multi-output racing pins')
    # Remove 0.1ms boost clock and the old all-injector-stop configuration
    # lockout. Ignition conflict fields can remain in legacy tune flash but
    # cannot stop fuel PWM or shut down the serial configuration interface.
    replace(matchline(r'^\s*brset\s+config_error,feature2,error_exit'),
            find('INJ_FIRE_CTL'),
            '        inc     mms\n        jmp     INJ_FIRE_CTL\n',
            'remove obsolete configuration lockout and boost timer overhead')

    # Obsolete water-injection and spark-only IAT/CLT ignition trim sections.
    # Include the unconditional water-mode prelude ahead of Water_Injection.
    w=find('Water_Injection')
    prelude=[i for i in range(find('Over_Run_Done'), w) if re.match(r'^\s*lda\s+feature3_f\s*$',lines[i],re.I)]
    assert len(prelude)==1,prelude
    replace(prelude[0], find('IdleAdjust'), '', 'remove water and spark trim')
    # No knock angle adjustments, traction slip/timer or speed sensor logic.
    block('Knock_Detection', 'Prime_Checked', '', 'remove knock and traction')
    # Keep useful VE3 and AFR tables, but no boost/nitrous subloop.
    block('Prime_Checked', 'No_VE_Table_3', '''Prime_Checked:
        ; VE3 is optional FUEL mapping; clear its active latch whenever
        ; disabled in a tune, even if the input was previously selected.
        lda     feature6_f
        bit     #VETable3b
        bne     MS15_CHECK_VE3_OPTION
        bclr    UseVE3,EnhancedBits
        bra     No_VE_Table_3
MS15_CHECK_VE3_OPTION:
        jsr     Check_VE3_Table

''', 'remove boost/nitrous invocation and clear disabled VE3 latch')

    # Boost control tables and rotary split-angle macros are no longer called;
    # retain fuel VE lookup ending in VE_STEP_6 and entire TIMERROLL ISR.
    replace(matchline(r'^\*\* Boost Controller  table lookup macros'),
            find('TIMERROLL'), '', 'remove boost and rotary timing routines')
    # Nitrous controller, fuel adders and anti-lag. Preserve second VE-table
    # switching independently of nitrous activation; the legacy NOS input
    # remains *only* a table-selector input, never an actuator control.
    block('EnableN2O', 'AFR1_Targets', '''Check_VE3_Table:
        ; The pre-existing alternate table-select input stays available for
        ; fuel-only operation; its historical name in the header is NosIn.
        brset   NosIn,portd,MS15_VE3_OFF
        bset    UseVE3,EnhancedBits
        rts
MS15_VE3_OFF:
        bclr    UseVE3,EnhancedBits
        rts

''', 'remove nitrous/anti-lag, retain VE3 switch')

    # Remove water injector secondary output scheduling without disturbing
    # either injector driver or PWM transitions. Patched integrated source
    # comments out JS1 writer, but branch still executes water mode checks.
    water_intro=[i for i in range(find('NEW_SQUIRT2'),find('INJF3JMP'))
                 if re.match(r'^\s*lda\s+feature3_f\s*$',lines[i],re.I)]
    assert len(water_intro)==1,water_intro
    assert re.search(r'WaterInjb',lines[water_intro[0]+1],re.I)
    replace(water_intro[0],find('INJF3JMP'),'',
            'remove all water injection after second injector activates')
    water_shutdown=[i for i in range(find('OFF_INJ_2'),find('Dont_Clr_Water2'))
                    if re.match(r'^\s*lda\s+feature3_f\s*$',lines[i],re.I)]
    assert len(water_shutdown)==1,water_shutdown
    replace(water_shutdown[0],find('Dont_Clr_Water2'),'',
            'remove water shutdown without changing fuel injector current limit')

    # Remove tach pulses on reserved STEP/DIR/FAN pins; rearming tach IRQ stays.
    block('REARM_IRQ','CHK_REARM', '''REARM_IRQ:
        ; No tachometer/spark simulation writer on STEP/DIR/FAN.

''', 'remove legacy tach output controls')
    # Eliminate idle-actuator spark output ownership, old boost PWM, and
    # disabled FIDLE-mode branch. The project's patched source already
    # replaces the PWM actuator with a constant safe level.
    replace(find('inj2done'),find('CHECK_RPM'),
            'inj2done:\n        ; FIDLE is now owned by MS15_OUTPUT_SERVICE.\n\n',
            'single non-PWM idle actuator (STEP/DIR runs in main loop)')

    # Eliminate old spark ownership of front-panel injection LED.
    for pat in (r'^\s*brset\s+REUSE_LED17,outputpins,nsq1',
                r'^\s*brset\s+REUSE_LED17,outputpins,nsq2',
                r'^\s*brset\s+REUSE_LED17,outputpins,CHK_RE_ENABLE'):
        j=matchline(pat)
        replace(j,j+1,'','remove ignition pin reuse of injector LED')

    # Zero otherwise-unused knock timer/idle advance (fuel idle clock remains).
    replace(matchline(r'^\s*brclr\s+IdleAdvTimeOK,EnhancedBits6,knock_timer_checks'),
            find('Secs'), '', 'remove idle ignition advance and knock timer')

    # Section was previously used for nitrous launch delays. The generic
    # second-table transition timer must remain; only remove N2O countdown.
    replace(matchline(r'^\s*brclr\s+Launch,portd,nol_timer'),
            find('end100th'),'', 'remove launch-triggered nitrous countdown')

    # The legacy fail-safe setting could bypass IRQ ACK/rearm. Keep tach
    # filtering/rearm active independent of old spark decoder mode bits.
    replace(find('CHK_REARM'), find('INCRPMER'), '''CHK_REARM:
        bset    ACK,INTSCR
        bclr    IMASK,INTSCR

''', 'preserve tach rearm safety without obsolete spark test bypass')

    # Apply descending so original source line anchors stay stable.
    changes.sort(reverse=True)
    for j,(a,b,body,note) in enumerate(changes):
        if j and b > changes[j-1][0]:
            raise AssertionError('Overlapping changes: '+note)
        lines[a:b] = [body] if body else []
    result = ''.join(lines)
    assert result != source
    # Keep old RAM layout but expose the formerly spark-named byte only as
    # a prime-pulse counter. Historical symbol retains its storage address.
    result, count = re.subn(r'(?im)^(\s*(?:lda|sta|inc|clr|dec)\s+)TCSparkCut\b',
                            r'\1MS15_PrimeCount', result)
    assert count==5,count
    # NosDcOk was reused in original 029y4a for *extra cranking fuel*.
    # Nitrous operation is gone; keep this fuel feature and its precise
    # flag bit, but stop referencing the stale NOS identifier at runtime.
    result, count = re.subn(
        r'(?im)^(\s*(?:brclr|brset|bclr|bset)\s+)NosDcOk(?=,EnhancedBits\b)',
        r'\1MS15_ExtraCrankGate', result)
    assert count==5, count
    inc='include "msns-extra.h"'
    assert result.count(inc)==1
    result=result.replace(inc,
        inc+eol+'MS15_PrimeCount  equ TCSparkCut ; priming, not ignition'
        +eol+'MS15_ExtraCrankGate equ NosDcOk ; original extra-cranking-fuel flag')
    # Use existing, intentionally freed direct-page locations. Explicitly
    # initialize all persistent output state before the first main-loop pass.
    init='mov     #$01,MS15_STATE'
    assert result.count(init)==1
    result=result.replace(init,init+eol+
        '        clr     MS15_OUT_CLOCK'+eol+
        '        clr     MS15_OUT_STATE_A'+eol+
        '        clr     MS15_OUT_STATE_B')
    # Minimal once-per-1ms clock work: six pin evaluations run in the main
    # loop only when the 100ms counter reaches 100, never in injector ISRs.
    tick='bset     MS15_TICK,MS15_STATE'
    assert result.count(tick)==1
    result=result.replace(tick,tick+eol+'        inc     MS15_OUT_CLOCK')

    # Front-panel LEDs are no longer injection, warmup or spark indicators.
    # Keep branch target labels and physical injector paths intact, replacing
    # the old LED pin commands with NOP; each bit now has one owner in the
    # programmable output service.
    led_line=re.compile(
        r'(?im)^(?P<prefix>\s*(?:(?:[A-Za-z_]\w*):\s*)?)'
        r'(?:bset|bclr)\s+(?:sled|wled|aled|coila|coilb),portc\b[^\r\n]*')
    result,nled=led_line.subn(
        lambda m:m.group('prefix')+'nop     ; MS1.5 programmable LED owns this pin',result)
    assert nled>=3,('no legacy LED pin writers found',nled)

    # New serial-burnable calibration records follow the five existing IAC
    # bytes in page 9; 6 * 7 = 42 bytes, offsets 118..159 (<189).
    # Only JS2 (index 3) starts in mode 4 / preserved fan hysteresis.
    anchor='ms15_max_lo_f:    db    64T'
    assert result.count(anchor)==1
    records=['; Six programmable output records, page 9 offsets 118..159.']
    pins=('led17','led18','led19','js2','js3','fidle')
    fields=('mode','src_a','on_a','off_a','src_b','on_b','off_b')
    for n,pin in enumerate(pins):
        for field in fields:
            val=4 if n==3 and field=='mode' else 0
            records.append(f'ms15_out{n}_{field}_f: db    {val}T  ; {pin}')
    assert len(records)==43
    result=result.replace(anchor,anchor+eol+eol+eol.join(records))
    assert 'include "ms15_iac.inc"' in result
    # Source-only checks run on fully integrated firmware; never assemble.
    return result


def transform(original: str) -> str:
    return transform_integrated(initial_fuel_only(original))


def main() -> None:
    if len(sys.argv)!=2:
        raise SystemExit('Usage: finalize_ms15_fuel_only.py /path/to/fully-patched/msns-extra.asm')
    path=Path(sys.argv[1])
    raw=path.read_bytes()
    result=transform_integrated(raw.decode('latin-1'))
    path.write_bytes(result.encode('latin-1'))
    print('SOURCE ONLY: post-ignition removal cleanup complete; UNBUILT')

if __name__=='__main__': main()