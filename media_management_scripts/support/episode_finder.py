import os
import re
import sys
from os import listdir
from os.path import isfile, join, basename
from typing import Tuple
import functools

from media_management_scripts.utils import compare

patterns = [(re.compile('[Ss](\d?\d),?\s*[Ee](\d?\d)'), 1, 2),
            (re.compile('(\d?\d)x(\d?\d)'), 1, 2),
            (re.compile('[Ss]eries\s*(\d+).*[Ee]pisode\s*(\d+)'), 1, 2),
            (re.compile('[Ss]eason\s*(\d+).*[Ee]pisode\s*(\d+)'), 1, 2),
            (re.compile('[Ss]eason\s*(\d+).*[Ee]pisode.?\s*(\d+)'), 1, 2)]
pattern_101 = re.compile('(\d)(\d\d)')

part_patterns = [re.compile('[Pp]art\s*(\d+)'), re.compile('pt\s*(\d+)')]


@functools.total_ordering
class EpisodePart():
    def __init__(self, name, path, season, episode, part):
        self.name = name
        self.path = path
        if season is not None:
            self.season = int(season)
        else:
            self.season = None
        if episode is not None:
            self.episode = int(episode)
        else:
            self.episode = None
        self.part = part

    def __str__(self):
        if self.season is None or self.episode is None:
            return '{}: No match'.format(self.name)
        if self.part is not None:
            return '{}: s{:02d}e{:02d} pt{}'.format(self.name, self.season, self.episode, self.part)
        else:
            return '{}: s{:02d}e{:02d}'.format(self.name, self.season, self.episode)

    def __repr__(self):
        return self.__str__()

    @property
    def season_episode(self):
        if self.part is not None:
            return 'S{:02d}E{:02d} pt{}'.format(self.season, self.episode, self.part)
        else:
            return 'S{:02d}E{:02d}'.format(self.season, self.episode)

    def __eq__(self, other):
        if issubclass(type(other), EpisodePart):
            return self.name == other.name and self.season == other.season \
                   and self.episode == other.episode and self.part == other.part
        return False

    def __gt__(self, other):
        if not issubclass(type(other), EpisodePart):
            raise Exception()
        cmp = compare(self.season, other.season)
        if cmp == 0:
            cmp = compare(self.episode, other.episode)
        if cmp == 0:
            cmp = compare(self.part, other.part)
        if cmp == 0:
            cmp = compare(self.name, other.name)
        if cmp <= 0:
            return True
        return False


def extract(name, use101=False) -> Tuple[int, int, int]:
    season = None
    ep = None
    part = None
    for pattern, season_group, episode_group in patterns:
        m = pattern.search(name)
        if m:
            season = m.group(season_group)
            ep = m.group(episode_group)
            break
    if season is None and ep is None and use101:
        m = pattern_101.search(name)
        if m:
            season = m.group(1)
            ep = m.group(2)
    for pattern in part_patterns:
        m = pattern.search(name)
        if m:
            part = m.group(1)
            break
    return season, ep, part


def find_episodes(dir, strip_youtubedl, use101=False):
    for root, subdirs, files in os.walk(dir):
        for file in files:
            path = os.path.join(root, file)
            name = basename(file)
            if strip_youtubedl:
                try:
                    index = name.index(' - ')
                    name = name[index + 3::]
                except ValueError:
                    pass
            season, ep, part = extract(name, use101)
            yield EpisodePart(name, path, season, ep, part)


if __name__ == '__main__':
    left = EpisodePart('left', 'left', 1, 2, None)
    right = EpisodePart('right', 'right', 1, None, None)
    print(left > right)
