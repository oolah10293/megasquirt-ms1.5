"""SOURCE-ONLY end-to-end tests. Does not compile or emit any firmware.

The integrated test requires the complete patched 029y4a source and tuning INI.
CI must supply these explicitly via the environment. Baseline transform-only tests
remain useful locally but may not stand in for integrated-source verification.
"""
import hashlib
import os
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from remove_ms15_ignition_full import transform as remove_ignition
from finalize_ms15_fuel_only import transform_integrated as finish_source
from simplify_ms15_fuel_only_ini import transform as hide_old_menus
from finalize_ms15_fuel_only_ini import transform_integrated as finish_ini

ASM_SHA='a80d055ebed3349c7bc3541a7d1c63c824bed85d290c41638cd659f63aa9e928'
ORIGINAL_ZIP=Path(os.environ.get('MS15_ORIGINAL_ZIP','/mnt/data/029y4a(1).zip'))
INTEGRATED_ASM=os.environ.get('MS15_INTEGRATED_ASM')
INTEGRATED_INI=os.environ.get('MS15_INTEGRATED_INI')


def cleaned_source(body):
    return '\n'.join(c for x in body.splitlines() if (c:=x.split(';',1)[0].strip()) and not c.startswith('*'))


def symbols(body):
    found=set()
    for line in cleaned_source(body).splitlines():
        for pattern in (r'^([A-Za-z_]\w*):',r'^([A-Za-z_]\w*)\s+(?:equ|rmb|ds|db|dw|=|set|macro)\b',r'^\$MACRO\s+([A-Za-z_]\w*)'):
            m=re.match(pattern,line,re.I)
            if m:
                found.add(m.group(1).lower()); break
    return found


class FinalSourceOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ORIGINAL_ZIP) as archive:
            names=[s for s in archive.namelist() if s.endswith('/src/msns-extra.asm')]
            assert len(names)==1,names
            upstream=archive.read(names[0])
        assert hashlib.sha256(upstream).hexdigest()==ASM_SHA
        cls.original=upstream.decode('latin-1')
        cls.full=remove_ignition(cls.original)
        cls.cleaned=finish_source(cls.full)
        # Both integrated env variables are mandatory when CI asks for them;
        # running on the original alone must not be mistaken for integration.
        if bool(INTEGRATED_ASM)!=bool(INTEGRATED_INI):
            raise AssertionError('Provide BOTH MS15_INTEGRATED_ASM and MS15_INTEGRATED_INI')
        if os.environ.get('MS15_REQUIRE_INTEGRATED')=='1' and not INTEGRATED_ASM:
            raise AssertionError('Integrated firmware required in this test run')
        if INTEGRATED_ASM:
            original_integrated=Path(INTEGRATED_ASM).read_bytes().decode('latin-1')
            cls.integrated=finish_source(remove_ignition(original_integrated))
            cls.integrated_ini=finish_ini(hide_old_menus(Path(INTEGRATED_INI).read_bytes().decode('latin-1')))
        else:
            cls.integrated=None
            cls.integrated_ini=None

    def test_physical_removal_of_execution(self):
        a=cleaned_source(self.cleaned)
        for label in ('spark_lookup','SPARKTIME','misc_spark','turnallsparkoff','Knock_Detection','EnableN2O','doBoostControl','CheckBoost','traction','error_vector','config_error1','Water_Injection','CYCLE_CALC'):
            self.assertNotRegex(a,rf'(?im)^{re.escape(label)}:',label)
        for name in ('T2SC1','T2CH1H','T2CH1L'):
            lines=[x for x in a.splitlines() if re.search(r'\b'+name+r'\b',x,re.I)]
            self.assertFalse(any(re.search(r'\b(?:bset|enable|mov\s+#.*TOIE)\b',x,re.I) for x in lines),lines)
        self.assertRegex(a,r'(?im)^\s*dw\s+Dummy\s*$')
        self.assertNotRegex(a,r'(?im)\b(?:COILNEG|COILPOS|TurnAllSpkOff|SparkTrigg)\b')
        self.assertNotRegex(a,r'(?im)^\s*brset\s+config_error,feature2,(?:config_er1JMP|error_exit)\b')
        self.assertNotIn('brset    water,porta,SKIP_ALL_O2',a)

    def test_fuel_paths_and_advanced_features_preserved(self):
        a=cleaned_source(self.cleaned)
        for label in ('CalcRPM','VE1_LOOKUP','VE2_LOOKUP','TIMERROLL','INJ_FIRE_CTL','DOSQUIRT','squirtCheck1','AFR1_Targets','AFR2_Targets','IdleAdjust','DO_FAN_Check','FAN_ON','FAN_OFF','IN_SCI_RCV','Check_VE3_Table','CheckSoftLimit'):
            self.assertRegex(a,rf'(?im)^{re.escape(label)}:',label)
        for field in ('pwcalc1','pwcalc2','pw_staged','pw_staged2','OverRun','RevLimit_f','SRevLimRPM','SRevLimHTime','SRevLimTimeLeft','EfanOnTemp_f','EfanOffTemp_f'):
            self.assertRegex(a,rf'(?i)\b{re.escape(field)}\b')
        self.assertRegex(a,r'(?i)bset\s+config_error,feature2\s*\n\s*jmp\s+FAN_ON')
        self.assertRegex(a,r'(?i)bclr\s+config_error,feature2')
        # Expected original-only FAN writers remain in *unpatched* upstream.
        # The complete integrated assembly is tested independently below.

    def test_no_remaining_nitrous_spark_delay_or_unsafe_output3(self):
        a=cleaned_source(self.cleaned)
        for forbidden in (r'^\s*add\s+NosPW\b',
                          r'^\s*brset\s+out3sparkd,',
                          r'^\s*bclr\s+Output3,portd',
                          r'^\s*inc\s+Out3Timer\b',
                          r'^\s*lda\s+Spark2Delay_f\b',
                          r'^\s*sta\s+ST2Timer\b',
                          r'^\s*sthx\s+dwelldelay[1-6]\b',
                          r'^\s*sta\s+(?:NosPW|NitrousAngle)\b'):
            self.assertNotRegex(a,r'(?im)'+forbidden,forbidden)
        # VE3 is a FUEL-table switch, not a spark-table switch. Its delay
        # is still used by VE3_Table and deliberately retained.
        for token in ('VE3Timer','VE3Delay_f','Check_VE3_Table','NosDcOk',
                      'MS15_PrimeCount'):
            self.assertRegex(a,r'(?i)\b'+token+r'\b')
        self.assertRegex(a,r'(?im)^MS15_PrimeCount\s+equ\s+TCSparkCut\b')
        self.assertNotRegex(a,r'(?im)^\s*(?:lda|sta|inc|clr|dec)\s+TCSparkCut\b')
        # The source no longer defines any dead dwell/spark helper aliases.
        for old in ('dwelltmpX','dwelltmpH','dwelltmpL','SparkdltX',
                    'SparkdltH','SparkdltL'):
            self.assertNotRegex(a,rf'(?im)^\s*{old}\s+equ\b')
        # The legacy bit's active use is extra cranking fuel only.
        self.assertRegex(a,r'(?im)^MS15_ExtraCrankGate\s+equ\s+NosDcOk\b')
        self.assertNotRegex(a,r'(?im)^\s*(?:brclr|brset|bset|bclr)\s+NosDcOk\b')
        self.assertRegex(a,r'(?im)^\s*bset\s+MS15_ExtraCrankGate,EnhancedBits\b')
        self.assertRegex(a,r'(?im)^\s*bclr\s+MS15_ExtraCrankGate,EnhancedBits\b')
        # Retain fixed-zero old telemetry slots without any live ignition code.
        for old in ('SparkAngle','KnockAngle','CltIatAngle'):
            self.assertRegex(a,r'(?im)^\s*sta\s+'+old+r'\b')

    def test_ve3_disable_clears_latched_fuel_table_selection(self):
        # If a tune disables VE3 after an input previously selected it,
        # stale UseVE3 must not keep changing which fuel/AFR map is active.
        for body in (self.cleaned, self.integrated):
            if body is None: continue
            src=cleaned_source(body)
            self.assertRegex(
                src,
                r'(?is)Prime_Checked:\s+lda\s+feature6_f\s+bit\s+#VETable3b'
                r'\s+bne\s+MS15_CHECK_VE3_OPTION\s+bclr\s+UseVE3,EnhancedBits'
                r'\s+bra\s+No_VE_Table_3\s+MS15_CHECK_VE3_OPTION:'
                r'\s+jsr\s+Check_VE3_Table')
            # Physical table switch input retains fuel-only selection role.
            self.assertRegex(src, r'(?i)Check_VE3_Table:\s+brset\s+NosIn,portd,MS15_VE3_OFF')

    def test_help_excludes_retired_ignition_and_racing_features(self):
        if not INTEGRATED_INI:
            self.skipTest('Requires the integrated, matching TunerStudio INI')
        ini=self.integrated_ini
        for retired in ('Fhelp4','Fhelp5','Shelp1','Shelp2','Shelp3','Shelp4',
                        'Shelp5','Chelp1','Chelp4','Chelp5','TachoHelp',
                        'DwellHelp','Stim4WHelp'):
            self.assertNotRegex(ini,rf'(?im)^\s*help\s*=\s*{retired}\s*,')
            self.assertNotRegex(ini,rf'(?im)^\s*subMenu\s*=\s*{retired}\b')
        for token in ('help = Fhelp1, "MegaSquirt MS1.5 Fuel-Only"',
                      'help = Fhelp2, "Fuel Table Selection"',
                      'help = Fhelp7, "Fuel Rev Limiter"',
                      'help = Chelp2, "Advanced Fuel Configuration"'):
            self.assertIn(token,ini)
        # Help must describe actual fuel-only rev limiting and VE3 operation.
        self.assertIn('soft delay counts in 0.1 second ticks',ini.lower())
        self.assertIn('table-select input goes low',ini)

    def test_dashboard_choices_use_real_output_channels(self):
        # Source-only INI check: 13 default ECU indicators plus TunerStudio's
        # own application states, with additional right-click-only choices.
        if not INTEGRATED_INI:
            self.skipTest('Requires matching integrated TunerStudio INI')
        front=self.integrated_ini.split('[FrontPage]',1)[1].split('[RunTime]',1)[0]
        defaults=re.findall(r'(?im)^\s*indicator\s*=',front)
        optional=re.findall(r'(?im)^\s*indicatorTemplate\s*=',front)
        self.assertEqual(len(defaults),13)
        self.assertEqual(len(optional),5)
        expected={
            'Fuel Pump ON':'porta & 0b00000001',
            'JS0 STEP high':'porta & 0b00100000',
            'JS1 DIR=1':'porta & 0b00010000',
            'JS2 Fan cmd high':'porta & 0b00001000',
            'JS3 cmd high':'porta & 0b00000100',
            'FIDLE cmd high':'porta & 0b00000010',
            'LED17 high':'portc & 0b00000001',
            'LED18 high':'portc & 0b00000100',
            'LED19 high':'portc & 0b00000010',
            'Engine running':'engine & 0b00000001',
            'Cranking':'engine & 0b00000010',
            'Config ERROR':'portc & 0b10000000',
            'FLOOD CLEAR':'floodclear && (( engine & 3 ) != 1)',
        }
        for label,expr in expected.items():
            self.assertIn('{ '+expr+' }',front,label)
            self.assertIn('"'+label+'"',front,label)
        for retired in ('Output3 On','Launch On','Knocked','NOS/Tables On',
                        'Fidle/Spark'):
            self.assertNotIn(retired,front,retired)
        for template in ('Afterstart enrich','Warmup enrich','TPS accel ON',
                         'TPS decel ON','MAP accel ON'):
            self.assertIn('"'+template+'"',front,template)
        # Not Connected, Data Logging and Protocol Error are TunerStudio
        # application states, not fake ECU status bits.
        for native in ('Not Connected','Data Logging','Protocol Error'):
            self.assertNotIn('"'+native+'"',front)

    def test_native_led_events_and_startup_defaults(self):
        if not INTEGRATED_ASM:
            self.skipTest('Requires complete MS1.5 output integration')
        a=cleaned_source(self.integrated)
        configs=(5,6,7,4,0,0)
        for idx,mode in enumerate(configs):
            self.assertRegex(a,r'(?im)^ms15_out'+str(idx)+r'_mode_f:\s*db\s+'+str(mode)+r'T')
        # Out-of-line IRQ handlers avoid HC08 relative-branch overflows and
        # return by absolute JMP, not stack calls. Real injector event timing
        # is still observed directly by each selected LED.
        for start,stop,event in (
            ('NEW_SQUIRT1:','nsq1:','ON1'),
            ('NEW_SQUIRT2:','nsq2:','ON2'),
            ('CHECK_RPM:','CHK_RE_ENABLE:','OFF'),
        ):
            block=a.split(start,1)[1].split(stop,1)[0]
            self.assertRegex(block,r'(?is)jmp\s+MS15_IL_'+event+
                             r'\s+ILE_RET_'+event+r':')
        for pin in ('sled','wled','aled'):
            self.assertNotRegex(a,r'(?im)^\s*bset\s+'+pin+r',portc\b')
            self.assertNotRegex(a,r'(?im)^\s*bclr\s+'+pin+r',portc\b')
        choices=self.integrated_ini
        for idx in range(3):
            self.assertIn('"Squirt (injector activity)"',choices)
            self.assertIn('"Warmup enrichment"',choices)
            self.assertIn('"Acceleration enrichment"',choices)
        module=(Path(INTEGRATED_ASM).parent/'ms15_outputs.inc').read_text()
        for flag in ('firing1,squirt','firing2,squirt','warmup,engine','TPSAEN,engine'):
            self.assertIn(flag,module)
        for event,on in (('ON1',True),('ON2',True),('OFF',False)):
            block=module.split('MS15_IL_'+event+':',1)[1].split(
                'jmp     ILE_RET_'+event,1)[0]
            self.assertRegex(block,r'(?is)psha\s+tpa\s+psha')
            self.assertRegex(block,r'(?is)pula\s+tap\s+pula')
            for idx,pin in enumerate(('sled','wled','aled')):
                instruction='bset' if on else 'bclr'
                self.assertRegex(block,
                    r'(?is)lda\s+ms15_out'+str(idx)+r'_mode_f\s+'
                    r'cmp\s+#5T\s+bne\s+IL_'+event+'_'+str(idx)+r'\s+'
                    +instruction+r'\s+'+pin+r',portc\s+IL_'+event+'_'+str(idx)+r':')
        for pin in ('sled','wled','aled'):
            self.assertEqual(len(re.findall(r'(?im)^\s*bset\s+'+pin+r',portc\b',module)),2)
            self.assertEqual(len(re.findall(r'(?im)^\s*bclr\s+'+pin+r',portc\b',module)),1)

    def test_all_remaining_legacy_runtime_identifiers_are_accounted_for(self):
        # Audit the *entire integrated* assembly, not a handful of snippets.
        # Historical flash DB/equ fields are deliberately kept in-place for
        # older tune compatibility; actual instructions must be an exact
        # allow-list of harmless placeholders and the VE3 fuel input.
        src=cleaned_source(self.integrated or self.cleaned)
        suspicious=re.compile(
            r'\b(?:spark\w*|coil\w*|dwell\w*|knock\w*|launch\w*'
            r'|nitrous\w*|nos\w*|boost\w*|tract\w*'
            r'|shiftlight\w*|T2SC1|T2CH1\w*)\b',re.I)
        allowed={
            'bset nosin,ptdpue',              # VE3 input pull-up
            'brset nosin,portd,ms15_ve3_off', # VE3 input only
            'mov #%00010000,t2sc1',         # disable compare output
            'bclr toie,t2sc1',              # disable compare interrupt
            'sta sparkangle',               # zero serial telemetry
            'sta knockangle',               # zero serial telemetry
        }
        live=[]
        for line in src.splitlines():
            if not suspicious.search(line):continue
            if line.endswith(':'):continue
            if re.search(r'\b(?:equ|db|dw|ds|rmb)\b',line,re.I):continue
            live.append(' '.join(line.lower().split()))
        self.assertEqual(set(live),allowed,live)
        self.assertEqual(len(live),len(allowed),live)

    def test_no_dangling_original_labels(self):
        prior=symbols(self.full)
        deleted=prior-symbols(self.cleaned)
        allowed={'stx'}
        for n,line in enumerate(cleaned_source(self.cleaned).splitlines(),1):
            if not line or line.startswith('*'):continue
            words={w.lower() for w in re.findall(r'\b[A-Za-z_]\w*\b',line)}
            self.assertFalse((words&deleted)-allowed,(n,line,words&deleted))

    def test_reapplication_is_rejected(self):
        with self.assertRaises(AssertionError):
            finish_source(self.cleaned)

    def test_integrated_source_and_ini(self):
        if not INTEGRATED_ASM: self.skipTest('Run with integrated firmware to activate end-to-end tests')
        a=cleaned_source(self.integrated)
        ini=self.integrated_ini
        # The STEP/DIR routine is intentionally included from a separate
        # assembly file; it is NOT defined inline in msns-extra.asm.
        iac=Path(INTEGRATED_ASM).parent/'ms15_iac.inc'
        self.assertIn('MS15_IAC_SERVICE:',iac.read_text(encoding='latin-1'))
        for key in ('MS15_TICK','ms15_step_low_f','ms15_home_hi_f','ms15_max_hi_f'):
            self.assertIn(key.lower(),self.integrated.lower(),key)
        for marker in ('include "ms15_iac.inc"','include "ms15_defs.inc"'):
            self.assertIn(marker,a)
        # The installed fan uses only JS2 output1, never pre-existing water/NOS pins.
        w=re.findall(r'(?im)^\s*(bset|bclr)\s+(water2|water|output1),porta\b',a)
        self.assertEqual(set((x.lower(),y.lower()) for x,y in w),{('bset','output1'),('bclr','output1')},w)
        self.assertEqual(len(w),2,w)
        self.assertNotRegex(a,r'(?im)^\s*brset\s+config_error,feature2\b')
        self.assertRegex(a,r'(?im)^\s*bset\s+config_error,feature2\b')
        for marker in ('subMenu = idleControl','subMenu = ms15FanControl','subMenu = veTable1Tbl','subMenu = veTable2Tbl','subMenu = afrTable1Tbl','subMenu = afrTable2Tbl','subMenu = RevLimiterS'):
            self.assertIn(marker,ini,marker)
        self.assertIn('MS1/Extra format MS15_003 ******',ini)
        for forbidden in ('dialog = sparkSettings,','dialog = knock,','dialog = NosSystem,','dialog = launchSettings,','dialog = boostControl,'):
            self.assertNotIn(forbidden,ini)
        self.assertIn('Table-select input low',ini)
        pre=Path(INTEGRATED_ASM).read_bytes().decode('latin-1')
        deleted=symbols(pre)-symbols(self.integrated)
        for n,line in enumerate(cleaned_source(self.integrated).splitlines(),1):
            if not line:continue
            words={word.lower() for word in re.findall(r'\b[A-Za-z_]\w*\b',line)}
            self.assertFalse((words&deleted)-{'stx'},(n,line,words&deleted))

if __name__=='__main__':unittest.main()