from tests import create_test_video, VideoDefinition
from media_management_scripts.support.encoding import VideoFileContainer
import unittest
from tempfile import TemporaryDirectory, NamedTemporaryFile
import configparser
import os
from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET, Resolution
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

class BackupMock():
    def __init__(self, return_code=0):
        self.return_code = return_code

    def wait(self):
        return self.return_code


class ConvertDvdTestCase(unittest.TestCase):
    def setUp(self):
        self.files = []
        self.dirs = []
        self.config_file = NamedTemporaryFile(suffix='.ini', delete=False, mode='w')
        processed_shelve_file = NamedTemporaryFile(suffix='.shelve')
        log_file = NamedTemporaryFile(suffix='.log')

        config = configparser.ConfigParser()
        self.movie_in = TemporaryDirectory()
        self.tv_in = TemporaryDirectory()
        self.working_dir = TemporaryDirectory()
        self.movie_out = TemporaryDirectory()
        self.tv_out = TemporaryDirectory()
        config['directories'] = {
            'movie.dir.in': self.movie_in.name,
            'tv.dir.in': self.tv_in.name,
            'working.dir': self.working_dir.name,
            'movie.dir.out': self.movie_out.name,
            'tv.dir.out': self.tv_out.name
        }
        config['backup'] = {
            'enabled': False,
            'rclone': 'does/not/exist',
            'split': '/usr/local/bin/gsplit',
            'max.size': 25,
            'split.size': '5G',
            'backup.path': '/not'
        }
        config['transcode'] = {
            'bitrate': 'auto',
            'crf': DEFAULT_CRF,
            'preset': DEFAULT_PRESET,
            'deinterlace': True,
            'deinterlace_threshold': .5,
            'auto_bitrate_480': 2000
        }
        config['logging'] = {
            'level': 'DEBUG',
            'file': log_file.name,
            'db': processed_shelve_file.name
        }

        self.files.extend([self.config_file, processed_shelve_file, log_file])
        self.dirs.extend([self.movie_in, self.tv_in, self.working_dir, self.movie_out, self.tv_out])
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
        ret = self.convert_dvds.backup_file('dir', 'file')
        self.assertTrue(type(ret) == BackupMock)
        self.assertEquals(0, ret.wait())
        self.assertEqual(1, self.backup_count)
        with NamedTemporaryFile(suffix='.ini') as temp_file:
            ret, split_dir = self.convert_dvds.backup(os.path.dirname(temp_file.name), temp_file.name)
            self.assertIsNone(split_dir)
            self.assertTrue(type(ret) == BackupMock)
            self.assertEquals(0, ret.wait())
            self.assertEqual(2, self.backup_count)

    def test_config_file_created(self):
        parser = configparser.ConfigParser()
        parser.read(self.config_file.name)
        self.assertEqual('does/not/exist', parser.get('backup', 'rclone', fallback=None))

    def test_config_parsed(self):
        self.assertEqual(Resolution.MEDIUM_DEF.auto_bitrate, self.convert_dvds.convert_config.auto_bitrate_720)
        self.assertEqual(2000, self.convert_dvds.convert_config.auto_bitrate_480)
