from media_management_scripts.support.encoding import (
    Resolution,
    VideoCodec,
    VideoFileContainer,
    AudioCodec,
    AudioChannelName,
)
from media_management_scripts.support.executables import ffmpeg, ffprobe
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from media_management_scripts.convert import execute
from typing import List, Tuple, NamedTuple, Dict
from collections import namedtuple
import os

random_source = (
    "/dev/random" if bool(os.environ.get("TRAVIS", False)) else "/dev/urandom"
)


class VideoDefinition(NamedTuple):
    resolution: Resolution = Resolution.LOW_DEF
    codec: VideoCodec = VideoCodec.H264
    container: VideoFileContainer = VideoFileContainer.MKV
    interlaced: bool = False


class AudioDefinition(NamedTuple):
    codec: AudioCodec = AudioCodec.AAC
    channels: AudioChannelName = AudioChannelName.STEREO


def _execute(args):
    ret = execute(args, print_output=True)
    if ret != 0:
        raise Exception("Failed to create test video")


def create_test_video(
    length: int = 30,
    video_def: VideoDefinition = VideoDefinition(),
    audio_defs: List[AudioDefinition] = [AudioDefinition()],
    output_file=None,
    metadata: Dict[str, str] = {},
) -> _TemporaryFileWrapper:
    """
    Creates a video file matching the given video & audio definitions. If an output_file is not provided, a NamedTemporaryFile is used and returned
    :param length: the length of the file in seconds (Note, depending on codecs, the exact length may vary slightly)
    :param video_def: the video definition (codec, resolution, etc)
    :param audio_defs: the list of audio tracks
    :param output_file: the output file (or None for a NamedTemporaryFile)
    :return: the NamedTemporaryFile if no output_file was provided
    """
    audio_files = []
    if len(audio_defs) > 0:
        with NamedTemporaryFile(suffix=".wav") as raw_audio_file:
            # Create raw audio
            args = [
                ffmpeg(),
                "-y",
                "-ar",
                "48000",
                "-f",
                "s16le",
                "-i",
                random_source,
                "-t",
                str(length),
                raw_audio_file.name,
            ]
            _execute(args)
            for audio_def in audio_defs:
                audio_file = NamedTemporaryFile(
                    suffix=".{}".format(audio_def.codec.extension)
                )
                audio_files.append(audio_file)
                args = [
                    ffmpeg(),
                    "-y",
                    "-i",
                    raw_audio_file.name,
                    "-strict",
                    "-2",
                    "-c:a",
                    audio_def.codec.ffmpeg_codec_name,
                    "-ac",
                    str(audio_def.channels.num_channels),
                    "-t",
                    str(length),
                    audio_file.name,
                ]
                _execute(args)

    # ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 testsrc.mpg
    file = (
        NamedTemporaryFile(suffix=".{}".format(video_def.container.extension))
        if not output_file
        else output_file
    )

    args = [
        ffmpeg(),
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration={}:size={}x{}:rate=30".format(
            length, video_def.resolution.width, video_def.resolution.height
        ),
    ]

    for f in audio_files:
        args.extend(["-i", f.name])
    args.extend(["-c:v", video_def.codec.ffmpeg_encoder_name])

    if video_def.interlaced:
        args.extend(["-vf", "tinterlace=6"])

    if len(audio_defs) > 0:
        args.extend(["-c:a", "copy"])

    for i in range(len(audio_defs) + 1):
        args.extend(["-map", str(i)])

    if metadata:
        for key, value in metadata.items():
            args.extend(["-metadata", "{}={}".format(key, value)])

    if output_file:
        args.extend(["-t", str(length), output_file])
    else:
        args.extend(["-t", str(length), file.name])

    _execute(args)
    for f in audio_files:
        f.close()
    if not output_file:
        return file
