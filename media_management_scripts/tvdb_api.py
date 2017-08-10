import requests
import json
import shelve
import os

BASE_URL = 'https://api.thetvdb.com'
DEFAULT_CONFIG_LOCATION = '~/.config/tvdb/tvdb.ini'


class TVDB():
    def __init__(self, api_key, username, user_key, shelve_file='./tvdb.shelve'):
        self._api_key = api_key
        self._username = username
        self._user_key = user_key
        self._jwt = None
        self._db = shelve.open(shelve_file)

    def _get_jwt(self):
        payload = {'apikey': self._api_key, 'username': self._username, 'userkey': self._user_key}
        res = requests.post(BASE_URL + '/login', json=payload)
        res.raise_for_status()
        return res.json()['token']

    def refresh(self):
        if self._jwt is None:
            self._jwt = self._get_jwt()
        else:
            headers = {'Authorization': 'Bearer ' + self._jwt}
            res = requests.get(BASE_URL + '/refresh_token', headers=headers)
            if res.status_code == requests.codes.ok:
                self._jwt = res.json()['token']
            else:
                self._jwt = self._get_jwt()

    def _search_series(self, name):
        if self._jwt is None:
            self.refresh()
        headers = {'Authorization': 'Bearer ' + self._jwt}
        params = {'name': name}
        res = requests.get(BASE_URL + '/search/series', params=params, headers=headers)
        res.raise_for_status()
        # if res.status_code == requests.codes.ok:
        return res.json()

    def search_series(self, name):
        series_id = self._db.get(name, None)
        if series_id is None:
            result = self._search_series(name)
            for s in result['data']:
                if s['seriesName'] == name:
                    series_id = int(s['id'])
                    self._db[name] = series_id
                    return series_id
        return series_id

    def get_episodes(self, series_id):
        if self._jwt is None:
            self.refresh()
        headers = {'Authorization': 'Bearer ' + self._jwt}
        page = 1
        episodes = []
        while page is not None:
            res = requests.get(BASE_URL + '/series/{}/episodes'.format(series_id), headers=headers,
                               params={'page': page})
            res = res.json()
            episodes.extend(res['data'])
            page = res['links']['next']
        return episodes

    @staticmethod
    def season_number(e):
        return e['airedSeason'], e['airedEpisodeNumber']

    @staticmethod
    def season_number_dvd(e):
        return e['dvdSeason'], e['dvdEpisodeNumber']

    def find_episode(self, series_name, episode=None, air_date=None):
        if episode is None and air_date is None:
            raise Exception('Both episode and air_date cannot be null')
        series_id = self.search_series(series_name)
        if series_id:
            if episode:
                episodes = self.get_episodes(series_id)
                for e in episodes:
                    if e['episodeName'] == episode:
                        return [e]
            if air_date:
                if self._jwt is None:
                    self.refresh()
                headers = {'Authorization': 'Bearer ' + self._jwt}
                params = {'firstAired': air_date}
                res = requests.get(BASE_URL + '/series/{}/episodes/query'.format(series_id),
                                   headers=headers,
                                   params=params)
                res = res.json()
                print(res)
                if 'data' in res:
                    return res['data']

        return []

    def query(self, series_name, firstAired):
        if self._jwt is None:
            self.refresh()
        headers = {'Authorization': 'Bearer ' + self._jwt}
        series_id = self.search_series(series_name)
        params = {'firstAired': firstAired}
        res = requests.get(BASE_URL + '/series/{}/episodes/query'.format(series_id), headers=headers, params=params)
        return res.json()

    def _write_data(self):
        with open('series.json', 'w') as file:
            json.dump(self.series, file)

    def _read_data(self):
        try:
            with open('series.json', 'r') as f:
                self.series = json.load(f)
        except (OSError, IOError) as e:
            pass


def from_config(config: str = DEFAULT_CONFIG_LOCATION) -> TVDB:
    if config is None:
        config = DEFAULT_CONFIG_LOCATION
    import configparser
    parser = configparser.ConfigParser()
    parser.read(config)
    username = parser.get('tvdb', 'username')
    user_key = parser.get('tvdb', 'userkey')
    api_key = parser.get('tvdb', 'apikey')
    shelve_file = os.path.expanduser(parser.get('tvdb', 'shelve.file', fallback='~/.config/tvdb/tvdb.shelve'))

    return TVDB(api_key, username, user_key, shelve_file)


def _run_command(cmd, ns):
    config = os.path.expanduser(ns['config'])
    tvdb = from_config(config)

    if cmd == 'episodes':
        series_name = ns['series']
        series_id = tvdb.search_series(series_name)
        episodes = tvdb.get_episodes(series_id)
        episodes = sorted(episodes, key=TVDB.season_number)
        print(json.dumps(episodes))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--config', type=str, default='~/.config/tvdb/tvdb.ini')

    subparsers = parser.add_subparsers(help='Sub commands', dest='command')

    episodes_parser = subparsers.add_parser('episodes', parents=[parent_parser])
    episodes_parser.add_argument('series', type=str)

    ns = vars(parser.parse_args())
    cmd = ns.get('command', None)
    if not cmd:
        parser.print_usage()
    else:
        _run_command(cmd, ns)
