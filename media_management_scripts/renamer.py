import sys
import os
from os import listdir
from os.path import isfile, join, basename, dirname
import re

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
            new_name = '{} - s{}e{}{}'.format(show, season, pad(episode), ext)
        else:
            new_name = 's{}e{}{}'.format(season, pad(episode), ext)

        if output:
            new_name = join(output, new_name)
        else:
            dir = dirname(file)
            new_name = join(dir, new_name)

        print('{}->{}'.format(file, new_name))
        if not dry_run:
            os.rename(file, new_name)
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


def ifempty(s, replacement):
    return s if s is not None else replacement


def rename_process(template, files, index_start=1, output_dir=None, regex=None, ignore_missing_regex=False):
    if regex:
        regex = re.compile(regex)
    namespace = {
        'lpad': lpad,
        'zpad': zpad,
        'ifempty': ifempty,
        'lower': lambda s: s.lower(),
        'upper': lambda s: s.upper(),
    }
    t = Template(content=template, delimiters=('${', '}'), namespace=namespace)

    results = []

    index = index_start
    for file in files:
        if output_dir:
            dir = output_dir
        else:
            dir = os.path.dirname(file)
        ext = os.path.splitext(file)[1][1::]
        basename = os.path.basename(file)
        params = {
            'index': index,
            'i': index,
            'ext': ext,
            'filename': basename,
            're': RegexResults(ignore_missing=ignore_missing_regex)
        }
        if regex:
            m = regex.search(file)
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
                params['re'] = params['regex'] = RegexResults(items, ignore_missing=ignore_missing_regex)
        result = t.substitute(params)
        result = os.path.join(dir, result)
        results.append((file, result))
        index += 1

    return results
