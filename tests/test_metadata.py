from media_management_scripts.support.encoding import (
    VideoCodec,
    VideoFileContainer,
    Resolution,
    AudioCodec,
    AudioChannelName,
)
from tests import create_test_video, VideoDefinition, AudioDefition, assertAudioLength
from media_management_scripts.utils import create_metadata_extractor
import unittest
from tempfile import NamedTemporaryFile


class MetadataTestCase(unittest.TestCase):
    def test_metadata_print(self):
        from media_management_scripts.commands.metadata import print_metadata

        with create_test_video(length=2) as file:
            print_metadata(file.name)

    def test_metadata_in_file(self):
        meta = {"TestKey": "test_value"}
        length = 2
        with create_test_video(
            length=length,
            video_def=VideoDefinition(
                Resolution.HIGH_DEF, VideoCodec.H264, VideoFileContainer.WTV
            ),
            metadata=meta,
        ) as file:
            metadata = create_metadata_extractor().extract(file.name)
            print(metadata.tags)
            self.assertTrue("TestKey" in metadata.tags)
            self.assertEqual("test_value", metadata.tags["TestKey"])

        with create_test_video(
            length=length,
            video_def=VideoDefinition(
                Resolution.HIGH_DEF, VideoCodec.H264, VideoFileContainer.MKV
            ),
            metadata=meta,
        ) as file:
            metadata = create_metadata_extractor().extract(file.name)
            print(metadata.tags)
            # MKV stores as uppercase
            self.assertTrue("TESTKEY" in metadata.tags)
            self.assertEqual("test_value", metadata.tags["TESTKEY"])

    def test_h264_stereo(self):
        length = 5
        with create_test_video(length=length) as file:
            metadata = create_metadata_extractor().extract(file.name)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(1, len(metadata.audio_streams))

            v = metadata.video_streams[0]
            a = metadata.audio_streams[0]

            self.assertEqual(VideoCodec.H264.ffmpeg_codec_name, v.codec)
            self.assertEqual(length, v.duration)
            self.assertEqual(Resolution.LOW_DEF.width, v.width)
            self.assertEqual(Resolution.LOW_DEF.height, v.height)

            self.assertEqual(AudioCodec.AAC.ffmpeg_codec_name, a.codec)
            assertAudioLength(length, a.duration)
            self.assertEqual(2, a.channels)

    def test_h264_stereo_ac3(self):
        length = 5
        with create_test_video(
            length=length,
            audio_defs=[AudioDefition(AudioCodec.AC3, AudioChannelName.STEREO)],
        ) as file:
            metadata = create_metadata_extractor().extract(file.name)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(1, len(metadata.audio_streams))

            v = metadata.video_streams[0]
            a = metadata.audio_streams[0]

            self.assertEqual(VideoCodec.H264.ffmpeg_codec_name, v.codec)
            self.assertEqual(length, v.duration)
            self.assertEqual(Resolution.LOW_DEF.width, v.width)
            self.assertEqual(Resolution.LOW_DEF.height, v.height)

            self.assertEqual(AudioCodec.AC3.ffmpeg_codec_name, a.codec)
            assertAudioLength(length, a.duration)
            self.assertEqual(2, a.channels)

    def test_h264_5_1(self):
        length = 5
        with create_test_video(
            length=length,
            audio_defs=[AudioDefition(AudioCodec.AAC, AudioChannelName.SURROUND_5_1)],
        ) as file:
            metadata = create_metadata_extractor().extract(file.name)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(1, len(metadata.audio_streams))

            v = metadata.video_streams[0]
            a = metadata.audio_streams[0]

            self.assertEqual(VideoCodec.H264.ffmpeg_codec_name, v.codec)
            self.assertEqual(length, v.duration)
            self.assertEqual(Resolution.LOW_DEF.width, v.width)
            self.assertEqual(Resolution.LOW_DEF.height, v.height)

            self.assertEqual(AudioCodec.AAC.ffmpeg_codec_name, a.codec)
            assertAudioLength(length, a.duration)
            self.assertEqual(6, a.channels)

    def test_h264_1080p_5_1(self):
        length = 3
        with create_test_video(
            length=length,
            video_def=VideoDefinition(
                Resolution.HIGH_DEF, VideoCodec.H264, VideoFileContainer.MP4
            ),
            audio_defs=[AudioDefition(AudioCodec.AAC, AudioChannelName.SURROUND_5_1)],
        ) as file:
            metadata = create_metadata_extractor().extract(file.name)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(1, len(metadata.audio_streams))

            v = metadata.video_streams[0]
            a = metadata.audio_streams[0]

            self.assertEqual(VideoCodec.H264.ffmpeg_codec_name, v.codec)
            self.assertEqual(length, v.duration)
            self.assertEqual(Resolution.HIGH_DEF.width, v.width)
            self.assertEqual(Resolution.HIGH_DEF.height, v.height)

            self.assertEqual(AudioCodec.AAC.ffmpeg_codec_name, a.codec)
            assertAudioLength(length, a.duration)
            self.assertEqual(6, a.channels)

    def test_h264_stereo_2_audio(self):
        length = 5
        with create_test_video(
            length=length, audio_defs=[AudioDefition(), AudioDefition()]
        ) as file:
            metadata = create_metadata_extractor().extract(file.name)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(2, len(metadata.audio_streams))

            v = metadata.video_streams[0]
            self.assertEqual(VideoCodec.H264.ffmpeg_codec_name, v.codec)
            self.assertEqual(length, v.duration)
            self.assertEqual(Resolution.LOW_DEF.width, v.width)
            self.assertEqual(Resolution.LOW_DEF.height, v.height)

            for a in metadata.audio_streams:
                self.assertEqual(AudioCodec.AAC.ffmpeg_codec_name, a.codec)
                assertAudioLength(length, a.duration)
                self.assertEqual(2, a.channels)

    def test_h265_1080p_5_1(self):
        length = 3
        with create_test_video(
            length=length,
            video_def=VideoDefinition(
                Resolution.HIGH_DEF, VideoCodec.H265, VideoFileContainer.MKV
            ),
            audio_defs=[AudioDefition(AudioCodec.AAC, AudioChannelName.SURROUND_5_1)],
        ) as file:
            metadata = create_metadata_extractor().extract(file.name)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(1, len(metadata.audio_streams))

            v = metadata.video_streams[0]
            a = metadata.audio_streams[0]

            self.assertEqual(VideoCodec.H265.ffmpeg_codec_name, v.codec)
            self.assertEqual(length, v.duration)
            self.assertEqual(Resolution.HIGH_DEF.width, v.width)
            self.assertEqual(Resolution.HIGH_DEF.height, v.height)

            self.assertEqual(AudioCodec.AAC.ffmpeg_codec_name, a.codec)
            assertAudioLength(length, a.duration)
            self.assertEqual(6, a.channels)

    def test_mpeg2(self):
        length = 5
        with create_test_video(
            length=length, video_def=VideoDefinition(codec=VideoCodec.MPEG2)
        ) as file:
            metadata = create_metadata_extractor().extract(file.name, True)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(1, len(metadata.audio_streams))
            self.assertFalse(metadata.interlace_report.is_interlaced())

            v = metadata.video_streams[0]
            a = metadata.audio_streams[0]

            self.assertEqual(VideoCodec.MPEG2.ffmpeg_codec_name, v.codec)
            self.assertEqual(length, v.duration)
            self.assertEqual(Resolution.LOW_DEF.width, v.width)
            self.assertEqual(Resolution.LOW_DEF.height, v.height)

            self.assertEqual(AudioCodec.AAC.ffmpeg_codec_name, a.codec)
            assertAudioLength(length, a.duration)
            self.assertEqual(2, a.channels)

    def test_mpeg2_interlaced(self):
        length = 5
        with create_test_video(
            length=length,
            video_def=VideoDefinition(codec=VideoCodec.MPEG2, interlaced=True),
        ) as file:
            metadata = create_metadata_extractor().extract(file.name, True)
            self.assertEqual(1, len(metadata.video_streams))
            self.assertEqual(1, len(metadata.audio_streams))
            self.assertTrue(metadata.interlace_report.is_interlaced(threshold=0.4))

            v = metadata.video_streams[0]
            a = metadata.audio_streams[0]

            self.assertEqual(VideoCodec.MPEG2.ffmpeg_codec_name, v.codec)
            self.assertEqual(length - 0.033, v.duration)
            self.assertEqual(Resolution.LOW_DEF.width, v.width)
            self.assertEqual(Resolution.LOW_DEF.height, v.height)

            self.assertEqual(AudioCodec.AAC.ffmpeg_codec_name, a.codec)
            assertAudioLength(length, a.duration)
            self.assertEqual(2, a.channels)
