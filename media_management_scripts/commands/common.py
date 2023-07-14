import argparse
import itertools
from media_management_scripts.support.encoding import (
    DEFAULT_CRF,
    DEFAULT_PRESET,
    Resolution,
    VideoCodec,
    AudioCodec,
)
from media_management_scripts.support.formatting import (
    duration_from_str,
    DURATION_PATTERN,
)


class DurationType:
    def __call__(self, value):
        if not DURATION_PATTERN.match(value):
            raise argparse.ArgumentTypeError(
                "'{}' is not a valid duration".format(value)
            )
        return duration_from_str(value)


parent_parser = argparse.ArgumentParser(add_help=False)
parent_parser.add_argument(
    "--print-args", action="store_const", const=True, default=False
)
parent_parser.add_argument(
    "-n", "--dry-run", action="store_const", const=True, default=False
)

input_parser = argparse.ArgumentParser(add_help=False)
input_parser.add_argument("input", help="Input directory")

output_parser = argparse.ArgumentParser(add_help=False)
output_parser.add_argument("output", help="Output target")
output_parser.add_argument(
    "-y",
    "--overwrite",
    help="Overwrite output target if it exists",
    action="store_const",
    default=False,
    const=True,
)

convert_parent_parser = argparse.ArgumentParser(add_help=False, parents=[])
convert_parent_parser.add_argument(
    "--crf",
    default=DEFAULT_CRF,
    type=int,
    help="The CRF value for H.264 transcoding. Default={}".format(DEFAULT_CRF),
)
convert_parent_parser.add_argument(
    "--preset",
    default=DEFAULT_PRESET,
    choices=[
        "ultrafast",
        "superfast",
        DEFAULT_PRESET,
        "faster",
        "fast",
        "medium",
        "slow",
        "slower",
        "veryslow",
        "placebo",
    ],
    help="The preset for H.264 transcoding. Default={}".format(DEFAULT_PRESET),
)
convert_parent_parser.add_argument(
    "--bitrate",
    default=None,
    help='Use variable bitrate up to this value. Default=None (ignored). Specify "auto" for automatic bitrate.',
)
convert_parent_parser.add_argument(
    "--deinterlace",
    action="store_const",
    const=True,
    default=False,
    help="Attempt to detect interlacing and remove it",
)
convert_parent_parser.add_argument("--deinterlace-threshold", type=float, default=0.5)
convert_parent_parser.add_argument(
    "--add-ripped-metadata",
    action="store_const",
    const=True,
    default=False,
    help="Adds a metadata item to the output indicating this is a ripped video",
    dest="include_meta",
)
convert_parent_parser.add_argument(
    "--scale",
    choices=[r.height for r in Resolution],
    type=int,
    default=None,
    help="Set the maximum height scale",
)
convert_parent_parser.add_argument(
    "--start",
    "-s",
    type=DurationType(),
    help="Start time of the input in 00h00m00.00s format",
)
convert_parent_parser.add_argument(
    "--end",
    "-e",
    type=DurationType(),
    help="End time of the input in 00h00m00.00s format",
)

start_end_parser = argparse.ArgumentParser(add_help=False)
start_end_parser.add_argument(
    "--start",
    "-s",
    type=DurationType(),
    help="Start time of the input in 00h00m00.00s format",
)
start_end_parser.add_argument(
    "--end",
    "-e",
    type=DurationType(),
    help="End time of the input in 00h00m00.00s format",
)


class VideoCodecAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(VideoCodecAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        codec = VideoCodec.from_code_name(values)
        setattr(namespace, self.dest, codec.ffmpeg_encoder_name)


convert_parent_parser.add_argument(
    "--video-codec",
    "--vc",
    action=VideoCodecAction,
    dest="video_codec",
    default=VideoCodec.H264.ffmpeg_encoder_name,
    choices=list(
        itertools.chain(
            ["copy"], itertools.chain.from_iterable(v.codec_names for v in VideoCodec)
        )
    ),
)

convert_parent_parser.add_argument(
    "--audio-codec",
    "--ac",
    dest="audio_codec",
    default=AudioCodec.AAC.ffmpeg_codec_name,
    choices=list(
        itertools.chain(["copy"], [ac.ffmpeg_codec_name for ac in AudioCodec])
    ),
)

__all__ = [
    "parent_parser",
    "input_parser",
    "output_parser",
    "convert_parent_parser",
    "start_end_parser",
]
