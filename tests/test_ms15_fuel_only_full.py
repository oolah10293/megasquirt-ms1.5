"""No-assembler regression tests for dedicated 029y4a-based fuel-only MS1.5."""
import hashlib
import os
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from remove_ms15_ignition_full import transform as strip_ignition
from simplify_ms15_fuel_only_ini import transform as clean_ini

EXPECTED_ASM_SHA='a80d055ebed3349c7bc3541a7d1c63c824bed85d290c41638cd659f63aa9e928'
ORIGINAL_ZIP=Path(os.environ.get('MS15_ORIGINAL_ZIP','/mnt/data/029y4a(1).zip'))

class FuelOnlyFirmwareSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ORIGINAL_ZIP) as z:
            candidates=[n for n in z.namelist() if n.endswith('/src/msns-extra.asm')]
            assert len(candidates)==1, candidates
            original=z.read(candidates[0])
        if hashlib.sha256(original).hexdigest()!=EXPECTED_ASM_SHA:
            raise AssertionError('Original source changed; refusing unreviewed deletion')
        cls.original=original.decode('latin-1')
        cls.result=strip_ignition(cls.original)

    def test_no_coil_timing_or_ignition_configuration_restrictions(self):
        for name in ('spark_lookup:','SPARKTIME:','misc_spark:',
                     'check_msns:','CYCLE_CALC:','$MACRO TurnAllSpkOff'):
            self.assertNotRegex(self.result, r'(?im)^'+re.escape(name)+r'$')
        self.assertNotRegex(self.result, r'(?im)^\s*bset\s+TOIE,T2SC1\b')
        self.assertNotRegex(self.result, r'(?im)^\s*bset\s+config_error,feature2\b')
        self.assertRegex(self.result, r'(?im)^\s*dw\s+Dummy\s*; TIM2 Ch1')
        self.assertNotRegex(self.result, r'(?im)^\s*(?:COILNEG|COILPOS|TurnAllSpkOff)\b')

    def test_critical_fuel_idle_and_afr_paths_preserved(self):
        for marker in ('CalcRPM:', 'VE1_LOOKUP:', 'VE2_LOOKUP:', 'INJ_FIRE_CTL:',
                       'squirtCheck1:','TIMERROLL:','DOSQUIRT:',
                       'AFR1_Targets:','AFR2_Targets:', 'Normal_ADSEL:',
                       'CalcRunningParameters:','No_FANOn_Porta:',
                       'SKIP_ALL_O2:'):
            self.assertTrue(re.search(re.escape(marker),self.result,re.I), marker)
        # Fuel-only interrupt still samples 24-bit high resolution periods.
        self.assertIn('mov     iTimeX,iTimepX',self.result)
        self.assertIn('sta     iTimeH',self.result)
        self.assertIn('sta     iTimeL',self.result)
        self.assertIn('jmp     squirtCheck1',self.result)
        # T2CurrX is in extended RAM, so direct INC cannot reach it.
        self.assertNotRegex(self.result, r'(?im)^\s*inc\s+T2CurrX\b')
        self.assertRegex(self.result, r'(?im)^\s*lda\s+T2CurrX\s+add\s+#1\s+sta\s+T2CurrX\b')
        # Extended RAM idle and staged-fuel counters cannot use direct INC/DEC.
        self.assertNotRegex(self.result, r'(?im)^\s*dec\s+idleDelayClock\b')
        self.assertNotRegex(self.result, r'(?im)^\s*inc\s+stgTransitionCnt\b')
        self.assertRegex(self.result, r'(?im)^\s*deca\s+sta\s+idleDelayClock\b')
        self.assertRegex(self.result, r'(?im)^\s*lda\s+stgTransitionCnt\s+inca\s+sta\s+stgTransitionCnt\b')
        for suffix in 'XHL':
            self.assertNotRegex(self.result, rf'(?im)^\s*mov\s+T2Curr{suffix},')
            self.assertRegex(self.result, rf'(?im)^\s*lda\s+T2Curr{suffix}\s+sta\s+T2Last{suffix}\b')
        self.assertIn('bclr    config_error,feature2',self.result)

    def test_deleted_asm_symbols_are_not_referenced(self):
        def symbols(s):
            result=set()
            for line in s.splitlines():
                code=line.split(';',1)[0]
                for pattern in (r'^\s*([A-Za-z_]\w*):',
                                r'^\s*([A-Za-z_]\w*)\s+(?:equ|rmb|ds|db|dw|=|set|macro)\b',
                                r'^\s*\$MACRO\s+([A-Za-z_]\w*)'):
                    m=re.match(pattern,code,re.I)
                    if m:result.add(m.group(1).lower());break
            return result
        removed=symbols(self.original)-symbols(self.result)
        for i,line in enumerate(self.result.splitlines(),1):
            code=line.split(';',1)[0].strip()
            if not code or code.startswith('*'):continue
            words={x.lower() for x in re.findall(r'\b[A-Za-z_]\w*\b',code)}
            self.assertFalse((words&removed)-{'stx'},(i,line,words&removed))

    def test_fail_closed_on_modified_source(self):
        with self.assertRaises(AssertionError):
            strip_ignition(self.original.replace('spark_lookup:', 'spark_lookup_old:',1))
        with self.assertRaises(AssertionError):
            strip_ignition(self.result)

    def test_tuner_studio_preserves_critical_calibration_abi(self):
        raw=Path(os.environ.get('MS15_TUNING_INI','/mnt/data/MS15_2026-11-10.ini')).read_bytes().decode('latin1')
        updated=clean_ini(raw)
        self.assertEqual(raw.split('[Constants]',1)[1].split('[Menu]',1)[0],
                         updated.split('[Constants]',1)[1].split('[Menu]',1)[0])
        for field in ('subMenu = idleControl','subMenu = ms15FanControl',
                      'subMenu = veTable1Tbl','subMenu = afrTable1Tbl',
                      'subMenu = RevLimiterS','subMenu = egoControl1'):
            self.assertIn(field,updated)
        for line in updated.splitlines():
            clean=line.strip()
            self.assertFalse(re.match(r'^subMenu\s*=\s*(sparkSettings|sparkMap|sparkTbl|codeBase|wheeldecoder|launchSettings|traction)\b',clean,re.I),clean)
        self.assertIn('MS1/Extra format MS15_002 ******',updated)

if __name__=='__main__':unittest.main()