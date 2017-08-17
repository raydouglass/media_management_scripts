import unittest

from media_management_scripts.convert import ConvertConfig, convert_config_from_ns, convert_with_config, combine
from media_management_scripts.support.combine_all import combine_all
from tests import create_test_video, VideoDefinition, AudioDefition, AudioCodec, AudioChannelName
from tempfile import NamedTemporaryFile, TemporaryDirectory
from media_management_scripts.utils import extract_metadata
import os

SRT_TEXT = """
1
00:01:16,820 --> 00:01:19,660
This is the first piece.

2
00:01:19,740 --> 00:01:22,700
This is another piece.

"""


class CombineTestCase(unittest.TestCase):
    def _validate_file(self, filename, lang='eng'):
        metadata = extract_metadata(filename)
        self.assertEqual(1, len(metadata.video_streams))
        self.assertEqual(1, len(metadata.audio_streams))
        self.assertEqual(1, len(metadata.subtitle_streams))
        self.assertEqual(lang, metadata.subtitle_streams[0].language)

    def test_basic_combine(self):
        with create_test_video(length=3) as file, \
                NamedTemporaryFile(suffix='.srt', mode='w') as srt_file, \
                NamedTemporaryFile(suffix='.mkv') as out:
            srt_file.file.write(SRT_TEXT)
            srt_file.file.flush()
            ret = combine(file.name, srt_file.name, output=out.name, lang='eng', overwrite=True)
            self.assertEqual(0, ret)
            self._validate_file(out.name)

    def test_combine_all(self):
        with TemporaryDirectory() as input_dir, TemporaryDirectory() as output_dir:
            create_test_video(length=3, output_file=os.path.join(input_dir, 'file1.mkv'))
            create_test_video(length=3, output_file=os.path.join(input_dir, 'file2.mkv'))
            create_test_video(length=3, output_file=os.path.join(input_dir, 'file3.mkv'))
            with open(os.path.join(input_dir, 'file1.eng.srt'), 'w') as f:
                f.write(SRT_TEXT)
            with open(os.path.join(input_dir, 'file2.spa.srt'), 'w') as f:
                f.write(SRT_TEXT)
            combine_all(input_dir, output_dir)
            out1 = os.path.join(output_dir, 'file1.mkv')
            out2 = os.path.join(output_dir, 'file2.mkv')
            self.assertTrue(os.path.isfile(out1))
            self.assertTrue(os.path.isfile(out2))
            self.assertFalse(os.path.isfile(os.path.join(output_dir, 'file3.mkv')))

            self._validate_file(out1)
            self._validate_file(out2, 'spa')
