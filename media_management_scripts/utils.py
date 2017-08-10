from media_management_scripts.support.metadata import MetadataExtractor, Metadata


def compare_gt(this, other):
    if this is not None and other is not None:
        return this > other
    elif this is not None:
        return True
    else:
        return False


def compare_lt(this, other):
    return not compare_gt(this, other)


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
