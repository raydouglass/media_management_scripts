from . import SubCommand
from .common import *
from typing import Iterable
from media_management_scripts.support.episode_finder import (
    find_episodes,
    calculate_new_filenames,
)


class FindEpisodesCommand(SubCommand):
    @property
    def name(self):
        return "find-episodes"

    def build_argparse(self, subparser):
        find_episode_parser = subparser.add_parser(
            self.name,
            help="Find Season/Episode/Part using file names",
            parents=[parent_parser, input_parser],
        )

        find_episode_parser.add_argument("--output", "-o", default="./", dest="output")
        find_episode_parser.add_argument(
            "--seasons",
            action="store_const",
            const=True,
            default=False,
            help="If renaming, moves files into season directories",
        )
        find_episode_parser.add_argument(
            "--use-101-pattern",
            "--101",
            action="store_const",
            const=True,
            default=False,
            help="Use a \d\d\d pattern",
        )
        find_episode_parser.add_argument(
            "--show", default=None, type=str, dest="show", help="Show name"
        )

        group = find_episode_parser.add_mutually_exclusive_group()
        group.add_argument(
            "--rename",
            action="store_const",
            const=True,
            default=False,
            help="Renames the files using the season & episode if found",
        )
        group.add_argument(
            "--copy",
            action="store_const",
            const=True,
            default=False,
            help="Copies the file with new name to output directory",
        )

    def subexecute(self, ns):
        dry_run = ns["dry_run"]
        input_dir = ns["input"]
        out_dir = ns["output"]
        season_folders = ns["seasons"]
        show_name = ns["show"]
        use_101_pattern = ns["use_101_pattern"]

        episodes = find_episodes(input_dir, use_101_pattern)

        table = sorted(
            list(calculate_new_filenames(episodes, out_dir, season_folders, show_name))
        )

        columns = ("Original", "Episode", "New Path")
        if not dry_run and ns.get("rename", False):
            self._bulk_move(
                table,
                column_descriptions=columns,
                src_index=0,
                dest_index=2,
                print_table=True,
            )
        elif not dry_run and ns.get("copy", False):
            self._bulk_copy(
                table,
                column_descriptions=columns,
                src_index=0,
                dest_index=2,
                print_table=True,
            )
        else:
            self._bulk_print(
                table, column_descriptions=columns, src_index=0, dest_index=2
            )


SubCommand.register(FindEpisodesCommand)
