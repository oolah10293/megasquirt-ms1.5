#!/usr/bin/env python3
"""Self-contained source-only tests; no assembler, downloads or hardware."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from apply_ms15_fuel_only import transform

BASELINE = '''; simplified source fixture from Nov. 9 assembler listing
        lda     outputpins_f
        sta     outputpins
        lda     personality_f
        sta     personality               ;move from flash to ram
spark_lookup:
        lda     personality_f   ; Are we using a spark mode?
        beq     No_Personality
No_Personality:
        jmp     CheckSoftLimit
nospkoff:
        lda    personality_f
        beq    No_misc_Spark
No_misc_Spark:
        sei
check_msns:
        brclr   MSNS,personality,check3
        brset   REUSE_FIDLE,outputpins,check3
        brset   REUSE_LED17,outputpins,check3
        mov     #3,tmp4
        bset    config_error,feature2
        jmp     done_checks
check3:   ; check for idle conflict
        lda     feature13_f
        bit     #pwmidleb
        beq     check4
check4:
        lda     feature3_f
check10:
        clra
        brclr   MSNS,personality,check10a
check10a:
        brclr   MSNEON,personality,check10b
        bra     done_checks
; page-0 burn refresh
        lda     outputpins_f
        sta     outputpins
        lda     personality_f
        sta     personality              ; move from flash to ram
'''

class FuelOnlyTests(unittest.TestCase):
    def test_modes_forced_off_and_checks_preserved(self):
        changed = transform(BASELINE)
        self.assertEqual(changed.count('clr     personality'), 2)
        self.assertNotIn('lda     personality_f', changed)
        self.assertIn('spark_lookup:\n        lda     personality', changed)
        self.assertIn('nospkoff:\n        lda    personality', changed)
        self.assertIn('brclr   MSNS,personality,check3', changed)
        self.assertIn('bset    config_error,feature2', changed)
        self.assertIn('brclr   MSNS,personality,check10a', changed)

    def test_fails_if_page_zero_burn_path_is_missing(self):
        shorter = BASELINE.rsplit('        lda     outputpins_f', 1)[0]
        with self.assertRaises(AssertionError):
            transform(shorter)

    def test_fails_if_extra_flash_personality_read_exists(self):
        with self.assertRaises(AssertionError):
            transform(BASELINE+'        lda personality_f\n')

    def test_preserves_crlf(self):
        src = BASELINE.replace('\n','\r\n')
        result = transform(src)
        self.assertEqual(result.count('\r\n'), result.count('\n'))
        self.assertEqual(result.count('clr     personality'), 2)

if __name__ == '__main__':
    unittest.main()
