import sys
import os
from os import listdir
from os.path import isfile, join, basename, dirname
import re
import shutil

from tempita import Template

season_pattern = re.compile('Season (\d+)')


def pad(i):
    if i < 10:
        return '0' + str(i)
    else:
        return str(i)


def rename(season, episode, show, files, dry_run, output):
    for file in files:
        ext = os.path.splitext(file)[1]
        if show:
            new_name = '{} - S{}S{}{}'.format(show, season, pad(episode), ext)
        else:
            new_name = 'S{}E{}{}'.format(season, pad(episode), ext)

        if output:
            new_name = join(output, 'Season {}'.format(season), new_name)
        else:
            dir = dirname(file)
            new_name = join(dir, new_name)

        print('{}->{}'.format(file, new_name))
        if not dry_run:
            os.makedirs(os.path.dirname(new_name), exist_ok=True)
            shutil.move(file, new_name)
        episode += 1


def recursive_dir(dir):
    files = []
    dirs = []
    for f in listdir(dir):
        path = join(dir, f)
        if isfile(path):
            files.append(path)
        else:
            dirs.append(path)
    m = season_pattern.search(basename(dir))
    if m:
        season = m.group(1)
        rename(season, 1, files)
    for d in dirs:
        recursive_dir(d)


def run(input_dirs, season=1, episode=1, show=None, dry_run=False, output=None):
    files = []
    for input_dir in input_dirs:
        new_files = sorted(
            [join(input_dir, f) for f in listdir(input_dir) if isfile(join(input_dir, f)) and not f.startswith('.')])
        files.extend(new_files)
    season = pad(season)
    rename(season, episode, show, files, dry_run, output)


class RegexResults(object):
    def __init__(self, values=[], ignore_missing=False):
        self.values = values
        self.ignore_missing = ignore_missing

    def __iter__(self):
        return self.values

    def __getitem__(self, index):
        if index < 0 or index >= len(self.values):
            if self.ignore_missing:
                return None
            else:
                raise IndexError('Index out of bounds: {}'.format(index))
        else:
            return self.values[index]


def zpad(s, length=2):
    return str(s).rjust(length, '0')


def lpad(s, length=2):
    return str(s).rjust(length, ' ')


def ifempty(check, if_not_none, if_none=None):
    if if_none is None:
        return check if check is not None else if_not_none
    elif check is None:
        return if_not_none
    else:
        return if_none


RENAMER_NAMESPACE = {
    'lpad': lpad,
    'zpad': zpad,
    'ifempty': ifempty,
    'lower': lambda s: s.lower(),
    'upper': lambda s: s.upper(),
}


def rename_process(template, files, index_start=1, output_dir=None, regex=None, ignore_missing_regex=False, params={}):
    if regex:
        regex = re.compile(regex)

    t = Template(content=template, delimiters=('${', '}'), namespace=RENAMER_NAMESPACE)

    results = []

    index = index_start
    for file in files:
        if output_dir:
            dir = output_dir
        else:
            dir = os.path.dirname(file)
        ext = os.path.splitext(file)[1][1::]
        wo_ext = os.path.splitext(file)[0]
        base = os.path.basename(file)
        new_params = {
            'index': index,
            'i': index,
            'wo_ext': wo_ext,
            'ext': ext,
            'filename': base,
            're': RegexResults(ignore_missing=ignore_missing_regex)
        }
        new_params.update(params)
        if regex:
            m = regex.search(base)
            if m:
                items = [m.group()]
                m_index = 1
                for item in m.groups():
                    try:
                        item = int(item)
                    except ValueError:
                        pass
                    items.append(item)
                    m_index += 1
                    new_params['re'] = new_params['regex'] = RegexResults(items, ignore_missing=ignore_missing_regex)
        result = t.substitute(new_params)
        result = os.path.join(dir, result)
        results.append((file, result))
        index += 1

    return results
