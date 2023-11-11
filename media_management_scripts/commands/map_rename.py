from pathlib import Path
from . import SubCommand
from .common import *
import argparse
import os
from media_management_scripts.support.episode_finder import (
    find_episodes,
    extract,
    EpisodePart,
)
import tempfile


class MapRenameCommand(SubCommand):
    @property
    def name(self):
        return "map-rename"

    def build_argparse(self, subparser):
        desc = """Bulk rename episodes based on a mapping file. Renaming "cycles" (e.g. swapping two episodes) are supported.

The mapping file is formatted with a source and destination Season/Episode on each line. Blank lines and lines starting with # are ignored.

Example:

# Source Destination
S02E06 S02E04
S02E04 S02E06
S11E01 S10E24

"""

        map_rename_parser = subparser.add_parser(
            "map-rename",
            help="Bulk rename episodes based on a mapping file",
            parents=[parent_parser],
            formatter_class=argparse.RawTextHelpFormatter,
            description=desc,
        )
        map_rename_parser.add_argument(
            "mapping_file", help="The mapping file to use", type=argparse.FileType()
        )
        map_rename_parser.add_argument("tv_show_dir", help="TV Show directory")

        map_rename_parser.add_argument(
            "-y",
            "--overwrite",
            help="Overwrite output target if it exists",
            action="store_const",
            default=False,
            const=True,
        )

    def subexecute(self, ns):
        tv_show_dir = ns["tv_show_dir"]
        mapping_file = ns["mapping_file"]
        dry_run = ns["dry_run"]
        overwrite = ns["overwrite"]

        if not any(filter(lambda x: "season" in x.lower(), os.listdir(tv_show_dir))):
            print(f"'{tv_show_dir}' does not appear to be a TV Show directory")
            return

        mapping = {}
        for line in mapping_file:
            line = line.strip()
            if line and not line.startswith("#"):
                src, dest = line.split()
                src_season, src_episode, _ = extract(src)
                dest_season, dest_episode, _ = extract(dest)
                mapping[(src_season, src_episode)] = (dest_season, dest_episode)

        episodes = list(find_episodes(tv_show_dir))
        episodes_map = {(e.season, e.episode): e for e in episodes}

        table = []
        quit = False
        for src, dest in sorted(mapping.items()):
            if src not in episodes_map:
                season, ep = src
                print(f"Episode 'S{season:02d}E{ep:02d}' not found.")
                quit = True
                continue

            src_episode = episodes_map[src]
            src_path = src_episode.path

            if dest in episodes_map:
                dest_episode = episodes_map[dest]
                dest_path = dest_episode.path
            else:
                ext = os.path.splitext(src_path)[1]
                season, ep = dest
                dest_path = (
                    Path(tv_show_dir)
                    / f"Season {season:02d}"
                    / f"S{season:02d}E{ep:02d}{ext}"
                )

            table.append((src_path, dest_path))

        if quit:
            return 1

        self._bulk_print(table, ["Source", "Destination"])

        quit = False
        for dest in mapping.values():
            if dest not in mapping and dest in episodes_map and not overwrite:
                d = episodes_map[dest].path
                print(
                    f"Destination '{d}' exists, but is not also being renamed. If this is intended, use --overwrite to continue."
                )
                quit = True
        if quit:
            return 2

        if not dry_run:
            files = [
                (src, dest, tempfile.mkstemp(dir=tv_show_dir)[1]) for src, dest in table
            ]
            files.sort()
            for src, _, intermediate in files:
                self._move(src, intermediate, overwrite=True, print_output=True)
            for _, dest, intermediate in files:
                self._move(intermediate, dest, overwrite=True, print_output=True)


SubCommand.register(MapRenameCommand)
