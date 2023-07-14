import unittest

from media_management_scripts.support import formatting


class FormattingTestCase(unittest.TestCase):
    def test_duration_from_str(self):
        self.assertAlmostEqual(1, formatting.duration_from_str("1s"))
        self.assertAlmostEqual(1.5, formatting.duration_from_str("1.5s"))
        self.assertAlmostEqual(61, formatting.duration_from_str("1m1s"))
        self.assertAlmostEqual(1, formatting.duration_from_str("00m1s"))
        self.assertAlmostEqual(3601, formatting.duration_from_str("1h00m1s"))
        self.assertAlmostEqual(3790, formatting.duration_from_str("1h3m10s"))
        self.assertAlmostEqual(3790.01, formatting.duration_from_str("1h3m10.01s"))
