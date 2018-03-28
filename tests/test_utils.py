import unittest

from media_management_scripts import utils
from media_management_scripts.support.episode_finder import extract
from tests import create_test_video
import os
from media_management_scripts.commands.metadata import print_metadata


class UtilsTestCase(unittest.TestCase):
    def test_compare_gt(self):
        self.assertEqual(0, utils.compare_gt(0, 0))
        self.assertEqual(1, utils.compare_gt(0, -1))
        self.assertEqual(-1, utils.compare_gt(1, None))
        self.assertEqual(1, utils.compare_gt(None, 1))

    def test_compare_lt(self):
        self.assertEqual(0, utils.compare_lt(0, 0))
        self.assertEqual(-1, utils.compare_lt(0, -1))
        self.assertEqual(1, utils.compare_lt(1, None))
        self.assertEqual(-1, utils.compare_lt(None, 1))


class EpisodeFinderTestCase(unittest.TestCase):
    def test(self):
        test_strs = {'S01E13': ('01', '13', None),
                     's01e03': ('01', '03', None),
                     's1e03': ('1', '03', None),
                     'Series 1, Episode 14': ('1', '14', None),
                     'Series 12, Episode 14': ('12', '14', None),
                     'Series2, Episode 14': ('2', '14', None),
                     'Pointless Series 7 Episode 69 Part 1': ('7', '69', '1'),
                     'Show 2x06': ('2', '06', None),
                     'XFM The Ricky Gervais Show Series 1 Episode 23 - Karl\'s Room 101-liag2szq7Eg': ('1', '23', None),
                     'Room 101 S01E01 - Bob Monkhouse-5Xw-KJojVeA': ('01', '01', None),
                     'TEFL commute season 4 episode 4 - room 101-_ASgSRU_w-Y': ('4', '4', None),
                     '_ Season 3, “Episode” 6': ('3', '6', None),
                     'Journeys [S03E20]  -': ('03', '20', None),
                     'Journeys S3E19 - Los': ('3', '19', None)
                     }
        for key in test_strs:
            result = extract(key)
            self.assertEqual(test_strs[key], result)

    def test_101(self):
        self.assertEqual(extract('Test 101.mp4', use101=False), (None, None, None))
        self.assertEqual(extract('Test 101.mp4', use101=True), ('1', '01', None))


class TestFileTestCase(unittest.TestCase):
    def test(self):
        with create_test_video(length=5) as file:
            self.assertTrue(os.path.isfile(file.name))
