import os
import re
import sys
from os import listdir
from os.path import isfile, join, basename
from typing import Tuple

from media_management_scripts.utils import compare_gt

patterns = [re.compile('[Ss](\d?\d)\s*[Ee](\d?\d)'),
            re.compile('(\d?\d)x(\d?\d)'),
            re.compile('[Ss]eries\s*(\d+).*[Ee]pisode\s*(\d+)'),
            re.compile('[Ss]eason\s*(\d+).*[Ee]pisode\s*(\d+)'),
            re.compile('(\d)(\d\d)')]

part_patterns = [re.compile('[Pp]art\s*(\d+)'), re.compile('pt\s*(\d+)')]


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
        if not self.season or not self.episode:
            return '{}: No match'.format(self.name)
        if self.part:
            return '{}: s{}e{:02d} pt{}'.format(self.name, self.season, self.episode, self.part)
        else:
            return '{}: s{}e{:02d}'.format(self.name, self.season, self.episode)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if issubclass(other.__cls__, EpisodePart):
            return self.season == other.season and self.episode == other.episode and self.part == other.part
        return False

    def __gt__(self, other):
        if compare_gt(self.season, other.season):
            return True
        elif compare_gt(self.episode, other.episode):
            return True
        elif compare_gt(self.part, other.part):
            return True
        else:
            return self.name > other.name

    def __lt__(self, other):
        return not self.__gt__(other)


def extract(name) -> Tuple[int, int, int]:
    season = None
    ep = None
    part = None
    for pattern in patterns:
        m = pattern.search(name)
        if m:
            season = m.group(1)
            ep = m.group(2)
            if season == '1' and ep == '01':
                season = None
                ep = None
            else:
                break
    for pattern in part_patterns:
        m = pattern.search(name)
        if m:
            part = m.group(1)
            break
    return season, ep, part


def find_episodes(dir, strip_youtubedl):
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
            season, ep, part = extract(name)
            yield EpisodePart(name, path, season, ep, part)


def main(dir):
    files = sorted([f for f in listdir(dir) if isfile(join(dir, f)) and not f.startswith('.')])
    for file in files:
        name = basename(file)[6::]
        season, ep, part = extract(name)
