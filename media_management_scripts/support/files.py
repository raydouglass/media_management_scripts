import os

from typing import Callable, Tuple, Iterator

import logging

logger = logging.getLogger(__name__)


def mp4_mkv_filter(f: str) -> bool:
    return f.endswith('.mkv') or f.endswith('.mp4')


def all_files_filter(f: str) -> bool:
    return True


def movie_files_filter(file):
    return file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi') or file.endswith('.m4v')


def check_exists(output: str):
    if os.path.exists(output):
        logger.warning('Cowardly refusing to overwrite existing file: {}'.format(output))
        return True
    return False


def create_dirs(file: str):
    dir = os.path.dirname(file)
    if dir:
        os.makedirs(dir, exist_ok=True)


def list_files(input_dir: str,
               filter: Callable[[str], bool] = mp4_mkv_filter) -> Iterator[str]:
    for root, subdirs, files in os.walk(input_dir):
        for file in files:
            if not file.startswith('.') and filter(file):
                path = os.path.join(root.replace(input_dir, ''), file)
                if path.startswith('/'):
                    path = path[1::]
                yield path


def get_input_output(input_dir: str,
                     output_dir: str,
                     work_dir: str = None,
                     filter: Callable[[str], bool] = mp4_mkv_filter) -> Iterator[Tuple[str, ...]]:
    for file in sorted(list_files(input_dir, filter)):
        input_file = os.path.join(input_dir, file)
        output_file = os.path.join(output_dir, file)
        if work_dir:
            work_file = os.path.join(work_dir, file)
            yield input_file, output_file, work_file
        else:
            yield input_file, output_file