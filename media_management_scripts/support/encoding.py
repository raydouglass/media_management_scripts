from enum import Enum

DEFAULT_CRF = 15
DEFAULT_PRESET = 'fast'


class Resolution(Enum):
    # Width, height, auto bitrate
    LOW_DEF = (360, 240, 500)
    STANDARD_DEF = (720, 480, 1500)
    MEDIUM_DEF = (1280, 720, 3500)
    HIGH_DEF = (1920, 1080, 6000)
    ULTRA_HIGH_DEF = (3840, 2160, None)

    @property
    def width(self):
        return self.value[0]

    @property
    def height(self):
        return self.value[1]

    @property
    def auto_bitrate(self):
        return self.value[2]


def resolution_name(height):
    if height <= 576:
        return Resolution.STANDARD_DEF
    elif height <= 800:
        return Resolution.MEDIUM_DEF
    elif height <= 1080:
        return Resolution.HIGH_DEF
    else:
        return Resolution.ULTRA_HIGH_DEF


class VideoCodec(Enum):
    H264 = ('libx264', 'h264')
    H265 = ('libx265', 'hevc')
    MPEG2 = ('mpeg2video', 'mpeg2video')

    @property
    def ffmpeg_encoder_name(self):
        return self.value[0]

    @property
    def ffmpeg_codec_name(self):
        return self.value[1]


class AudioCodec(Enum):
    AAC = 'aac'
    AC3 = 'ac3'
    DTS = 'dts'

    @property
    def extension(self):
        return self.value

    @property
    def ffmpeg_codec_name(self):
        return self.value


class AudioChannelName(Enum):
    MONO = (1, ['mono'])
    STEREO = (2, ['stereo'])
    SURROUND_5_1 = (6, ['surround', '5.1'])
    SURROUND_6_1 = (7, ['6.1'])
    SURROUND_7_1 = (8, ['7.1'])

    @property
    def num_channels(self):
        return self.value[0]

    @property
    def names(self):
        return self.value[1]

    @property
    def name(self):
        return self.names()[0]

    @staticmethod
    def from_name(name):
        for ac in list(AudioChannelName):
            for n in ac.names:
                if n == name:
                    return ac
        return None


class VideoFileContainer(Enum):
    MP4 = 'mp4'
    MKV = 'mkv'

    @property
    def extension(self):
        return self.value


class H264Preset(Enum):
    ULTRAFAST = 'ultrafast'
    SUPERFAST = 'superfast'
    VERYFAST = 'veryfast'
    FASTER = 'faster'
    FAST = 'fast'
    MEDIUM = 'medium'
    SLOW = 'slow'
    VERYSLOW = 'veryslow'
    PLACEBO = 'placebo'

    @staticmethod
    def from_value(value):
        for preset in list(H264Preset):
            if preset.value == value:
                return preset
        return None
