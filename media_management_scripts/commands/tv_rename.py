from . import SubCommand
from .common import *

from media_management_scripts.tvdb_api import TVDB, get_season_episode

from os.path import isfile, join, basename, dirname


def pad(i):
    if i < 10:
        return "0" + str(i)
    else:
        return str(i)


class TvRenameCommand(SubCommand):
    @property
    def name(self):
        return "tv-rename"

    def build_argparse(self, subparser):
        tv_rename_parser = subparser.add_parser(
            "tv-rename",
            help="Renames files in a directory to sXXeYY. Can also use TVDB to name files (<show> - SxxeYY - <episode_name>)",
            parents=[parent_parser],
        )
        tv_rename_parser.add_argument(
            "-s", "--season", default=1, help="The season to use", type=int
        )
        tv_rename_parser.add_argument(
            "-e", "--episode", default=1, help="The episode to start with", type=int
        )
        tv_rename_parser.add_argument(
            "--tvdb",
            default=False,
            action="store_const",
            const=True,
            help="Use TVDB to rename episodes",
        )
        tv_rename_parser.add_argument(
            "--show", default=None, help="The name of the show", type=str
        )
        tv_rename_parser.add_argument(
            "--output",
            default=None,
            help="The output directory to move & rename to",
            type=str,
        )
        tv_rename_parser.add_argument(
            "input",
            nargs="*",
            help="The directories to search for files. These will be processed in order.",
        )

    def subexecute(self, ns):
        input_to_cmd = ns["input"]
        season = ns.get("season", 1)
        episode = ns.get("episode", 1)
        show = ns.get("show", None)
        output = ns.get("output", None)
        use_tvb = ns["tvdb"]
        if use_tvb and show is None:
            import sys

            print("You must specify a show name if using TVDB")
            sys.exit(1)

        if use_tvb:
            from media_management_scripts.tvdb_api import from_config

            tvdb = from_config()
        else:
            tvdb = None

        results = self.run(input_to_cmd, season, episode, show, output, tvdb)
        if results:
            self._bulk_move(results, column_descriptions=["Source", "Destination"])

    def _remove_special_characters(self, s):
        # https://stackoverflow.com/a/31976060
        return s.translate({ord(c): None for c in "/<>:'\"\\|?*"})

    def run(self, input_dirs, season=1, episode=1, show=None, output=None, tvdb=None):
        from os import listdir, path

        files = []
        for input_dir in input_dirs:
            new_files = sorted(
                [
                    join(input_dir, f)
                    for f in listdir(input_dir)
                    if isfile(join(input_dir, f)) and not f.startswith(".")
                ]
            )
            files.extend(new_files)
        if tvdb:
            shows = [(str(i), name) for i, name in tvdb.search_series(show)]
            if len(shows) == 0:
                print("Not search results for show '{}' found.".format(show))
                return
            if len(shows) > 1:
                from dialog import Dialog

                d = Dialog(autowidgetsize=True)
                code, tag = d.menu("Choices:", choices=shows, title="Pick a show")
                if code != d.OK:
                    return
                show = next(x[1] for x in shows if x[0] == tag)
                series_id = int(tag)
            else:
                series_id = int(shows[0][0])
            episodes = tvdb.get_episodes(series_id)
            episode_map = {get_season_episode(ep): ep for ep in episodes}
        else:
            episode_map = {}
        results = []
        for file in files:
            ext = path.splitext(file)[1]
            ep = episode_map.get((season, episode), None)
            ep_name = ep.get("episodeName", None) if ep else None
            if show is not None and ep is not None and ep_name is not None:
                new_name = "{} - S{}E{} - {}{}".format(
                    show, pad(season), pad(episode), ep_name, ext
                )
            elif show is not None:
                new_name = "{} - S{}E{}{}".format(show, pad(season), pad(episode), ext)
            else:
                new_name = "S{}E{}{}".format(pad(season), pad(episode), ext)

            new_name = self._remove_special_characters(new_name)

            if output:
                new_name = join(output, "Season {}".format(pad(season)), new_name)
            else:
                dir = dirname(file)
                new_name = join(dir, new_name)
            results.append((file, new_name))
            episode += 1
        return results


SubCommand.register(TvRenameCommand)
