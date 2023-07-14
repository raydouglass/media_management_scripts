from . import SubCommand
from .common import *


class ConcatMp4Command(SubCommand):
    @property
    def name(self):
        return "concat-mp4"

    def build_argparse(self, subparser):
        concat_mp4_parser = subparser.add_parser(
            "concat-mp4",
            help="Concat multiple mp4 files together",
            parents=[parent_parser],
        )  # No input dir
        concat_mp4_parser.add_argument("output", help="The output file")
        concat_mp4_parser.add_argument(
            "input",
            nargs="*",
            help="The input files to concat. These must be mp4 with h264 codec.",
        )
        concat_mp4_parser.add_argument(
            "--overwrite",
            "-y",
            help="Overwrite the output",
            action="store_const",
            const=True,
            default=False,
        )
        concat_mp4_parser.add_argument(
            "--quiet",
            "-q",
            help="Suppress output",
            action="store_const",
            const=False,
            default=True,
        )

    def subexecute(self, ns):
        from media_management_scripts.support.concat_mp4 import concat_mp4

        input_to_cmd = ns["input"]
        output_file = ns["output"]
        overwrite = ns["overwrite"]
        quiet = ns["quiet"]
        concat_mp4(output_file, input_to_cmd, overwrite, print_output=(not quiet))


SubCommand.register(ConcatMp4Command)
