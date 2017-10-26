from media_management_scripts.support.metadata import MetadataExtractor, Metadata
from typing import Iterable


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
    return MetadataExtractor({'ffprobe_exe': '/usr/local/bin/ffprobe'}, db_file=db_file)


def extract_metadata(input: str, detect_interlace=False, db_file=None) -> Metadata:
    return create_metadata_extractor(db_file=db_file).extract(input, detect_interlace)


def season_episode_name(season, episode, ext=None):
    if ext:
        if not ext.startswith('.'):
            ext = '.' + ext
        return 's{}e{:02d}{}'.format(season, int(episode), ext)
    else:
        return 's{}e{:02d}'.format(season, int(episode))


def fuzzy_equals(a: str, b: str, ignore_chars: Iterable[str] = [], ratio: float = .85) -> bool:
    from difflib import SequenceMatcher
    ifignore = (lambda x: x in ignore_chars) if ignore_chars else None
    return SequenceMatcher(ifignore, a, b).ratio() >= ratio


def fuzzy_equals_word(a: str, b: str, ratio: float = .85):
    from difflib import SequenceMatcher
    import re
    pattern = re.compile('\w+')
    ifignore = lambda x: pattern.match(x) is None
    return SequenceMatcher(ifignore, a, b).ratio() >= ratio
