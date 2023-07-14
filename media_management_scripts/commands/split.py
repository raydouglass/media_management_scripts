from . import SubCommand
from .common import *


class SplitCommand(SubCommand):
    @property
    def name(self):
        return "split"

    def build_argparse(self, subparser):
        split_parser = subparser.add_parser(
            "split", help="Split a file", parents=[parent_parser, start_end_parser]
        )
        split_parser.add_argument(
            "-c",
            "--by-chapters",
            help="Split file by chapters, specifying number of chapters per file",
            type=int,
        )

        split_parser.add_argument("input", nargs="+", help="Input directory")
        split_parser.add_argument("--output", "-o", default="./", dest="output")

    def subexecute(self, ns):
        from media_management_scripts.support.files import get_files_in_directories
        from media_management_scripts.support.split import split_by_chapter
        from media_management_scripts.convert import cut
        import os

        input_to_cmd = ns["input"]

        output = ns["output"]
        if ns.get("by_chapters", None) is not None:
            chapters = ns["by_chapters"]
            count = 0
            for file in get_files_in_directories(input_to_cmd):
                count += split_by_chapter(file, output, chapters, initial_count=count)
                # print(file)
        else:
            if os.path.isdir(output):
                raise Exception("Output cannot be a directory")
            start = ns["start"]
            end = ns.get("end")
            cut(input_to_cmd[0], output, start, end)


SubCommand.register(SplitCommand)
