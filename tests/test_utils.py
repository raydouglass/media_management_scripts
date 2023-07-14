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


class TestFileTestCase(unittest.TestCase):
    def test(self):
        with create_test_video(length=5) as file:
            self.assertTrue(os.path.isfile(file.name))
