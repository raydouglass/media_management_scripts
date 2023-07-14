import os
import subprocess
import tempfile
from media_management_scripts.support.executables import ffmpeg, execute_with_output
from media_management_scripts.utils import extract_metadata
from media_management_scripts.support.encoding import VideoCodec, AudioCodec


def _temp_convert(input, output, print_output=False):
    # ffmpeg -i input1.mp4 -c copy -bsf:v h264_mp4toannexb -f mpegts intermediate1.ts
    print("Converting {}".format(input))
    args = [
        ffmpeg(),
        "-loglevel",
        "fatal",
        "-i",
        input,
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-c:s",
        "copy",
        "-bsf:v",
        "h264_mp4toannexb",
        "-f",
        "mpegts",
        output,
    ]
    ret, r = execute_with_output(args, print_output=print_output)
    if ret != 0:
        raise Exception("Error during ffmpeg: {}".format(r))


def _concat(files, output, print_output=False):
    # ffmpeg -i "concat:intermediate1.ts|intermediate2.ts" -c copy -bsf:a aac_adtstoasc output.mp4
    concat_str = "concat:"
    for f in files:
        concat_str += f + "|"
    concat_str = concat_str[0:-1]
    print(concat_str)
    args = [
        ffmpeg(),
        "-loglevel",
        "fatal",
        "-y",
        "-i",
        concat_str,
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-c:s",
        "copy",
        "-bsf:a",
        "aac_adtstoasc",
        output,
    ]
    ret, r = execute_with_output(args, print_output=print_output)
    if ret != 0:
        raise Exception("Error during ffmpeg: {}".format(r))


def _validate_file(file):
    metadata = extract_metadata(file)
    if len(metadata.video_streams) != 1:
        raise Exception("Not exactly 1 video stream in {}".format(file))
    if not VideoCodec.H264.equals(metadata.video_streams[0].codec):
        raise Exception("File not H264: {}".format(file))
    non_aac_audio = [
        a for a in metadata.audio_streams if not AudioCodec.AAC.equals(a.codec)
    ]
    if non_aac_audio:
        raise Exception("Not all audio streams are AAC: {}".format(file))


def concat_mp4(output, files, overwrite=False, print_output=False):
    if not overwrite and os.path.exists(output):
        print("Cowardly refusing to overwrite existing file: {}".format(output))
        return
    temp_files = []
    try:
        for f in files:
            file = os.path.abspath(f)
            _validate_file(file)
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".ts").name
            temp_files.append(tmp)
            _temp_convert(file, tmp, print_output)
        _concat(temp_files, output, print_output)
    finally:
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)
