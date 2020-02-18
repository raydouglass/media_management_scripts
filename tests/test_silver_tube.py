import unittest
from tempfile import TemporaryDirectory, NamedTemporaryFile
import configparser
from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET
from media_management_scripts.support.executables import ccextractor, comskip
import os
from media_management_scripts.support.encoding import Resolution, VideoCodec, VideoFileContainer, AudioCodec, \
    AudioChannelName
from tests import create_test_video, VideoDefinition, LOG_FILE
from unittest import mock

from media_management_scripts.silver_tube.processing import Configuration
from media_management_scripts.tvdb_api import TVDB

WTV_VIDEO_DEF = VideoDefinition(resolution=Resolution.STANDARD_DEF,
                                codec=VideoCodec.MPEG2,
                                container=VideoFileContainer.WTV)

try:
    comskip()
    comskip_installed = True
except:
    comskip_installed = False


@unittest.skipUnless(comskip_installed, reason='Need comskip to run these tests')
class SilverTubeTestCase(unittest.TestCase):
    def setUp(self):
        self.files = []
        self.dirs = []
        self.config_file = NamedTemporaryFile(suffix='.ini', delete=False, mode='w')
        db_file = NamedTemporaryFile(suffix='.sqlite3')

        config = configparser.ConfigParser()
        config['main'] = {
            'debug': False,
            'database.file': db_file.name,
            'log.config': LOG_FILE
        }
        self.tv_in = TemporaryDirectory()
        self.commercial_in = TemporaryDirectory()
        self.srt_in = TemporaryDirectory()
        self.temp_dir = TemporaryDirectory()
        self.out_dir = TemporaryDirectory()
        config['directories'] = {
            'tv.in': self.tv_in.name,
            'commercial.in': self.commercial_in.name,
            'srt.in': self.srt_in.name,
            'temp.dir': self.temp_dir.name,
            'out.dir': self.out_dir.name,
            'tv.pattern': '*.wtv'
        }
        config['transcode'] = {
            'preset': DEFAULT_PRESET,
            'crf': DEFAULT_CRF,
            'bitrate': 'auto'
        }
        config['ccextractor'] = {
            'executable': ccextractor(),
            'run.if.missing': True
        }
        comskip_ini = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'comskip.ini')
        config['comskip'] = {
            'executable': comskip(),
            'comskip.ini': comskip_ini,
            'run.if.missing': True
        }
        self.files.extend([self.config_file, db_file])
        self.dirs.extend([self.tv_in, self.commercial_in, self.srt_in, self.temp_dir, self.out_dir])
        with self.config_file:
            config.write(self.config_file)

    def tearDown(self):
        for f in self.files:
            f.close()
            if os.path.exists(f.name):
                os.unlink(f.name)
        for d in self.dirs:
            d.cleanup()

    def test_config_file_created(self):
        parser = configparser.ConfigParser()
        parser.read(self.config_file.name)
        self.assertEqual(ccextractor(), parser.get('ccextractor', 'executable', fallback=None))

    @mock.patch('media_management_scripts.tvdb_api.TVDB')
    def test_no_files(self, tvdb_mock):
        config = Configuration(self.config_file.name, tvdb_mock)
        config.run()
        self.assertEqual(0, config.count)

    @mock.patch('media_management_scripts.tvdb_api.TVDB')
    def test_basic(self, tvdb_mock):
        tvdb_mock.find_episode.return_value = [{
            'id': 1001,
            'episodeName': 'Test Episode NameTVDB',
            'overview': 'TheOverview',
            'firstAired': '2011-01-01',
            'airedSeason': 2,
            'airedEpisodeNumber': 3
        }]
        tvdb_mock.season_number = lambda e: (e['airedSeason'], e['airedEpisodeNumber'])
        meta = {
            'Title': 'TheSeries',
            'WM/SubTitle': 'Test Episode Name',
            'WM/SubTitleDescription': 'TheSubTitleDescription',
            'WM/MediaOriginalBroadcastDateTime': '2011-01-01T00:00:00Z'
        }
        input_file = os.path.join(self.tv_in.name, 'test.wtv')
        create_test_video(length=10, video_def=WTV_VIDEO_DEF, output_file=input_file, metadata=meta)
        os.utime(input_file, (0, 0))
        config = Configuration(self.config_file.name, tvdb_mock)
        config.run()
        self.assertEqual(1, config.count)

        expected_file = os.path.join(self.out_dir.name,
                                     'TheSeries/Season 2/TheSeries - S02E03 - Test Episode NameTVDB.mp4')
        self.assertTrue(os.path.isfile(expected_file))

    @mock.patch('media_management_scripts.tvdb_api.TVDB')
    def test_store_candidates(self, tvdb_mock):
        tvdb_mock.find_episode.return_value = [{
            'id': 1001,
            'episodeName': 'Test Episode NameTVDB',
            'overview': 'TheOverview',
            'firstAired': '2011-01-01',
            'airedSeason': 2,
            'airedEpisodeNumber': 3
        }, {
            'id': 1002,
            'episodeName': 'Test Episode NameTVDB2',
            'overview': 'TheOverview2',
            'firstAired': '2011-01-02',
            'airedSeason': 2,
            'airedEpisodeNumber': 4
        }]
        tvdb_mock.season_number = lambda e: (e['airedSeason'], e['airedEpisodeNumber'])
        tvdb_mock.get_series_id.return_value = 54321
        meta = {
            'Title': 'TheSeries',
            'WM/SubTitle': 'Test Episode Name',
            'WM/SubTitleDescription': 'TheSubTitleDescription',
            'WM/MediaOriginalBroadcastDateTime': '2011-01-01T00:00:00Z'
        }
        input_file = os.path.join(self.tv_in.name, 'test.wtv')
        create_test_video(length=10, video_def=WTV_VIDEO_DEF, output_file=input_file, metadata=meta)
        os.utime(input_file, (0, 0))
        config = Configuration(self.config_file.name, tvdb_mock)
        config.run()
        self.assertEqual(1, config.count)

        expected_file = os.path.join(self.out_dir.name,
                                     'TheSeries/Season 2/TheSeries - S02E03 - Test Episode NameTVDB.mp4')
        self.assertFalse(os.path.isfile(expected_file))

        config.wtvdb.begin()
        wtv = config.wtvdb.get_wtv('test.wtv')
        self.assertIsNotNone(wtv)
        self.assertEqual(2, len(wtv.candidate_episodes))
        config.wtvdb.end()

    @mock.patch('media_management_scripts.tvdb_api.TVDB')
    def test_no_candidates(self, tvdb_mock):
        tvdb_mock.find_episode.return_value = []
        tvdb_mock.season_number = lambda e: (e['airedSeason'], e['airedEpisodeNumber'])
        tvdb_mock.get_series_id.return_value = 54321
        meta = {
            'Title': 'TheSeries',
            'WM/SubTitle': 'Test Episode Name',
            'WM/SubTitleDescription': 'TheSubTitleDescription',
            'WM/MediaOriginalBroadcastDateTime': '2011-01-01T00:00:00Z'
        }
        input_file = os.path.join(self.tv_in.name, 'test.wtv')
        create_test_video(length=10, video_def=WTV_VIDEO_DEF, output_file=input_file, metadata=meta)
        os.utime(input_file, (0, 0))
        config = Configuration(self.config_file.name, tvdb_mock)
        config.run()
        self.assertEqual(1, config.count)

        expected_file = os.path.join(self.out_dir.name,
                                     'TheSeries/Season 2/TheSeries - S02E03 - Test Episode NameTVDB.mp4')
        self.assertFalse(os.path.isfile(expected_file))

        config.wtvdb.begin()
        wtv = config.wtvdb.get_wtv('test.wtv')
        self.assertIsNotNone(wtv)
        self.assertEqual(0, len(wtv.candidate_episodes))
        config.wtvdb.end()
