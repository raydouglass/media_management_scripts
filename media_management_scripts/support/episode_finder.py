import os
import re
from typing import Tuple, Iterator, Iterable
import functools

from media_management_scripts.utils import compare, season_episode_name, to_int
from media_management_scripts.support.files import (
    list_files,
    movie_and_subtitle_files_filter,
)

patterns = [
    (re.compile(r"[Ss](\d+),?\s*[Ee](\d+)"), 1, 2),
    (re.compile(r"(\d+)x(\d+)"), 1, 2),
    (re.compile(r"[Ss]eries\s*(\d+).*[Ee]pisode\s*(\d+)"), 1, 2),
    (re.compile(r"[Ss]eason\s*(\d+).*[Ee]pisode\s*(\d+)"), 1, 2),
    (re.compile(r"[Ss]eason\s*(\d+).*[Ee]pisode.?\s*(\d+)"), 1, 2),
]
pattern_101 = re.compile(r"(\d)(\d\d)")

part_patterns = [re.compile(r"[Pp]art\s*(\d+)"), re.compile("pt\s*(\d+)")]


@functools.total_ordering
class EpisodePart:
    def __init__(self, name, path, season, episode, part):
        self.name = name
        self.path = path
        self.season = season
        self.episode = episode
        self.part = part

    def __str__(self):
        if self.season is None or self.episode is None:
            return "{}: No match".format(self.name)
        if self.part is not None:
            return "{}: S{:02d}E{:02d} pt{}".format(
                self.name, self.season, self.episode, self.part
            )
        else:
            return "{}: S{:02d}E{:02d}".format(self.name, self.season, self.episode)

    def __repr__(self):
        return self.__str__()

    @property
    def season_episode(self):
        if self.part is not None:
            return "S{:02d}E{:02d} pt{}".format(self.season, self.episode, self.part)
        else:
            return "S{:02d}E{:02d}".format(self.season, self.episode)

    def __eq__(self, other):
        if issubclass(type(other), EpisodePart):
            return (
                self.name == other.name
                and self.season == other.season
                and self.episode == other.episode
                and self.part == other.part
            )
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
    return to_int(season), to_int(ep), to_int(part)


def find_episodes(dir, use101=False) -> Iterator[EpisodePart]:
    for path in list_files(dir, movie_and_subtitle_files_filter):
        name = os.path.basename(path)
        name, _ = os.path.splitext(name)
        season, ep, part = extract(name, use101)
        path = os.path.join(dir, path)
        yield EpisodePart(name, path, season, ep, part)


def calculate_new_filenames(
    episodes: Iterable[EpisodePart], output_dir, use_season_folders, show_name
):
    for ep in episodes:
        if ep.season and ep.episode:
            path = ep.path
            filename = os.path.basename(path)
            name, ext = os.path.splitext(filename)

            new_name = season_episode_name(ep.season, int(ep.episode), ep.name, ext)
            if show_name:
                new_name = "{} - {}".format(show_name, new_name)
            if use_season_folders:
                season_f = "Season {:02d}".format(ep.season)
            else:
                season_f = None

            if show_name and season_f:
                out_file = os.path.join(output_dir, show_name, season_f, new_name)
            elif show_name:
                out_file = os.path.join(output_dir, show_name, new_name)
            elif season_f:
                out_file = os.path.join(output_dir, season_f, new_name)
            else:
                out_file = os.path.join(output_dir, new_name)
            yield ep.path, ep.season_episode, out_file
        else:
            yield ep.path, None, None
