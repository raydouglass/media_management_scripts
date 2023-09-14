from . import SubCommand
from .common import *
from media_management_scripts.support.encoding import Resolution, VideoCodec, AudioCodec
import itertools
import os


def filter_copy(codecs):
    return list(filter(lambda x: x != "copy", codecs))


class CreateTestVideoCommand(SubCommand):
    @property
    def name(self):
        return "create-test-video"

    def build_argparse(self, subparser):
        cmd_parser = subparser.add_parser(
            self.name,
            help="Create a test video file with the specified definitions",
            parents=[parent_parser, output_parser],
        )
        cmd_parser.add_argument(
            "--video-codec",
            "--vc",
            dest="video_codec",
            default=VideoCodec.H264.ffmpeg_codec_name,
            choices=filter_copy(
                itertools.chain.from_iterable(v.codec_names for v in VideoCodec)
            ),
        )
        cmd_parser.add_argument(
            "--audio-codec",
            "--ac",
            dest="audio_codec",
            default=AudioCodec.AAC.ffmpeg_codec_name,
            choices=filter_copy([ac.ffmpeg_codec_name for ac in AudioCodec]),
        )
        cmd_parser.add_argument(
            "--resolution",
            "-r",
            dest="resolution",
            default=Resolution.LOW_DEF.height,
            choices=[str(r.height) for r in Resolution],
        )
        cmd_parser.add_argument(
            "--length",
            "--duration",
            "-l",
            dest="length",
            type=DurationType,
            default=30.0,
            help="Duration of the video in 00h00m00.00s format",
        )

    def subexecute(self, ns):
        from media_management_scripts.support.test_video import (
            create_test_video,
            VideoDefinition,
            AudioDefinition,
        )

        output_file = ns["output"]
        video_codec = VideoCodec.from_code_name(ns["video_codec"])
        audio_codec = AudioCodec.from_code_name(ns["audio_codec"])
        resolution = Resolution.from_height(ns["resolution"])
        length = ns["length"]
        overwrite = ns["overwrite"]

        vd = VideoDefinition(codec=video_codec, resolution=resolution)
        ad = AudioDefinition(codec=audio_codec)
        if ns["dry_run"]:
            print("Would create test video with the following definitions:")
            print("Video Definition: {}".format(vd))
            print("Audio Definition: {}".format(ad))
            print("Length: {}".format(length))
            print("Output File: {}".format(output_file))
        elif os.path.exists(output_file) and not overwrite:
            print("Output file exists and overwrite is false")
        else:
            create_test_video(length, vd, [ad], output_file, metadata=None)


SubCommand.register(CreateTestVideoCommand)
