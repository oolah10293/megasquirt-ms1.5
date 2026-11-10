"""Source-only tests against an exact 029y4a ZIP; no build or flash."""
import hashlib
import os
from pathlib import Path
import re
import sys
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from remove_ms15_ignition_stage1 import transform

SOURCE_SHA = 'a80d055ebed3349c7bc3541a7d1c63c824bed85d290c41638cd659f63aa9e928'


class Stage1SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        archive = os.environ.get('MS15_ORIGINAL_ZIP')
        if not archive:
            raise unittest.SkipTest(
                'Set MS15_ORIGINAL_ZIP to exact original 029y4a ZIP for source-only tests')
        with ZipFile(archive) as z:
            source = z.read('029y4a/src/msns-extra.asm')
        if hashlib.sha256(source).hexdigest() != SOURCE_SHA:
            raise AssertionError('029y4a assembly does not match independently audited source SHA')
        cls.source = source.decode('latin-1')

    def test_removes_spark_lookup_and_ignition_checks(self):
        changed = transform(self.source)
        for removed in ('spark_lookup:', 'STTABLELOOKUP:', 'check_msns:', 'check10:'):
            self.assertNotIn(removed, changed)
        for kept in ('CheckSoftLimit:', 'ms15_check_nitrous:', 'ms15_checks_done:',
                     'mov     #5,tmp4', 'mov     #6,tmp4'):
            self.assertIn(kept, changed)

    def test_preserves_shared_fuel_rpm_and_serial_code(self):
        changed = transform(self.source)
        for retained in ('DOSQUIRT:', 'TIMERROLL:', 'CheckSoftLimit:', 'CheckOutputs:',
                         'start_adc:', 'MODE_B:', 'AFR1_Targets:', 'turnallsparkoff:'):
            self.assertIn(retained, changed)
        self.assertIn('jmp     CheckSoftLimit', changed)
        self.assertEqual(len(self.source.splitlines()) - len(changed.splitlines()), 628)
        self.assertEqual(len(self.source) - len(changed), 19529)
        self.assertEqual(len(re.findall(r'(?mi)^\s*(?:jmp|bra)\s+CheckSoftLimit\b', changed)), 3)

    def test_rejects_unexpected_deleted_label_consumer(self):
        mutated = self.source.replace('jmp     spark_lookup', 'jmp     STTABLELOOKUP', 1)
        with self.assertRaises(AssertionError):
            transform(mutated)

    def test_rejects_missing_fuel_entry(self):
        mutated = self.source.replace('bra       spark_lookup', 'bra       CheckSoftLimit', 1)
        with self.assertRaises(AssertionError):
            transform(mutated)

    def test_rejects_double_application(self):
        changed = transform(self.source)
        with self.assertRaises(AssertionError):
            transform(changed)


if __name__ == '__main__':
    unittest.main()
