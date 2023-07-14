import unittest
from media_management_scripts.support.episode_finder import (
    EpisodePart,
    calculate_new_filenames,
    extract,
)


class ExtractTestCase(unittest.TestCase):
    def assertExtract(
        self, test_str, expected_season, expected_episode, expected_part, use101=False
    ):
        season, ep, part = extract(test_str, use101=use101)

        self.assertEqual(season, expected_season)
        self.assertEqual(expected_episode, ep)
        self.assertEqual(expected_part, part)

    def test_extract(self):
        self.assertExtract("S01E01.mp4", 1, 1, None)
        self.assertExtract("S3E201.mp4", 3, 201, None)
        self.assertExtract("Something - S01E01 - Name.mp4", 1, 1, None)
        self.assertExtract("S01E01.mp4", 1, 1, None)

    def test_extract_101(self):
        self.assertExtract("101.mp4", None, None, None, use101=False)
        self.assertExtract("101.mp4", 1, 1, None, use101=True)

        self.assertExtract("206.mp4", None, None, None, use101=False)
        self.assertExtract("206.mp4", 2, 6, None, use101=True)

    def test_extract2(self):
        self.assertExtract("2x06.mp4", 2, 6, None)
        self.assertExtract("season 3 episode 555.mp4", 3, 555, None)
        self.assertExtract("Season 3 Episode 555.mp4", 3, 555, None)
        self.assertExtract("Season 03 episode 05.mp4", 3, 5, None)
        self.assertExtract("Series 03 Episode 05.mp4", 3, 5, None)
        self.assertExtract("series 03 episode 05.mp4", 3, 5, None)

    def test_extract_part(self):
        self.assertExtract("S01E01 part 1.mp4", 1, 1, 1)
        self.assertExtract("S01E01 pt2.mp4", 1, 1, 2)


class RenameTestCase(unittest.TestCase):
    def test_rename(self):
        name = "Test"
        path = "Test.mp4"
        season = 1
        episode = 1
        part = None
        episodes = [EpisodePart(name, path, season, episode, part)]

        source, season_episode, dest = next(
            calculate_new_filenames(
                episodes, output_dir="", use_season_folders=False, show_name=None
            )
        )
        self.assertEqual(path, source)
        self.assertEqual(dest, "S01E01 - Test.mp4")

    def test_rename_output_dir(self):
        name = "Test"
        path = "Test.mp4"
        season = 1
        episode = 1
        part = None
        episodes = [EpisodePart(name, path, season, episode, part)]

        output_dir = "output"

        source, season_episode, dest = next(
            calculate_new_filenames(
                episodes,
                output_dir=output_dir,
                use_season_folders=False,
                show_name=None,
            )
        )
        self.assertEqual(path, source)
        self.assertEqual(dest, output_dir + "/S01E01 - Test.mp4")

    def test_rename_with_season(self):
        name = "Test"
        path = "Test.mp4"
        season = 1
        episode = 1
        part = None
        episodes = [EpisodePart(name, path, season, episode, part)]

        source, season_episode, dest = next(
            calculate_new_filenames(
                episodes, output_dir="", use_season_folders=True, show_name=None
            )
        )
        self.assertEqual(path, source)
        self.assertEqual("Season 01/S01E01 - Test.mp4", dest)

    def test_rename_with_show(self):
        name = "Test"
        path = "Test.mp4"
        season = 1
        episode = 1
        part = None
        episodes = [EpisodePart(name, path, season, episode, part)]

        show_name = "Show Name"

        source, season_episode, dest = next(
            calculate_new_filenames(
                episodes, output_dir="", use_season_folders=False, show_name=show_name
            )
        )
        self.assertEqual(path, source)
        self.assertEqual(show_name + "/" + show_name + " - S01E01 - Test.mp4", dest)

    def test_rename_with_show_and_season(self):
        name = "Test"
        path = "Test.mp4"
        season = 1
        episode = 1
        part = None
        episodes = [EpisodePart(name, path, season, episode, part)]

        show_name = "Show Name"

        source, season_episode, dest = next(
            calculate_new_filenames(
                episodes, output_dir="", use_season_folders=True, show_name=show_name
            )
        )
        self.assertEqual(path, source)
        self.assertEqual(
            show_name + "/Season 01/" + show_name + " - S01E01 - Test.mp4", dest
        )
