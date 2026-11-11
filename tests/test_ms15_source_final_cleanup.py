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
        for key in ('MS15_IAC_SERVICE:', 'MS15_TICK','ms15_step_low_f','ms15_home_hi_f','ms15_max_hi_f'):
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
        self.assertIn('MS1/Extra format MS15_001 ******',ini)
        for forbidden in ('dialog = sparkSettings,','dialog = knock,','dialog = NosSystem,','dialog = launchSettings,','dialog = boostControl,'):
            self.assertNotIn(forbidden,ini)
        self.assertIn('Table-select input low',ini)

if __name__=='__main__':unittest.main()