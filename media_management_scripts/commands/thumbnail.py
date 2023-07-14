from media_management_scripts.convert import convert_subtitles_to_srt
from . import SubCommand
from .common import *
import os
import math
from ..utils import extract_metadata
from ..support.formatting import duration_from_str
from ..support.executables import ffmpeg, execute_with_output


class ThumbnailCommand(SubCommand):
    @property
    def name(self):
        return "thumbnail"

    def build_argparse(self, subparser):
        parser = subparser.add_parser(
            "thumbnail",
            help="Extract a number of thumbnails from a video",
            parents=[parent_parser, input_parser, output_parser, start_end_parser],
        )
        parser.add_argument(
            "--count",
            "-c",
            default=10,
            type=int,
            help="Number of thumbnails to generate. Default is 10",
        )

    def _output_format(self, output, number):
        basename, ext = os.path.splitext(os.path.basename(output))
        dir = os.path.dirname(output)
        count = math.floor(math.log10(number)) + 1
        output_file = basename + "%0" + str(count) + "d" + ext
        return os.path.join(dir, output_file)

    def subexecute(self, ns):
        input_to_cmd = ns["input"]
        output = ns.get("output", None)
        number = ns.get("count", 10)
        start = ns.get("start", None)
        end = ns.get("end", None)

        output = self._output_format(output, number)
        duration = extract_metadata(input_to_cmd).estimated_duration

        if end:
            duration = end
        if start:
            duration -= start

        every_frame = str(number / duration)

        args = [ffmpeg(), "-y"]
        if start:
            args.extend(["-ss", str(start)])
        if end:
            args.extend(["-to", str(end)])
        args.extend(["-i", input_to_cmd, "-vf", "fps=" + every_frame, output])
        print(args)
        execute_with_output(args, print_output=True)


SubCommand.register(ThumbnailCommand)
