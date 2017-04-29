import os

from media_management_scripts.support.metadata import MetadataExtractor


def compare_gt(this, other):
    if this is not None and other is not None:
        return this > other
    elif this is not None:
        return True
    else:
        return False


def compare_lt(this, other):
    return not compare_gt(this, other)


def ALL_FILES(dir, file):
    return True


def ALL_NONHIDDEN_FILES(dir, file):
    return not file.startswith('.')


def MOVIE_FILES(dir, file):
    file = file.lower()
    return file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.m4v')


def find_files(dir, filter=ALL_NONHIDDEN_FILES):
    for root, subdirs, files in os.walk(dir):
        for file in files:
            if filter(root, file):
                yield os.path.join(root, file)


def list_files(input_dir):
    for root, subdirs, files in os.walk(input_dir):
        for file in files:
            path = os.path.join(root, file).replace(input_dir, '')
            yield path


def get_input_output(input_dir, output_dir, filter=ALL_NONHIDDEN_FILES):
    for file in sorted(list_files(input_dir)):
        input_file = os.path.join(input_dir, file)
        if filter(os.path.dirname(input_file), os.path.basename(input_file)):
            output_file = os.path.join(output_dir, file)
            yield input_file, output_file


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def create_metadata_extractor() -> MetadataExtractor:
    return MetadataExtractor({'ffprobe_exe': '/usr/local/bin/ffprobe'})


def season_episode_name(season, episode, ext=None):
    if ext:
        if not ext.startswith('.'):
            ext = '.' + ext
        return 's{}e{:02d}{}'.format(season, int(episode), ext)
    else:
        return 's{}e{:02d}'.format(season, int(episode))
