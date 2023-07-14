from . import SubCommand
from .common import *
import argparse
from media_management_scripts.support.executables import (
    java,
    filebot_jar,
    execute_with_output,
)

import re


def parse_filebot_text(text):
    pattern = re.compile(r"\s\[(.+)\] to \[(.+)\]")
    # Rename episodes using [TheTVDB]
    # Auto-detected query: [QI XL, qi xl series o]
    # Fetching episode data for [QI]
    # Resource not found: https://api.thetvdb.com/search/series?name=qi+xl+series+o
    # [TEST] from [/Volumes/Media.temp/QI_XL_Series_O_Episode_1_Ologies_720p.mp4.mp4] to [/QI/15/1/Ologies.mp4]
    # Processed 1 files
    lines = [line for line in text.split("\n") if line.startswith("[TEST]")]
    results = {}
    for line in lines:
        m = pattern.search(line)
        if m:
            source = m.group(1)
            destination = m.group(2)
            destination = destination.split("/")[1:-1]
            results[source] = tuple(destination)
    return results


def invoke_filebot(file_path: str, type: str):
    # java -jar FileBot.jar -rename /Volumes/Media/temp/QI_XL_Series_O_Episode_1_Ologies_720p.mp4.mp4 --db TheTVDB -non-strict --action test --format '{n}/{s}/{e}/{t}' --output '/'
    args = [
        java(),
        "-jar",
        filebot_jar(),
        "-rename",
        file_path,
        "--db",
        "TheTVDB" if type == "tv" else "TheMovieDB",
        "-non-strict",
        "--action",
        "test",
        "--format",
        "{n}/{s}/{e}/{t}/{ext}",
        "--output",
        "/",
    ]

    ret_code, filebot_output = execute_with_output(
        args, print_output=False, use_nice=False
    )
    if ret_code != 0:
        raise Exception(
            "Non-zero filebot return code ({}): {}".format(ret_code, filebot_output)
        )

    results = parse_filebot_text(filebot_output)
    result = results.get(file_path, None)
    if result:
        return result
    else:
        return None, None, None, None
        # series_name, season_number, episode_number, episode_name = None, None, None, None


class FilebotCommand(SubCommand):
    @property
    def name(self):
        return "filebot"

    def build_argparse(self, subparser):
        filebot_parser = subparser.add_parser(
            self.name, help="", parents=[parent_parser]
        )
        filebot_parser.add_argument("input", nargs="+", help="Input directory")
        filebot_parser.add_argument("--output", help="Output directory")
        filebot_parser.add_argument("--src", choices=("tv", "movie"), default="tv")
        filebot_parser.add_argument("--template", default="{plex}")

    def subexecute(self, ns):
        pass


SubCommand.register(FilebotCommand)
