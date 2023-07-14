import unittest

from media_management_scripts.convert import convert_config_from_ns, convert_with_config
from media_management_scripts.utils import ConvertConfig, extract_metadata
from tests import (
    create_test_video,
    VideoDefinition,
    AudioDefition,
    AudioCodec,
    AudioChannelName,
)
from tempfile import NamedTemporaryFile
from media_management_scripts.support.encoding import VideoCodec, Resolution


class ConfigTestCase(unittest.TestCase):
    def test_namespace(self):
        ns = {"crf": 10, "preset": "ultrafast", "auto_bitrate_720": 1000}
        config = convert_config_from_ns(ns)
        self.assertEqual(10, config.crf)
        self.assertEqual("ultrafast", config.preset)
        self.assertEqual(1000, config.auto_bitrate_720)


class ConvertTestCase(unittest.TestCase):
    def test_basic_convert(self):
        config = convert_config_from_ns({})
        with create_test_video(length=10) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_defaults_convert(self):
        config = convert_config_from_ns({})
        with create_test_video(
            length=3,
            video_def=VideoDefinition(
                resolution=Resolution.LOW_DEF, codec=VideoCodec.MPEG2
            ),
            audio_defs=[AudioDefition(codec=AudioCodec.AC3)],
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(metadata.resolution, Resolution.LOW_DEF)
            self.assertEqual(
                metadata.video_streams[0].codec, VideoCodec.H264.ffmpeg_codec_name
            )
            self.assertEqual(
                metadata.audio_streams[0].codec, AudioCodec.AAC.ffmpeg_codec_name
            )

    def test_auto_bitrate_convert(self):
        config = ConvertConfig(bitrate="auto")
        with create_test_video(length=10) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_auto_bitrate_custom_convert(self):
        config = ConvertConfig(bitrate="auto", auto_bitrate_240=300)
        with create_test_video(length=10) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_deinterlace_detect_convert(self):
        config = ConvertConfig(deinterlace=True)
        with create_test_video(length=10) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_deinterlace_convert(self):
        config = ConvertConfig(deinterlace=True)
        with create_test_video(
            length=10,
            video_def=VideoDefinition(codec=VideoCodec.MPEG2, interlaced=True),
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_scale_convert(self):
        config = ConvertConfig(scale=480)
        with create_test_video(
            length=4, video_def=VideoDefinition(resolution=Resolution.HIGH_DEF)
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(metadata.resolution, Resolution.STANDARD_DEF)

    def test_hevc_convert(self):
        config = convert_config_from_ns(
            {"video_codec": VideoCodec.H265.ffmpeg_encoder_name}
        )
        with create_test_video(length=3) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(
                metadata.video_streams[0].codec.lower(),
                VideoCodec.H265.ffmpeg_codec_name,
            )

    def test_mpeg2_convert(self):
        config = convert_config_from_ns(
            {"video_codec": VideoCodec.MPEG2.ffmpeg_encoder_name}
        )
        with create_test_video(length=3) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(
                metadata.video_streams[0].codec.lower(),
                VideoCodec.MPEG2.ffmpeg_codec_name,
            )

    def test_audio_convert(self):
        config = convert_config_from_ns(
            {"audio_codec": AudioCodec.AC3.ffmpeg_codec_name}
        )
        with create_test_video(length=3) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(
                metadata.audio_streams[0].codec, AudioCodec.AC3.ffmpeg_codec_name
            )

    def test_audio_remux(self):
        config = convert_config_from_ns({"audio_codec": "copy"})
        with create_test_video(
            length=3, audio_defs=[AudioDefition(codec=AudioCodec.AC3)]
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(
                metadata.audio_streams[0].codec, AudioCodec.AC3.ffmpeg_codec_name
            )

    def test_video_remux(self):
        config = convert_config_from_ns({"video_codec": "copy"})
        with create_test_video(
            length=3, video_def=VideoDefinition(codec=VideoCodec.MPEG2)
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(
                metadata.video_streams[0].codec, VideoCodec.MPEG2.ffmpeg_codec_name
            )

    def test_multiple_audio(self):
        config = convert_config_from_ns({})
        with create_test_video(
            length=3,
            audio_defs=[
                AudioDefition(codec=AudioCodec.AC3),
                AudioDefition(codec=AudioCodec.AC3),
            ],
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(2, len(metadata.audio_streams))
            self.assertEqual(
                metadata.audio_streams[0].codec, AudioCodec.AAC.ffmpeg_codec_name
            )
            self.assertEqual(
                metadata.audio_streams[1].codec, AudioCodec.AAC.ffmpeg_codec_name
            )

    def test_multiple_audio_mappings(self):
        config = convert_config_from_ns({"audio_codec": "copy"})
        with create_test_video(
            length=3,
            audio_defs=[
                AudioDefition(codec=AudioCodec.AAC),
                AudioDefition(codec=AudioCodec.AC3),
            ],
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(
                file.name, output.name, config, mappings=[2], overwrite=True
            )
            metadata = extract_metadata(output.name)
            self.assertEqual(1, len(metadata.audio_streams))
            self.assertEqual(
                metadata.audio_streams[0].codec, AudioCodec.AC3.ffmpeg_codec_name
            )

    def test_multiple_audio_mappings_str(self):
        config = convert_config_from_ns({"audio_codec": "copy"})
        with create_test_video(
            length=3,
            audio_defs=[
                AudioDefition(codec=AudioCodec.AAC),
                AudioDefition(codec=AudioCodec.AC3),
            ],
        ) as file, NamedTemporaryFile(suffix=".mkv") as output:
            convert_with_config(
                file.name, output.name, config, mappings=["a:1"], overwrite=True
            )
            metadata = extract_metadata(output.name)
            self.assertEqual(1, len(metadata.audio_streams))
            self.assertEqual(
                metadata.audio_streams[0].codec, AudioCodec.AC3.ffmpeg_codec_name
            )

    def test_cut_convert(self):
        config = convert_config_from_ns({"start": 3.0, "end": 6.0})
        with create_test_video(length=10) as file, NamedTemporaryFile(
            suffix=".mkv"
        ) as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertAlmostEqual(3.0, metadata.estimated_duration, delta=0.03)
