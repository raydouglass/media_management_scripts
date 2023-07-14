import unittest
from pyparsing import ParseException

from media_management_scripts.support.search_parser import parse_and_execute, parse
from tempfile import TemporaryDirectory, NamedTemporaryFile
import configparser
from media_management_scripts.support.encoding import DEFAULT_CRF, DEFAULT_PRESET
from media_management_scripts.support.executables import ccextractor, comskip
import os
from media_management_scripts.support.encoding import (
    Resolution,
    VideoCodec,
    VideoFileContainer,
    AudioCodec,
    AudioChannelName,
)
from tests import create_test_video, VideoDefinition, AudioDefition
from unittest import mock
from media_management_scripts.commands.search import search

H264_VIDEO_DEF = VideoDefinition(
    Resolution.LOW_DEF, VideoCodec.H264, VideoFileContainer.MP4
)
MPE2_VIDEO_DEF = VideoDefinition(
    Resolution.LOW_DEF, VideoCodec.MPEG2, VideoFileContainer.MP4
)

AAC_STEREO_AUDIO_DEF = AudioDefition(AudioCodec.AAC, AudioChannelName.STEREO)
AAC_SURROUND_AUDIO_DEF = AudioDefition(AudioCodec.AAC, AudioChannelName.SURROUND_5_1)
AC3_STEREO_AUDIO_DEF = AudioDefition(AudioCodec.AC3, AudioChannelName.STEREO)


class VideoMixin:
    def create(self, video_def, audio_def):
        self.count += 1
        create_test_video(
            1,
            video_def=video_def,
            audio_defs=[audio_def],
            output_file=os.path.join(self.tmpdir.name, "{}.mp4".format(self.count)),
        )
        return self.count

    def setup(self):
        self.count = -1
        self.tmpdir = TemporaryDirectory()
        self.db_file = os.path.join(self.tmpdir.name, "db_file")

    def cleanup(self):
        self.tmpdir.cleanup()

    def search(self, query):
        return list(search(self.tmpdir.name, query, self.db_file))

    def run_test(self, expected_count, query):
        self.assertEqual(expected_count, len(self.search(query)))


class SearchTestCase(unittest.TestCase, VideoMixin):
    def setUp(self):
        self.setup()

    def tearDown(self):
        self.cleanup()
        pass

    def test_basic(self):
        self.create(H264_VIDEO_DEF, AAC_STEREO_AUDIO_DEF)
        self.run_test(1, "v.codec = h264")
        self.run_test(0, "v.codec != h264")
        self.run_test(1, "a.codec = aac")
        self.run_test(0, "v.codec = ac3")
        self.run_test(1, "v.codec = h264 and a.codec = aac")
        self.run_test(1, "a.channels = 2")

    def test_multiple(self):
        self.create(H264_VIDEO_DEF, AAC_STEREO_AUDIO_DEF)
        self.create(H264_VIDEO_DEF, AAC_STEREO_AUDIO_DEF)
        self.run_test(2, "v.codec = h264")

    def test_advanced(self):
        self.create(H264_VIDEO_DEF, AAC_STEREO_AUDIO_DEF)
        self.create(H264_VIDEO_DEF, AC3_STEREO_AUDIO_DEF)
        self.run_test(1, "a.codec = aac")
        self.run_test(1, "a.codec = ac3")
        self.run_test(2, "a.codec in [ac3, aac]")
        self.run_test(2, "a.codec = aac or a.codec = ac3")

    def test_multiple_greater(self):
        self.create(H264_VIDEO_DEF, AAC_STEREO_AUDIO_DEF)
        self.create(H264_VIDEO_DEF, AAC_SURROUND_AUDIO_DEF)
        self.run_test(2, "a.channels > 1")
        self.run_test(2, "a.channels >= 2")
        self.run_test(1, "a.channels > 2")
        self.run_test(0, "a.channels < 2")

    def test_meta(self):
        create_test_video(
            1,
            video_def=H264_VIDEO_DEF,
            audio_defs=[AAC_STEREO_AUDIO_DEF],
            output_file=os.path.join(self.tmpdir.name, "test.mp4"),
            metadata={"title": "whatever"},
        )
        self.run_test(1, "meta.title = whatever")
        self.run_test(1, "meta.tags.title = whatever")
        create_test_video(
            1,
            video_def=H264_VIDEO_DEF,
            audio_defs=[AAC_STEREO_AUDIO_DEF],
            output_file=os.path.join(self.tmpdir.name, "test2.mp4"),
            metadata={"title": "whatever two"},
        )
        self.run_test(1, 'meta.title = "whatever two"')

    def test_resolution(self):
        self.create(H264_VIDEO_DEF, AAC_STEREO_AUDIO_DEF)
        self.run_test(1, "resolution = LOW_DEF")
