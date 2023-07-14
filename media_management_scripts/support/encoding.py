from enum import Enum

DEFAULT_CRF = 15
DEFAULT_PRESET = "fast"


class Resolution(Enum):
    # Width, height, auto bitrate
    LOW_DEF = (360, 240, 500, "auto_bitrate_240")
    STANDARD_DEF = (720, 480, 1600, "auto_bitrate_480")
    MEDIUM_DEF = (1280, 720, 4500, "auto_bitrate_720")
    HIGH_DEF = (1920, 1080, 8000, "auto_bitrate_1080")
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

    @property
    def auto_bitrate_name(self):
        return self.value[3]


class BitDepth(Enum):
    BIT_8 = (8, "yuv420p")
    BIT_10 = (10, "yuv420p10le")
    BIT_12 = (12, "yuv420p12le")

    @property
    def bits(self):
        return self.value[0]

    @property
    def pix_fmt(self):
        return self.value[1]

    @staticmethod
    def get_from_pix_fmt(pix_fmt: str):
        for i in BitDepth:
            if i.pix_fmt == pix_fmt:
                return i
        return None


def resolution_name(height):
    if height <= 240:
        return Resolution.LOW_DEF
    elif height <= 576:
        return Resolution.STANDARD_DEF
    elif height <= 800:
        return Resolution.MEDIUM_DEF
    elif height <= 1080:
        return Resolution.HIGH_DEF
    else:
        return Resolution.ULTRA_HIGH_DEF


class VideoCodec(Enum):
    H264 = ("libx264", ["h264"])
    H265 = ("libx265", ["hevc", "h265"])
    MPEG2 = ("mpeg2video", ["mpeg2video", "mpeg2"])
    COPY = ("copy", ["copy"])

    @property
    def ffmpeg_encoder_name(self):
        return self.value[0]

    @property
    def ffmpeg_codec_name(self):
        return self.value[1][0]

    @property
    def codec_names(self):
        return self.value[1]

    @staticmethod
    def from_code_name(name):
        for vc in VideoCodec:
            for n in vc.codec_names:
                if name == n:
                    return vc
        return None

    def equals(self, to_comp: str) -> bool:
        """
        Compares all of the possible names to the value
        :param to_comp:
        :return:
        """
        return to_comp == self.ffmpeg_encoder_name or to_comp in self.codec_names


class AudioCodec(Enum):
    AAC = "aac"
    AC3 = "ac3"
    DTS = "dts"
    COPY = "copy"

    @property
    def extension(self):
        return self.value

    @property
    def ffmpeg_codec_name(self):
        return self.value

    @property
    def ffmpeg_encoder_name(self):
        return self.ffmpeg_codec_name

    def equals(self, to_comp: str) -> bool:
        """
        Compares all of the possible names to the value
        :param to_comp:
        :return:
        """
        return to_comp == self.ffmpeg_encoder_name


class AudioChannelName(Enum):
    MONO = (1, ["mono"])
    STEREO = (2, ["stereo"])
    SURROUND_5_1 = (6, ["surround", "5.1"])
    SURROUND_6_1 = (7, ["6.1"])
    SURROUND_7_1 = (8, ["7.1"])

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
        for ac in AudioChannelName:
            for n in ac.names:
                if n == name:
                    return ac
        return None


class VideoFileContainer(Enum):
    MP4 = "mp4"
    MKV = "mkv"
    MPEG = "mpeg"
    WTV = "wtv"

    @property
    def extension(self):
        return self.value


class H264Preset(Enum):
    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    VERYSLOW = "veryslow"
    PLACEBO = "placebo"

    @staticmethod
    def from_value(value):
        for preset in H264Preset:
            if preset.value == value:
                return preset
        return None
