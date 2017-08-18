from media_management_scripts.tvdb_api import TVDB
from media_management_scripts.utils import create_metadata_extractor
from media_management_scripts.support.metadata import Metadata
from media_management_scripts.support.episode_finder import extract
from media_management_scripts.renamer import rename_process
from typing import Dict
from difflib import SequenceMatcher
from texttable import Texttable
import os
import shutil


def _map_metadata(input_files, meta_shelve=None) -> Dict[str, Metadata]:
    extractor = create_metadata_extractor()
    ret = {}
    for file in input_files:
        if meta_shelve and file in meta_shelve:
            ret[file] = meta_shelve[file]
        elif meta_shelve:
            ret[file] = meta_shelve[file] = extractor.extract(file)
        else:
            ret[file] = extractor.extract(file)
    return ret


def _get_season_episode(tvdb_episode, use_dvd=False):
    if use_dvd:
        season = tvdb_episode['dvdSeason']
        episode_num = tvdb_episode['dvdEpisodeNumber']
    else:
        season = tvdb_episode['airedSeason']
        episode_num = tvdb_episode['airedEpisodeNumber']
    return int(season), int(episode_num)


def _find_match(metadata: Metadata, episodes, use_dvd=False, fuzzy=False):
    date = metadata.tags['date'].split('T')[0]
    title = metadata.tags['title']
    fuzzy_match = 0
    fuzzy_episode = None
    for ep in episodes:
        ep_name = ep.get('episodeName', None)
        ep_date = ep.get('firstAired', None)
        if ep_date == date:
            if title == ep_name:
                return ep
            elif fuzzy:
                ratio = SequenceMatcher(None, title, ep_name).ratio()
                if ratio >= .85 and ratio > fuzzy_match:
                    fuzzy_episode = ep
                    fuzzy_match = ratio
    if not fuzzy_episode:
        if 'season_number' in metadata.tags and 'episode_sort' in metadata.tags:
            season = metadata.tags['season_number']
            ep_num = metadata.tags['episode_sort']
            for ep in episodes:
                tvdb_season, tvdb_ep_num = _get_season_episode(ep, use_dvd)
                if tvdb_season == season and tvdb_ep_num == ep_num:
                    return ep
    if not fuzzy_episode:
        season, ep_num, part = extract(title)
        if part is None:
            for ep in episodes:
                tvdb_season, tvdb_ep_num = _get_season_episode(ep, use_dvd)
                if tvdb_season == season and tvdb_ep_num == ep_num:
                    return ep
    return fuzzy_episode


def _do_rename(input, output):
    print('{} => {}'.format(input, output))
    d = os.path.dirname(output)
    os.makedirs(d, exist_ok=True)
    shutil.move(input, output)


def _output(matched, not_matched, output_dir, dry_run):
    table = []
    for file, params in matched.items():
        new_name = rename_process(
            '${show}/Season ${season|zpad}/${show} - S${season|zpad}E${ep_num|zpad} - ${name}.${ext}', files=[file],
            output_dir=output_dir,
            params=params)[0][1]
        if not dry_run:
            _do_rename(file, new_name)
        table.append((file, new_name))
    table.sort(key=lambda s: s[1])
    t = Texttable(max_width=0)
    t.set_deco(Texttable.VLINES | Texttable.HEADER)
    t.header(('Input', 'Output'))
    t.add_rows(rows=table, header=False)
    print(t.draw())
    if not_matched:
        print('Not Matched:')
        for file in not_matched:
            print('  {}'.format(file))


def process_itunes_tv(input_files, output_dir, tvdb: TVDB, meta_shelve=None, use_dvd=False, fuzzy=False, dry_run=True):
    metadata_map = _map_metadata(input_files, meta_shelve)
    series_name = {value.tags['show'] for value in metadata_map.values()}
    if len(series_name) != 1:
        raise Exception('Input files have different shows: {}'.format(series_name))
    series_name = series_name.pop()
    series_id = tvdb.search_series(series_name)
    tvdb_episodes = tvdb.get_episodes(series_id)
    matched = {}
    not_matched = []
    for file, metadata in metadata_map.items():
        episode = _find_match(metadata, tvdb_episodes, use_dvd, fuzzy)
        if episode:
            season, episode_num = _get_season_episode(episode, use_dvd)
            params = {
                'show': series_name,
                'season': season,
                'ep_num': episode_num,
                'name': episode['episodeName']
            }
            matched[file] = params
        else:
            not_matched.append(file)
    _output(matched, not_matched, output_dir, dry_run)
