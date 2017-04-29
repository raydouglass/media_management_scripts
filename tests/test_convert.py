import unittest

from media_management_scripts.convert_dvd import ConvertConfig, convert_config_from_ns, convert_with_config
from tests import create_test_video
from tempfile import NamedTemporaryFile


class ConfigTestCase(unittest.TestCase):
    def test_namespace(self):
        ns = {
            'crf': 10,
            'preset': 'ultrafast'
        }
        config = convert_config_from_ns(ns)
        self.assertEqual(10, config.crf)
        self.assertEqual('ultrafast', config.preset)


class ConvertTestCase(unittest.TestCase):
    def test_basic_convert(self):
        config = convert_config_from_ns({})
        with create_test_video(length=10) as file, NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_auto_bitrate_convert(self):
        config = ConvertConfig(bitrate='auto')
        with create_test_video(length=10) as file, NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)

    def test_deinterlace_convert(self):
        config = ConvertConfig(deinterlace=True)
        with create_test_video(length=10) as file, NamedTemporaryFile(suffix='.mkv') as output:
            convert_with_config(file.name, output.name, config, overwrite=True)
