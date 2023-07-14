import unittest

from media_management_scripts.renamer import (
    rename_process,
    rename_plex,
    PlexTemplateParams,
)


def new_names(results):
    return list(list(zip(*results))[1])


class RenameTests(unittest.TestCase):
    def test_rename(self):
        template = "${i}"
        files = ["test.mkv", "test2.mkv"]
        results = new_names(rename_process(template, files))
        self.assertEqual(["1", "2"], results)

    def test_function(self):
        template = "${i | zpad}"
        files = ["test.mkv", "test2.mkv"]
        results = new_names(rename_process(template, files))
        self.assertEqual(["01", "02"], results)

    def test_nested(self):
        template = "${lpad(zpad(i), 3)}"
        files = ["test.mkv", "test2.mkv"]
        results = new_names(rename_process(template, files))
        self.assertEqual([" 01", " 02"], results)

    def test_concat(self):
        template = "${zpad(i)+' '}"
        files = ["test.mkv", "test2.mkv"]
        results = new_names(rename_process(template, files))
        self.assertEqual(["01 ", "02 "], results)

    def test_concat2(self):
        template = '${zpad(i)+" "}'
        files = ["test.mkv", "test2.mkv"]
        results = new_names(rename_process(template, files))
        self.assertEqual(["01 ", "02 "], results)

    def test_ifempty(self):
        template = "${ifempty(var, 'test', '')}"
        files = ["test.mkv"]
        params = {"var": None}
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(["test"], results)

        template = "${ifempty(var, None, var+'test')}"
        files = ["test.mkv"]
        params = {"var": "ww"}
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(["wwtest"], results)

    def test_regex(self):
        template = "${re[1]}"
        files = ["S2", "S1"]
        regex = "S(\d)"
        results = new_names(rename_process(template, files, regex=regex))
        self.assertEqual(["2", "1"], results)

    def test_regex_missing(self):
        template = "${re[1]}"
        files = ["S2", "S"]
        regex = "S(\d)"
        with self.assertRaises(IndexError) as context:
            new_names(rename_process(template, files, regex=regex))

    def test_regex_missing_ignore(self):
        template = "${re[1]}"
        files = ["S2", "S"]
        regex = "S(\d)"
        results = new_names(
            rename_process(template, files, regex=regex, ignore_missing_regex=True)
        )
        self.assertEqual(["2", ""], results)

    def test_regex_missing_ifempty(self):
        template = '${ifempty(re[1], "Unknown", str(re[1])+" ")}'
        files = ["S2", "S"]
        regex = "S(\d)"
        results = new_names(
            rename_process(template, files, regex=regex, ignore_missing_regex=True)
        )
        self.assertEqual(["2 ", "Unknown"], results)

    def test_plex(self):
        template = "{plex}"
        files = ["file.mkv"]
        params = {
            "show": "TV Show",
            "season": 1,
            "episode_num": 2,
            "episode_name": "Episode Name",
            "episode_num_final": None,
        }
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(
            ["TV Show/Season 01/TV Show - S01E02 - Episode Name.mkv"], results
        )

        params = {
            "show": "TV Show",
            "season": 1,
            "episode_num": 2,
            "episode_name": None,
            "episode_num_final": None,
        }
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(["TV Show/Season 01/TV Show - S01E02.mkv"], results)

        template = "/Some/Path/{plex}"
        params = {
            "show": "TV Show",
            "season": 1,
            "episode_num": 2,
            "episode_name": "Episode Name",
            "episode_num_final": None,
        }
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(
            ["/Some/Path/TV Show/Season 01/TV Show - S01E02 - Episode Name.mkv"],
            results,
        )

    def test_plex_multiepisode(self):
        template = "{plex}"
        files = ["file.mkv"]
        params = {
            "show": "TV Show",
            "season": 1,
            "episode_num": 2,
            "episode_name": "Episode Name",
            "episode_num_final": 3,
        }
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(
            ["TV Show/Season 01/TV Show - S01E02-E03 - Episode Name.mkv"], results
        )

        params = {
            "show": "TV Show",
            "season": 1,
            "episode_num": 2,
            "episode_name": "Episode Name",
            "episode_num_final": 10,
        }
        results = new_names(rename_process(template, files, params=params))
        self.assertEqual(
            ["TV Show/Season 01/TV Show - S01E02-E10 - Episode Name.mkv"], results
        )

    def test_plex_params(self):
        params = PlexTemplateParams("TV Show", 1, 2, "Episode Name")
        self.assertEqual(
            "TV Show/Season 01/TV Show - S01E02 - Episode Name.mkv",
            rename_plex("file.mkv", params),
        )

        params = PlexTemplateParams("TV Show", 1, 2, "Episode Name", 3)
        self.assertEqual(
            "TV Show/Season 01/TV Show - S01E02-E03 - Episode Name.mkv",
            rename_plex("file.mkv", params),
        )

    def test_output_dir(self):
        template = "${i}"
        output_dir = "/Some/Path"
        files = ["test.mkv", "test2.mkv"]
        results = new_names(rename_process(template, files, output_dir=output_dir))
        self.assertEqual(["/Some/Path/1", "/Some/Path/2"], results)

    def test_output_dir2(self):
        template = "Path/${i}"
        output_dir = "/Some/Path"
        files = ["test.mkv", "test2.mkv"]
        results = new_names(rename_process(template, files, output_dir=output_dir))
        self.assertEqual(["/Some/Path/Path/1", "/Some/Path/Path/2"], results)

    def test_output_dir_plex(self):
        template = "{plex}"
        output_dir = "/Some/Path"
        files = ["file.mkv"]
        params = {
            "show": "TV Show",
            "season": 1,
            "episode_num": 2,
            "episode_name": "Episode Name",
            "episode_num_final": None,
        }
        results = new_names(
            rename_process(template, files, params=params, output_dir=output_dir)
        )
        self.assertEqual(
            ["/Some/Path/TV Show/Season 01/TV Show - S01E02 - Episode Name.mkv"],
            results,
        )

    def test_plex_specials(self):
        template = "{plex}"
        output_dir = "/Some/Path"
        files = ["file.mkv"]
        params = {
            "show": "TV Show",
            "season": 0,
            "episode_num": 2,
            "episode_name": "Episode Name",
            "episode_num_final": None,
        }
        results = new_names(
            rename_process(template, files, params=params, output_dir=output_dir)
        )
        self.assertEqual(
            ["/Some/Path/TV Show/Specials/TV Show - S00E02 - Episode Name.mkv"], results
        )

    def test_default_length(self):
        template = "${i|zpad}"
        files = [str(x) for x in range(5)]
        results = new_names(rename_process(template, files))
        self.assertEqual("01", results[0])

        template = "${i|zpad}"
        files = [str(x) for x in range(15)]
        results = new_names(rename_process(template, files))
        self.assertEqual("01", results[0])

        template = "${i|zpad}"
        files = [str(x) for x in range(100)]
        results = new_names(rename_process(template, files))
        self.assertEqual("001", results[0])
