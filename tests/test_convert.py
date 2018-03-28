import unittest

from media_management_scripts.convert import convert_config_from_ns, convert_with_config
from media_management_scripts.utils import ConvertConfig, extract_metadata
from tests import create_test_video, VideoDefinition, AudioDefition, AudioCodec, AudioChannelName
from tempfile import NamedTemporaryFile
from media_management_scripts.support.encoding import VideoCodec, Resolution


class ConfigTestCase(unittest.TestCase):
    def test_namespace(self):
        ns = {
            'crf': 10,
            'preset': 'ultrafast',
            'auto_bitrate_720': 1000
        }
        config = convert_config_from_ns(ns)
        self.assertEqual(10, config.crf)
        self.assertEqual('ultrafast', config.preset)
        self.assertEqual(1000, config.auto_bitrate_720)


class ConvertTestCase(unittest.TestCase):
    def test_basic_convert(self):
        config = convert_config_from_ns({})
        with create_test_video(length=10) as file, NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_auto_bitrate_convert(self):
        config = ConvertConfig(bitrate='auto')
        with create_test_video(length=10) as file, NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_auto_bitrate_custom_convert(self):
        config = ConvertConfig(bitrate='auto', auto_bitrate_240=300)
        with create_test_video(length=10) as file, NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_deinterlace_detect_convert(self):
        config = ConvertConfig(deinterlace=True)
        with create_test_video(length=10) as file, NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_deinterlace_convert(self):
        config = ConvertConfig(deinterlace=True)
        with create_test_video(length=10, video_def=VideoDefinition(codec=VideoCodec.MPEG2,
                                                                    interlaced=True)) as file, \
                NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_scale_convert(self):
        config = ConvertConfig(scale=480)
        with create_test_video(length=10, video_def=VideoDefinition(resolution=Resolution.HIGH_DEF)) as file, \
                NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
            metadata = extract_metadata(output.name)
            self.assertEqual(metadata.resolution, Resolution.STANDARD_DEF)
