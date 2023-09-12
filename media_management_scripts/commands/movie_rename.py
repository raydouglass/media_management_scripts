from . import SubCommand
from .common import *


class MovieRenameCommand(SubCommand):
    @property
    def name(self):
        return "movie-rename"

    def build_argparse(self, subparser):
        movie_rename_parser = subparser.add_parser(
            "movie-rename",
            help="Renames a file based on TheMovieDB",
            parents=[parent_parser],
        )
        movie_rename_parser.add_argument(
            "--confirm",
            help="Ask for confirmation before renaming, exiting with non-zero if no",
            action="store_const",
            const=True,
            default=False,
        )
        movie_rename_parser.add_argument("input", nargs="+", help="Input Files")

    def subexecute(self, ns):
        from media_management_scripts.support.movie_rename import movie_rename

        input_to_cmd = ns["input"]
        movie_rename(input_to_cmd, ns)


SubCommand.register(MovieRenameCommand)
