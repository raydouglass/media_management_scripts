import unittest

from media_management_scripts import utils
from media_management_scripts.support.episode_finder import extract
from tests import create_test_video
import os
from media_management_scripts.print_metadata import print_metadata


class UtilsTestCase(unittest.TestCase):
    def test_compare_gt(self):
        self.assertTrue(utils.compare_gt(0, -1))
        self.assertTrue(utils.compare_gt(1, None))
        self.assertFalse(utils.compare_gt(None, 1))

    def test_compare_lt(self):
        self.assertFalse(utils.compare_lt(0, -1))
        self.assertFalse(utils.compare_lt(1, None))
        self.assertTrue(utils.compare_lt(None, 1))


class EpisodeFinderTestCase(unittest.TestCase):
    def test(self):
        test_strs = {'S01E13': ('01', '13', None),
                     's01e03': ('01', '03', None),
                     's1e03': ('1', '03', None),
                     'Series 1, Episode 14': ('1', '14', None),
                     'Series 12, Episode 14': ('12', '14', None),
                     'Series2, Episode 14': ('2', '14', None),
                     'Pointless Series 7 Episode 69 Part 1.mp4': ('7', '69', '1')
                     }
        for key in test_strs:
            result = extract(key)
            self.assertEquals(test_strs[key], result)


class TestFileTestCase(unittest.TestCase):
    def test(self):
        with create_test_video(length=5) as file:
            self.assertTrue(os.path.isfile(file.name))
            print_metadata(file.name)
