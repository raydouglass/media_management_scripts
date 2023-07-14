import os
import re

from tempita import Template
from typing import NamedTuple, Tuple

season_pattern = re.compile(r"Season (\d+)")
PLEX_TEMPLATE = '${show}/${season|plex_season_specials}/${show} - S${season|zpad}${plex_episode(episode_num, episode_num_final)}${ifempty(episode_name, "", " - "+str(episode_name))}.${ext}'


class PlexTemplateParams(NamedTuple):
    show: str = None
    season: int = None
    episode_num: int = None
    episode_name: str = None
    episode_num_final: int = None


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
                raise IndexError("Index out of bounds: {}".format(index))
        else:
            return self.values[index]


def ifempty(check, if_none, if_not_none):
    if check:
        return if_not_none
    else:
        return if_none


_RENAMER_NAMESPACE = {
    "ifempty": ifempty,
    "lower": lambda s: s.lower(),
    "upper": lambda s: s.upper(),
}


def create_namespace(size: int = 2):
    length = max(2, len(str(size)))

    def zpad(s, length=length):
        return str(s).rjust(length, "0")

    def lpad(s, length=length):
        return str(s).rjust(length, " ")

    def plex_season_specials(s, length=length):
        if s:
            return "Season " + zpad(s, length)
        else:
            return "Specials"

    def plex_episode(episode_num, episode_num_final, length=length):
        if episode_num_final:
            return "E{}-E{}".format(
                zpad(episode_num, length), zpad(episode_num_final, length)
            )
        else:
            return "E{}".format(zpad(episode_num))

    d = {
        "lpad": lpad,
        "zpad": zpad,
        "plex_episode": plex_episode,
        "plex_season_specials": plex_season_specials,
    }
    d.update(_RENAMER_NAMESPACE)
    return d


def rename_plex(
    file: str, plex_params: PlexTemplateParams = None, output_dir=None
) -> str:
    return rename_process("{plex}", [file], output_dir=output_dir, params=plex_params)[
        0
    ][1]


def rename_process(
    template: str,
    files,
    index_start=1,
    output_dir=None,
    regex=None,
    ignore_missing_regex=False,
    params={},
):
    if regex:
        regex = re.compile(regex)

    if "{plex}" in template:
        template = template.replace("{plex}", PLEX_TEMPLATE)

    if isinstance(params, PlexTemplateParams):
        params = params._asdict()

    length = len(files)
    if "length" not in params:
        params["length"] = length

    t = Template(
        content=template, delimiters=("${", "}"), namespace=create_namespace(length)
    )
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
            "index": index,
            "i": index,
            "wo_ext": wo_ext,
            "ext": ext,
            "filename": base,
            "re": RegexResults(ignore_missing=ignore_missing_regex),
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
                    new_params["re"] = new_params["regex"] = RegexResults(
                        items, ignore_missing=ignore_missing_regex
                    )
        result = t.substitute(new_params)
        result = os.path.join(dir, result)
        results.append((file, result))
        index += 1

    return results
