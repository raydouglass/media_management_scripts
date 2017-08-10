import json
import re
from datetime import datetime
from typing import NamedTuple, Iterable
import os
import itertools


class TvShow(NamedTuple):
    file_path: str
    show: str
    network: str
    recorded_datetime: datetime


def _parse_dir(dir) -> Iterable[TvShow]:
    pattern = re.compile('(.+)_(.+)_(\d{4})_(\d\d)_(\d\d)_(\d\d)_(\d\d)_(\d\d).wtv')
    for file in os.listdir(dir):
        m = pattern.search(file)
        if m:
            filepath = os.path.join(dir, file)
            show = m.group(1)
            network = m.group(2)
            recorded_datetime = datetime(year=int(m.group(3)), month=int(m.group(4)), day=int(m.group(5)),
                                         hour=int(m.group(6)), minute=int(m.group(7)), second=int(m.group(8)))
            yield TvShow(filepath, show, network, recorded_datetime)


def run_delete(config_file, dry_run=True):
    """
    Deletes WTV files in a directory based on a configuration file
    :param config_file:
    :param dry_run:
    :return:
    """
    with open(config_file, 'r') as file:
        config = json.load(file)

    dir = config['directory']
    tv_shows_config = config['tv_shows']

    key = lambda x: x.show

    for show, files in itertools.groupby(sorted(_parse_dir(dir), key=key), key=key):
        if show in tv_shows_config:
            files = list(files)
            max_count = tv_shows_config[show]
            num_to_delete = len(files) - max_count
            if max_count > 0 and num_to_delete > 0:
                files.sort(key=lambda x: x.recorded_datetime)
                to_delete = files[:num_to_delete]
                for d in to_delete:
                    print('{}'.format(os.path.basename(d.file_path)))
                    if not dry_run:
                        os.remove(d.file_path)
