import tmdbsimple as tmdb
import os
from media_management_scripts.utils import create_metadata_extractor
import shelve


class NameInformation:
    def __init__(self, title, year, metadata):
        self.title = title.replace(":", "")
        self.year = year
        self.metadata = metadata

    def __repr__(self):
        return "<NameInformation: title={}, year={}, meta={}>".format(
            self.title, self.year, self.metadata
        )

    @property
    def simple_name(self):
        return "{} ({})".format(self.title, self.year)

    @property
    def name(self):
        if self.metadata.resolution:
            res = self.metadata.resolution.height
            return "{} ({}) - {}p".format(self.title, self.year, res)
        else:
            return "{} ({})".format(self.title, self.year)

    def new_name(self, file):
        filename, file_extension = os.path.splitext(file)
        new_name = self.name + file_extension
        new_path = os.path.join(os.path.dirname(file), new_name)
        return new_path


class MovieDbApi:
    def __init__(self, api_key=None, config_file=None, shelve_file="./tvdb.shelve"):
        if api_key is not None:
            tmdb.API_KEY = api_key
        else:
            import configparser

            if config_file is None:
                config_file = os.path.expanduser("~/.config/moviedb/moviedb.ini")
                if not os.path.exists(config_file):
                    raise Exception("Must provide either api_key or config_file")
            config = configparser.ConfigParser()
            config.read(config_file)
            tmdb.API_KEY = config.get("moviedb", "apikey")

        self.extractor = create_metadata_extractor()
        self._db = shelve.open(shelve_file)

    def search_file(self, file, single_result=True):
        if not os.path.exists(file) or not os.path.isfile(file):
            raise FileNotFoundError(file)

        metadata = self.extractor.extract(file)
        title = metadata.title
        results = self.search_title(title)
        if single_result and len(results) > 0:
            return results[0]
        elif single_result:
            return None
        return results

    def search_title(self, title, metadata=None):
        results = []
        if title:
            search_results = self._search(title)
            for r in search_results:
                moviedb_title = r["title"]
                year = r["release_date"].split("-")[0]
                results.append(NameInformation(moviedb_title, year, metadata))
        return results

    def _search(self, query):
        search = tmdb.Search()
        response = search.movie(query=query)
        return search.results

    def get_series_id(self, name: str) -> int:
        series_id = self._db.get(name, None)
        if series_id is None:
            for series_id, series_name in self.search_series(name):
                if series_name == name:
                    self._db[name] = series_id
                    return series_id
            series_id = None
        return series_id

    def search_series(self, name):
        series_id = self._db.get(name, None)
        if series_id is None:
            results = tmdb.Search().tv(query=name)
            for s in results["results"]:
                yield int(s["id"]), s["name"]
        else:
            yield series_id, name

    def get_episodes(self, series_id):
        seasons_info = tmdb.TV(series_id).info()["seasons"]
        season_numbers = [int(x["season_number"]) for x in seasons_info]
        episodes = []
        for season_number in season_numbers:
            result = tmdb.TV_Seasons(series_id, season_number).info()
            episodes.extend(result["episodes"])
        return [MovieDbEpisode(x) for x in episodes]

    def get_episodes_by_series_name(self, series_name):
        series_id = self.get_series_id(series_name)
        if series_name is None:
            raise Exception("No series named '{}' found".format(series_name))
        return self.get_episodes(series_id)


class MovieDbEpisode:
    def __init__(self, info_json):
        self.air_date = info_json["air_date"]
        self.season = info_json["season_number"]
        self.number = info_json["episode_number"]
        self.title = info_json["name"]

    def __repr__(self):
        return f'MovieDbEpisode<season={self.season}, number={self.number}, air_date={self.air_date}, title="{self.title}">'
