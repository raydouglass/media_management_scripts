from media_management_scripts.support.encoding import Resolution, VideoCodec, VideoFileContainer, AudioCodec, \
    AudioChannelName
from media_management_scripts.support.executables import ffmpeg, ffprobe
from tempfile import NamedTemporaryFile
from media_management_scripts.convert_dvd import execute
from typing import List, Tuple, NamedTuple


class VideoDefinition(NamedTuple):
    resolution: Resolution = Resolution.LOW_DEF
    codec: VideoCodec = VideoCodec.H264
    container: VideoFileContainer = VideoFileContainer.MKV


DEFAULT_VIDEO_DEFINITION = VideoDefinition(Resolution.LOW_DEF, VideoCodec.H264, VideoFileContainer.MKV)


class AudioDefition(NamedTuple):
    codec: AudioCodec = AudioCodec.AAC
    channels: AudioChannelName = AudioChannelName.STEREO


DEFAULT_AUDIO_DEFINITION = AudioDefition(AudioCodec.AAC, AudioChannelName.STEREO)


def _execute(args):
    ret = execute(args, print_output=True)
    if ret != 0:
        raise Exception('Failed to create test video')


def create_test_video(length: int = 30,
                      video_def: VideoDefinition = DEFAULT_VIDEO_DEFINITION,
                      audio_defs: List[AudioDefition] = [DEFAULT_AUDIO_DEFINITION]):
    audio_files = []
    if len(audio_defs) > 0:
        with NamedTemporaryFile(suffix='.wav') as raw_audio_file:
            # Create raw audio
            args = [ffmpeg(), '-y', '-ar', '48000', '-f', 's16le', '-i', '/dev/urandom', '-t', str(length),
                    raw_audio_file.name]
            _execute(args)
            for audio_def in audio_defs:
                audio_file = NamedTemporaryFile(suffix='.{}'.format(audio_def.codec.extension))
                audio_files.append(audio_file)
                args = [ffmpeg(), '-y', '-i', raw_audio_file.name, '-c:a', audio_def.codec.ffmpeg_codec_name, '-ac',
                        str(audio_def.channels.num_channels), '-t', str(length), audio_file.name]
                _execute(args)

    # ffmpeg -f lavfi -i testsrc=duration=10:size=1280x720:rate=30 testsrc.mpg
    file = NamedTemporaryFile(suffix='.{}'.format(video_def.container.extension))
    args = [ffmpeg(), '-y', '-f', 'lavfi', '-i',
            'testsrc=duration={}:size={}x{}:rate=30'.format(length, video_def.resolution.width,
                                                            video_def.resolution.height)]
    for f in audio_files:
        args.extend(['-i', f.name])

    args.extend(['-c:v', video_def.codec.ffmpeg_encoder_name])
    if len(audio_defs) > 0:
        args.extend(['-c:a', 'copy'])

    for i in range(len(audio_defs) + 1):
        args.extend(['-map', str(i)])

    args.extend(['-t', str(length), file.name])

    _execute(args)
    for f in audio_files:
        f.close()
    return file


def assertAudioLength(expected: int, actual: int):
    """
    Checks if the actualy is within 2% of the expected. This is required because conversion to AAC adds a tiny amount of time
    :param expected: 
    :param actual: 
    :return: 
    """
    min = expected
    max = expected * 1.02
    if not (min <= actual <= max):
        raise AssertionError('{} != {} ({}-{})'.format(expected, actual, min, max))
