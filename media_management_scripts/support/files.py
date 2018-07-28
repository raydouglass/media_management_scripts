import os

from typing import Callable, Tuple, Iterator

import logging

logger = logging.getLogger(__name__)


def mp4_mkv_filter(f: str) -> bool:
    return f.endswith('.mkv') or f.endswith('.mp4')


def all_files_filter(f: str) -> bool:
    return True


def movie_files_filter(file):
    return os.path.isfile(file) and \
           (file.endswith('.mkv') or \
            file.endswith('.mp4') or \
            file.endswith('.avi') or \
            file.endswith('.m4v') or \
            file.endswith('.webm') or \
            get_mime(file).startswith('video/'))


def get_mime(file):
    import magic
    return magic.from_file(file, mime=True)


def check_exists(output: str, log=True):
    if os.path.exists(output):
        if log:
            logger.warning('Cowardly refusing to overwrite existing file: {}'.format(output))
        return True
    return False


def create_dirs(file: str):
    dir = os.path.dirname(file)
    if dir:
        os.makedirs(dir, exist_ok=True)


def list_files(input_dir: str,
               file_filter: Callable[[str], bool] = mp4_mkv_filter) -> Iterator[str]:
    """
    List relative files in directory
    """
    for root, subdirs, files in os.walk(input_dir):
        for file in files:
            if not file.startswith('.') and file_filter(os.path.join(root, file)):
                path = os.path.join(root.replace(input_dir, ''), file)
                if path.startswith('/'):
                    path = path[1::]
                yield path


def get_files_in_directories(input_dirs, file_filter: Callable[[str], bool] = mp4_mkv_filter) -> Iterator[str]:
    for input_dir in input_dirs:
        if os.path.isdir(input_dir):
            for f in list_files(input_dir, file_filter=file_filter):
                yield os.path.join(input_dir, f)
        else:
            yield input_dir


def get_input_output(input_dir: str,
                     output_dir: str,
                     work_dir: str = None,
                     filter: Callable[[str], bool] = mp4_mkv_filter) -> Iterator[Tuple[str, ...]]:
    """
    Mimic the file structure from input_dir into output_dir (and optionally work_dir.

    The input files are filtered
    """
    for file in sorted(list_files(input_dir, filter)):
        input_file = os.path.join(input_dir, file)
        output_file = os.path.join(output_dir, file)
        if work_dir:
            work_file = os.path.join(work_dir, file)
            yield input_file, output_file, work_file
        else:
            yield input_file, output_file
