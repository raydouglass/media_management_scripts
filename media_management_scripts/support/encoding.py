from enum import Enum

DEFAULT_CRF = 15
DEFAULT_PRESET = 'fast'

HIGH_DEF_AUTO_BITRATE = 10000

PIXELS_1080 = 1920 * 1080


class Resolution(Enum):
    STANDARD_DEF = (720, 480)
    MEDIUM_DEF = (1280, 720)
    HIGH_DEF = (1920, 1080)
    ULTRA_HIGH_DEF = (3840, 2160)

    def auto_bitrate(self):
        pixels = self.value[0] * self.value[1]
        return int(pixels / PIXELS_1080 * HIGH_DEF_AUTO_BITRATE)

    @property
    def width(self):
        return self.value[0]

    @property
    def height(self):
        return self.value[1]


def resolution_name(height):
    if height <= 576:
        return Resolution.STANDARD_DEF
    elif height <= 800:
        return Resolution.MEDIUM_DEF
    elif height <= 1080:
        return Resolution.HIGH_DEF
    else:
        return Resolution.ULTRA_HIGH_DEF
