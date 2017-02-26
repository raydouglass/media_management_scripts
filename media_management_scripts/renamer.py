import sys
import os
from os import listdir
from os.path import isfile, join, basename, dirname
import re

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
        new_files=sorted([join(input_dir, f) for f in listdir(input_dir) if isfile(join(input_dir, f)) and not f.startswith('.')])
        files.extend(new_files)
    season = pad(season)
    rename(season, episode, show, files, dry_run, output)


def main():
    if len(sys.argv) == 2:
        recursive_dir(sys.argv[1])
        return
    if len(sys.argv) != 4:
        print('Need 3 args: <dir> <season> <starting episode>')
        sys.exit(1)
    files = sorted([f for f in listdir(sys.argv[1]) if isfile(join(sys.argv[1], f)) and not f.startswith('.')])
    season = pad(sys.argv[2])
    episode = int(sys.argv[3])
    rename(season, episode, files)


if __name__ == '__main__':
    main()
