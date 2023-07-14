import unittest

from media_management_scripts.convert import (
    convert_config_from_ns,
    convert_with_config,
    combine,
)
from media_management_scripts.support.combine_all import (
    combine_all,
    get_combinable_files,
)
from tests import (
    create_test_video,
    VideoDefinition,
    AudioDefition,
    AudioCodec,
    AudioChannelName,
)
from tempfile import NamedTemporaryFile, TemporaryDirectory
from media_management_scripts.utils import extract_metadata, ConvertConfig
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
    def _validate_file(self, filename, lang="eng"):
        metadata = extract_metadata(filename)
        self.assertEqual(1, len(metadata.video_streams))
        self.assertEqual(1, len(metadata.audio_streams))
        self.assertEqual(1, len(metadata.subtitle_streams))
        self.assertEqual(lang, metadata.subtitle_streams[0].language)

    def test_basic_combine(self):
        with create_test_video(length=3) as file, NamedTemporaryFile(
            suffix=".srt", mode="w"
        ) as srt_file, NamedTemporaryFile(suffix=".mkv") as out:
            srt_file.file.write(SRT_TEXT)
            srt_file.file.flush()
            ret = combine(
                file.name, srt_file.name, output=out.name, lang="eng", overwrite=True
            )
            self.assertEqual(0, ret)
            self._validate_file(out.name)

    def test_get_combinable_files(self):
        with TemporaryDirectory() as input_dir, TemporaryDirectory() as output_dir:
            file1 = os.path.join(input_dir, "file1.mkv")
            file2 = os.path.join(input_dir, "file2.mkv")
            file3 = os.path.join(input_dir, "file3.mkv")

            file1_srt = os.path.join(input_dir, "file1.eng.srt")
            file2_srt = os.path.join(input_dir, "file2.spa.srt")

            create_test_video(length=3, output_file=file1)
            create_test_video(length=3, output_file=file2)
            create_test_video(length=3, output_file=file3)
            with open(file1_srt, "w") as f:
                f.write(SRT_TEXT)
            with open(file2_srt, "w") as f:
                f.write(SRT_TEXT)
            files = list(get_combinable_files(input_dir, output_dir))
            self.assertEqual(
                (file1, file1_srt, "eng", os.path.join(output_dir, "file1.mkv")),
                files[0],
            )
            self.assertEqual(
                (file2, file2_srt, "spa", os.path.join(output_dir, "file2.mkv")),
                files[1],
            )
            self.assertEqual(
                (file3, None, None, os.path.join(output_dir, "file3.mkv")), files[2]
            )

    def test_combine_all(self):
        with TemporaryDirectory() as input_dir, TemporaryDirectory() as output_dir:
            create_test_video(
                length=3, output_file=os.path.join(input_dir, "file1.mkv")
            )
            create_test_video(
                length=3, output_file=os.path.join(input_dir, "file2.mkv")
            )
            create_test_video(
                length=3, output_file=os.path.join(input_dir, "file3.mkv")
            )
            with open(os.path.join(input_dir, "file1.eng.srt"), "w") as f:
                f.write(SRT_TEXT)
            with open(os.path.join(input_dir, "file2.spa.srt"), "w") as f:
                f.write(SRT_TEXT)
            combine_all(get_combinable_files(input_dir, output_dir))
            out1 = os.path.join(output_dir, "file1.mkv")
            out2 = os.path.join(output_dir, "file2.mkv")
            self.assertTrue(os.path.isfile(out1))
            self.assertTrue(os.path.isfile(out2))
            self.assertFalse(os.path.isfile(os.path.join(output_dir, "file3.mkv")))

            self._validate_file(out1)
            self._validate_file(out2, "spa")
