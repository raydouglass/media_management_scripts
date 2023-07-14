from media_management_scripts.support.encoding import (
    VideoCodec,
    VideoFileContainer,
    Resolution,
    AudioCodec,
)
from tests import create_test_video, VideoDefinition, assertAudioLength, AudioDefition
from media_management_scripts.support.concat_mp4 import concat_mp4
from media_management_scripts.utils import create_metadata_extractor
import unittest
from tempfile import NamedTemporaryFile

MP4_VIDEO_DEF = VideoDefinition(
    Resolution.LOW_DEF, VideoCodec.H264, VideoFileContainer.MP4
)


class ConcatMp4TestCase(unittest.TestCase):
    def test_2_files(self):
        with create_test_video(
            length=5, video_def=MP4_VIDEO_DEF
        ) as first, create_test_video(length=5, video_def=MP4_VIDEO_DEF) as second:
            with NamedTemporaryFile(suffix=".mp4") as output:
                concat_mp4(output.name, files=[first.name, second.name], overwrite=True)
                metadata = create_metadata_extractor().extract(output.name)
                self.assertEqual(1, len(metadata.video_streams))
                self.assertEqual(10, int(metadata.video_streams[0].duration))

                self.assertEqual(1, len(metadata.audio_streams))
                self.assertEqual("aac", metadata.audio_streams[0].codec)
                self.assertEqual(2, metadata.audio_streams[0].channels)
                assertAudioLength(10, metadata.audio_streams[0].duration)

    def test_3_files(self):
        with create_test_video(
            length=5, video_def=MP4_VIDEO_DEF
        ) as first, create_test_video(
            length=5, video_def=MP4_VIDEO_DEF
        ) as second, create_test_video(
            length=5, video_def=MP4_VIDEO_DEF
        ) as third:
            with NamedTemporaryFile(suffix=".mp4") as output:
                concat_mp4(
                    output.name,
                    files=[first.name, second.name, third.name],
                    overwrite=True,
                )
                metadata = create_metadata_extractor().extract(output.name)
                self.assertEqual(1, len(metadata.video_streams))
                self.assertEqual(15, int(metadata.video_streams[0].duration))

                self.assertEqual(1, len(metadata.audio_streams))
                self.assertEqual("aac", metadata.audio_streams[0].codec)
                self.assertEqual(2, metadata.audio_streams[0].channels)
                self.assertEqual(15, int(metadata.audio_streams[0].duration))

    def test_not_h264(self):
        with create_test_video(
            length=5,
            video_def=VideoDefinition(
                Resolution.LOW_DEF, VideoCodec.MPEG2, VideoFileContainer.MP4
            ),
        ) as first, create_test_video(length=5, video_def=MP4_VIDEO_DEF) as second:
            with NamedTemporaryFile(suffix=".mp4") as output:
                with self.assertRaises(expected_exception=Exception):
                    concat_mp4(
                        output.name, files=[first.name, second.name], overwrite=True
                    )

    def test_not_aac(self):
        with create_test_video(
            length=5,
            video_def=MP4_VIDEO_DEF,
            audio_defs=[AudioDefition(codec=AudioCodec.AC3)],
        ) as first, create_test_video(length=5, video_def=MP4_VIDEO_DEF) as second:
            with NamedTemporaryFile(suffix=".mp4") as output:
                with self.assertRaises(expected_exception=Exception):
                    concat_mp4(
                        output.name, files=[first.name, second.name], overwrite=True
                    )
