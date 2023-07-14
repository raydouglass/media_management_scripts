from media_management_scripts.support.encoding import (
    DEFAULT_CRF,
    DEFAULT_PRESET,
    Resolution,
    VideoCodec,
    AudioCodec,
)
from media_management_scripts.support.metadata import MetadataExtractor, Metadata
from typing import Iterable, NamedTuple
from configparser import ConfigParser
from media_management_scripts.support.executables import ffprobe


def to_int(maybe_int) -> int:
    if maybe_int is None:
        return None
    try:
        return int(maybe_int)
    except ValueError:
        return None


def compare_gt(this, other):
    if this is not None and other is not None:
        return int(this > other)
    elif this is not None:
        return -1
    else:
        return 1


def compare(this, other):
    if this is not None and other is not None:
        if this == other:
            return 0
        else:
            return -1 if this > other else 1
    elif this is not None:
        return 1
    else:
        return -1


def compare_lt(this, other):
    return -compare_gt(this, other)


def create_metadata_extractor(db_file=None) -> MetadataExtractor:
    return MetadataExtractor({"ffprobe_exe": ffprobe()}, db_file=db_file)


def extract_metadata(input: str, detect_interlace=False, db_file=None) -> Metadata:
    return create_metadata_extractor(db_file=db_file).extract(input, detect_interlace)


def season_episode_name(season, episode, episode_name=None, ext=None):
    if ext:
        if not ext.startswith("."):
            ext = "." + ext
        if episode_name:
            return "S{:02d}E{:02d} - {}{}".format(
                int(season), int(episode), episode_name, ext
            )
        else:
            return "S{:02d}E{:02d}{}".format(int(season), int(episode), ext)
    else:
        if episode_name:
            return "S{:02d}E{:02d} - {}".format(int(season), int(episode), episode_name)
        else:
            return "S{:02d}E{:02d}".format(int(season), int(episode))


def fuzzy_equals(
    a: str, b: str, ignore_chars: Iterable[str] = [], ratio: float = 0.85
) -> bool:
    from difflib import SequenceMatcher

    ifignore = (lambda x: x in ignore_chars) if ignore_chars else None
    return SequenceMatcher(ifignore, a, b).ratio() >= ratio


def fuzzy_equals_word(a: str, b: str, ratio: float = 0.85):
    from difflib import SequenceMatcher
    import re

    pattern = re.compile(r"\w+")
    ifignore = lambda x: pattern.match(x) is None
    return SequenceMatcher(ifignore, a, b).ratio() >= ratio


class ConvertConfig(NamedTuple):
    crf: int = DEFAULT_CRF
    preset: str = DEFAULT_PRESET
    bitrate: str = None
    include_meta: bool = False
    deinterlace: bool = False
    deinterlace_threshold: float = 0.5
    include_subtitles: bool = True
    start: float = None
    end: float = None
    auto_bitrate_240: int = Resolution.LOW_DEF.auto_bitrate
    auto_bitrate_480: int = Resolution.STANDARD_DEF.auto_bitrate
    auto_bitrate_720: int = Resolution.MEDIUM_DEF.auto_bitrate
    auto_bitrate_1080: int = Resolution.HIGH_DEF.auto_bitrate
    scale: int = None
    video_codec: str = VideoCodec.H264.ffmpeg_encoder_name
    audio_codec: str = AudioCodec.AAC.ffmpeg_codec_name


def convert_config_from_config_section(
    config: ConfigParser, section: str
) -> ConvertConfig:
    """
    Creates a ConvertConfig from a configparser section.

    All options are optional with sane defaults:
      [section.name]
      crf = 16
      preset = fast
      bitrate = disabled # (disabled|auto|int)
      deinterlace = False
      deinterlace_threshold = .5
      auto_bitrate_240 = 500
      auto_bitrate_480 = 1600
      auto_bitrate_720 = 4500
      auto_bitrate_1080 = 8000
      include_subtitles = True
      ripped = False

    :param config:
    :param section:
    :return:
    """
    # Transcode
    crf = config.get(section, "crf", fallback=DEFAULT_CRF)
    preset = config.get(section, "preset", fallback=DEFAULT_PRESET)
    bitrate = config.get(section, "bitrate", fallback="disabled")
    if bitrate == "disabled":
        bitrate = None
    elif bitrate and bitrate != "auto":
        try:
            int(bitrate)
        except ValueError:
            raise Exception(
                "Bitrate in [{}] must be 'auto', 'disabled' or an integer".format(
                    section
                )
            )
    deinterlace = bool(config.get(section, "deinterlace", fallback=False))
    deinterlace_threshold = float(
        config.get(section, "deinterlace_threshold", fallback=".5")
    )

    auto_bitrate_240 = config.getint(
        section, "auto_bitrate_240", fallback=Resolution.LOW_DEF.auto_bitrate
    )
    auto_bitrate_480 = config.getint(
        section, "auto_bitrate_480", fallback=Resolution.STANDARD_DEF.auto_bitrate
    )
    auto_bitrate_720 = config.getint(
        section, "auto_bitrate_720", fallback=Resolution.MEDIUM_DEF.auto_bitrate
    )
    auto_bitrate_1080 = config.getint(
        section, "auto_bitrate_1080", fallback=Resolution.HIGH_DEF.auto_bitrate
    )

    include_subtitles = config.getboolean(section, "include_subtitles", fallback=True)
    ripped = config.getboolean(section, "ripped", fallback=False)

    return ConvertConfig(
        crf=crf,
        preset=preset,
        bitrate=bitrate,
        auto_bitrate_240=auto_bitrate_240,
        auto_bitrate_480=auto_bitrate_480,
        auto_bitrate_720=auto_bitrate_720,
        auto_bitrate_1080=auto_bitrate_1080,
        deinterlace=deinterlace,
        deinterlace_threshold=deinterlace_threshold,
        include_subtitles=include_subtitles,
        include_meta=ripped,
    )
