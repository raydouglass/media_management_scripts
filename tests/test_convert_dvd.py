from tests import create_test_video, VideoDefinition
from media_management_scripts.support.encoding import VideoFileContainer
import unittest
from tempfile import TemporaryDirectory, NamedTemporaryFile
import configparser
import os
from media_management_scripts.support.encoding import (
    DEFAULT_CRF,
    DEFAULT_PRESET,
    Resolution,
)
from media_management_scripts.convert_daemon import ConvertDvds


# [directories]
# movie.dir.in = /mnt/media/Convert/Movie
# tv.dir.in = /mnt/media/Convert/TV Shows
# working.dir = /mnt/media/Working
# movie.dir.out = /mnt/media/
# tv.dir.out = /mnt/media/
#
# [backup]
# rclone = /usr/local/bin/rclone
# split = /usr/local/bin/gsplit
# backup.path = dest:/path/to/dest
# max.size = 25
# split.size = 5G
#
# [transcode]
# bitrate = auto
# crf = 18
# preset = veryfast
# deinterlace = True
# deinterlace_threshold = .5
#
# [logging]
# level = DEBUG
# file = convert.log
# db = processed.shelve


class BackupMock:
    def __init__(self, return_code=0):
        self.return_code = return_code

    def wait(self):
        return self.return_code


class ConvertDvdRegexTest(unittest.TestCase):
    def test_movie(self):
        from media_management_scripts.convert_daemon import MOVIE_NAME_REGEX

        self.assertIsNotNone(MOVIE_NAME_REGEX.fullmatch("Test (1999).mkv"))
        self.assertIsNotNone(MOVIE_NAME_REGEX.fullmatch("Test (1999) - 1080p.mkv"))
        self.assertIsNotNone(
            MOVIE_NAME_REGEX.fullmatch("Test (1999) - Extended 1080p.mkv")
        )
        self.assertIsNotNone(MOVIE_NAME_REGEX.fullmatch("Test (1999) - Extended.mkv"))
        self.assertIsNotNone(
            MOVIE_NAME_REGEX.fullmatch("Name with Spaces (2833) - 720p.mkv")
        )
        self.assertIsNone(MOVIE_NAME_REGEX.fullmatch("Test - Extended.mkv"))
        self.assertIsNone(MOVIE_NAME_REGEX.fullmatch("Test (1999) - .mkv"))

    def test_tv(self):
        from media_management_scripts.convert_daemon import TV_NAME_REGEX

        self.assertIsNotNone(
            TV_NAME_REGEX.fullmatch("TV Show Name - S01E01 - Episode Name.mkv")
        )
        self.assertIsNotNone(
            TV_NAME_REGEX.fullmatch("TV Show Name - S13E05 - Episode Name.mkv")
        )
        self.assertIsNotNone(TV_NAME_REGEX.fullmatch("TV Show Name - S13E05.mkv"))
        self.assertIsNotNone(TV_NAME_REGEX.fullmatch("TV Show Name - S2008E05.mkv"))
        self.assertIsNotNone(TV_NAME_REGEX.fullmatch("TV Show Name - S13E05-E06.mkv"))
        self.assertIsNone(TV_NAME_REGEX.fullmatch("Test - Extended.mkv"))
        self.assertIsNone(TV_NAME_REGEX.fullmatch("Test - S1E01 - Name.mkv"))
        self.assertIsNone(TV_NAME_REGEX.fullmatch("Test - S01E1 - Name.mkv"))


class ConvertDvdTestCase(unittest.TestCase):
    def setUp(self):
        self.files = []
        self.dirs = []
        self.config_file = NamedTemporaryFile(suffix=".ini", delete=False, mode="w")
        processed_shelve_file = NamedTemporaryFile(suffix=".shelve")
        self.log_file = NamedTemporaryFile(suffix=".log")

        config = configparser.ConfigParser()
        self.movie_in = TemporaryDirectory()
        self.tv_in = TemporaryDirectory()
        self.working_dir = TemporaryDirectory()
        self.movie_out = TemporaryDirectory()
        self.tv_out = TemporaryDirectory()
        config["directories"] = {
            "movie.dir.in": self.movie_in.name,
            "tv.dir.in": self.tv_in.name,
            "working.dir": self.working_dir.name,
            "movie.dir.out": self.movie_out.name,
            "tv.dir.out": self.tv_out.name,
        }
        config["backup"] = {
            "enabled": True,
            "rclone": "does/not/exist",
            "split": "/usr/local/bin/gsplit",
            "max.size": 25,
            "split.size": "5G",
            "backup.path": "/not",
        }
        config["movie.transcode"] = {
            "bitrate": "auto",
            "crf": DEFAULT_CRF,
            "preset": DEFAULT_PRESET,
            "deinterlace": True,
            "deinterlace_threshold": 0.5,
            "auto_bitrate_480": 2000,
        }
        config["logging"] = {
            "level": "DEBUG",
            "file": self.log_file.name,
            "db": processed_shelve_file.name,
        }

        self.files.extend([self.config_file, processed_shelve_file, self.log_file])
        self.dirs.extend(
            [self.movie_in, self.tv_in, self.working_dir, self.movie_out, self.tv_out]
        )
        with self.config_file:
            config.write(self.config_file)
        self.convert_dvds = ConvertDvds(self.config_file.name)

        self.backup_count = 0

        def backup_mock(file, target_dir):
            self.backup_count += 1
            return BackupMock()

        self.convert_dvds.backup_file = backup_mock

    def tearDown(self):
        for f in self.files:
            f.close()
            if os.path.exists(f.name):
                os.unlink(f.name)
        for d in self.dirs:
            d.cleanup()

    def test_backup_mock(self):
        ret = self.convert_dvds.backup_file("dir", "file")
        self.assertTrue(type(ret) == BackupMock)
        self.assertEqual(0, ret.wait())
        self.assertEqual(1, self.backup_count)
        with NamedTemporaryFile(suffix=".ini") as temp_file:
            ret, split_dir = self.convert_dvds.backup(
                os.path.dirname(temp_file.name), temp_file.name
            )
            self.assertIsNone(split_dir)
            self.assertTrue(type(ret) == BackupMock)
            self.assertEqual(0, ret.wait())
            self.assertEqual(2, self.backup_count)

    def test_config_file_created(self):
        parser = configparser.ConfigParser()
        parser.read(self.config_file.name)
        self.assertEqual(
            "does/not/exist", parser.get("backup", "rclone", fallback=None)
        )

    def test_config_parsed(self):
        self.assertEqual(
            Resolution.MEDIUM_DEF.auto_bitrate,
            self.convert_dvds.movie_convert_config.auto_bitrate_720,
        )
        self.assertEqual(2000, self.convert_dvds.movie_convert_config.auto_bitrate_480)

    def test_movie_run(self):
        movie_name = "Move Name (2000) - 1080p.mkv"
        input_file = os.path.join(self.movie_in.name, movie_name)
        create_test_video(length=10, output_file=input_file)
        os.utime(input_file, (0, 0))
        expected_output_file = os.path.join(self.movie_out.name, movie_name)

        result = self.convert_dvds.run()

        self.assertEqual(1, self.backup_count)
        self.assertTrue(os.path.isfile(expected_output_file))
        self.assertFalse(0, os.path.getsize(expected_output_file))
        self.assertEqual(1, result.movie_processed_count)
        self.assertEqual(1, result.movie_total_count)
        self.assertEqual(0, result.movie_error_count)
        self.assertEqual(0, result.tv_error_count)
        self.assertEqual(0, result.tv_processed_count)
        self.assertEqual(0, result.tv_total_count)

    def test_tv_run(self):
        tv_name = "Show Name/Season 02/Show Name - S02E01 - Episode Title.mkv"
        input_file = os.path.join(self.tv_in.name, tv_name)
        os.makedirs(os.path.dirname(input_file), exist_ok=True)
        create_test_video(length=10, output_file=input_file)
        os.utime(input_file, (0, 0))
        expected_output_file = os.path.join(self.tv_out.name, tv_name)

        result = self.convert_dvds.run()
        print(result)
        self.assertEqual(1, self.backup_count)
        self.assertTrue(os.path.isfile(expected_output_file))
        self.assertFalse(0, os.path.getsize(expected_output_file))
        self.assertEqual(0, result.movie_processed_count)
        self.assertEqual(0, result.movie_total_count)
        self.assertEqual(0, result.movie_error_count)
        self.assertEqual(0, result.tv_error_count)
        self.assertEqual(1, result.tv_processed_count)
        self.assertEqual(1, result.tv_total_count)

    def test_movie_exists(self):
        movie_name = "Move Name (2000) - 1080p.mkv"
        input_file = os.path.join(self.movie_in.name, movie_name)
        create_test_video(length=10, output_file=input_file)
        os.utime(input_file, (0, 0))

        output_file = os.path.join(self.movie_out.name, movie_name)
        with open(output_file, "w"):
            pass

        result = self.convert_dvds.run()

        self.assertEqual(1, self.backup_count)
        self.assertEqual(0, os.path.getsize(output_file))
        self.assertEqual(1, result.movie_processed_count)
        self.assertEqual(1, result.movie_total_count)
        self.assertEqual(0, result.movie_error_count)
        self.assertEqual(0, result.tv_error_count)
        self.assertEqual(0, result.tv_processed_count)
        self.assertEqual(0, result.tv_total_count)

    def test_multiple(self):
        movie_count = 3
        tv_count = 3
        expected_files = []
        for i in range(movie_count):
            movie_name = "Move Name (200{}) - 1080p.mkv".format(i)
            input_file = os.path.join(self.movie_in.name, movie_name)
            create_test_video(length=3, output_file=input_file)
            os.utime(input_file, (0, 0))
            expected_files.append(os.path.join(self.movie_out.name, movie_name))

        for i in range(tv_count):
            tv_name = (
                "Show Name/Season 02/Show Name - S02E0{} - Episode Title.mkv".format(i)
            )
            input_file = os.path.join(self.tv_in.name, tv_name)
            os.makedirs(os.path.dirname(input_file), exist_ok=True)
            create_test_video(length=3, output_file=input_file)
            os.utime(input_file, (0, 0))
            expected_files.append(os.path.join(self.tv_out.name, tv_name))

        result = self.convert_dvds.run()

        self.assertEqual(movie_count + tv_count, self.backup_count)
        for f in expected_files:
            self.assertTrue(os.path.isfile(f))
            self.assertFalse(0, os.path.getsize(f))
        self.assertEqual(movie_count, result.movie_processed_count)
        self.assertEqual(movie_count, result.movie_total_count)
        self.assertEqual(0, result.movie_error_count)
        self.assertEqual(0, result.tv_error_count)
        self.assertEqual(tv_count, result.tv_processed_count)
        self.assertEqual(tv_count, result.tv_total_count)
